"""
Business logic services for multi-plan cart system.
Contains PricingEngine, CartService, and CheckoutService.
"""
from decimal import Decimal
from datetime import timedelta
from typing import List, Tuple, Optional
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import ValidationError

from .models import Plan, Cart, CartItem, BundleOrder, Subscription


class PricingEngine:
    """Handles all price calculations for cart and checkout"""
    
    @staticmethod
    def calculate_daily_rate(plan: Plan) -> Decimal:
        """Calculate daily rate for a plan"""
        return plan.get_daily_rate()
    
    @staticmethod
    def calculate_item_price(plan: Plan, duration_days: int) -> int:
        """Calculate price for a plan with custom duration"""
        return plan.calculate_price_for_duration(duration_days)
    
    @staticmethod
    def calculate_cart_total(cart: Cart) -> int:
        """Calculate total price for entire cart"""
        return cart.get_total()


class CartService:
    """Business logic for cart operations"""
    
    @staticmethod
    def get_or_create_cart(user) -> Cart:
        """Get user's cart or create new one"""
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart
    
    @staticmethod
    def add_item(user, plan_id: int, duration_days: int = None) -> CartItem:
        """Add plan to cart with custom duration"""
        cart = CartService.get_or_create_cart(user)
        
        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            raise ValidationError({'plan_id': 'Plan not found or inactive'})
        
        # Use plan's default duration if not specified
        if duration_days is None:
            duration_days = plan.duration_days
        
        # Validate duration
        if not plan.validate_duration(duration_days):
            raise ValidationError({
                'duration_days': f"Duration must be between {plan.min_duration_days} and {plan.max_duration_days} days"
            })
        
        # Check for duplicate
        existing = cart.items.filter(plan=plan).first()
        if existing:
            raise ValidationError({'plan_id': 'This plan is already in your cart'})
        
        # Check for active subscription
        if Subscription.objects.filter(
            user=user, plan=plan, status__in=['ACTIVE', 'PENDING_PAYMENT']
        ).exists():
            raise ValidationError({
                'plan_id': 'You already have an active subscription for this plan'
            })
        
        return CartItem.objects.create(
            cart=cart,
            plan=plan,
            custom_duration_days=duration_days
        )
    
    @staticmethod
    def update_item_duration(user, item_id: int, duration_days: int) -> CartItem:
        """Update duration for a cart item"""
        try:
            item = CartItem.objects.select_related('plan', 'cart').get(
                id=item_id, cart__user=user
            )
        except CartItem.DoesNotExist:
            raise ValidationError({'item_id': 'Cart item not found'})
        
        if not item.plan.validate_duration(duration_days):
            raise ValidationError({
                'duration_days': f"Duration must be between {item.plan.min_duration_days} and {item.plan.max_duration_days} days"
            })
        
        item.custom_duration_days = duration_days
        item.save()
        return item
    
    @staticmethod
    def remove_item(user, item_id: int) -> bool:
        """Remove item from cart"""
        deleted, _ = CartItem.objects.filter(id=item_id, cart__user=user).delete()
        return deleted > 0
    
    @staticmethod
    def clear_cart(user) -> None:
        """Clear all items from cart"""
        cart = CartService.get_or_create_cart(user)
        cart.clear()


class CheckoutService:
    """Handles checkout and subscription creation"""
    
    @staticmethod
    def validate_cart(cart: Cart) -> List[str]:
        """Validate cart before checkout"""
        errors = []
        
        if cart.items.count() == 0:
            errors.append("Cart is empty")
            return errors
        
        for item in cart.items.select_related('plan').all():
            # Check plan is still active
            if not item.plan.is_active:
                errors.append(f"Plan '{item.plan.name}' is no longer available")
            
            # Check duration is still valid
            if not item.plan.validate_duration(item.custom_duration_days):
                errors.append(
                    f"Duration {item.custom_duration_days} days is no longer valid for '{item.plan.name}'"
                )
            
            # Check for existing active subscription
            if Subscription.objects.filter(
                user=cart.user, plan=item.plan, status__in=['ACTIVE', 'PENDING_PAYMENT']
            ).exists():
                errors.append(f"You already have an active subscription for '{item.plan.name}'")
        
        return errors
    
    @staticmethod
    def create_razorpay_order(cart: Cart) -> Tuple[BundleOrder, dict]:
        """Create Razorpay order for cart total"""
        import razorpay
        
        # Validate cart first
        errors = CheckoutService.validate_cart(cart)
        if errors:
            raise ValidationError({'cart': errors})
        
        total = PricingEngine.calculate_cart_total(cart)
        
        if total <= 0:
            raise ValidationError({'cart': 'Cart total must be greater than 0'})
        
        # Create bundle order
        bundle_order = BundleOrder.objects.create(
            user=cart.user,
            total_amount=total,
            status='PENDING'
        )
        
        # Create Razorpay order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            'amount': total * 100,  # Razorpay expects paise
            'currency': 'INR',
            'receipt': f'bundle_{bundle_order.id}',
        })
        
        bundle_order.razorpay_order_id = razorpay_order['id']
        bundle_order.save()
        
        return bundle_order, razorpay_order
    
    @staticmethod
    @transaction.atomic
    def complete_checkout(
        bundle_order: BundleOrder, 
        payment_id: str, 
        signature: str
    ) -> List[Subscription]:
        """Complete checkout after successful payment"""
        import razorpay
        import hmac
        import hashlib
        
        # Verify payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': bundle_order.razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
        except razorpay.errors.SignatureVerificationError:
            raise ValidationError({'signature': 'Payment verification failed'})
        
        # Check if already processed
        if bundle_order.status == 'PAID':
            raise ValidationError({'order': 'Order already processed'})
        
        cart = Cart.objects.prefetch_related('items__plan').get(user=bundle_order.user)
        subscriptions = []
        today = timezone.now().date()
        
        for item in cart.items.all():
            end_date = today + timedelta(days=item.custom_duration_days)
            
            subscription = Subscription.objects.create(
                user=bundle_order.user,
                plan=item.plan,
                bundle_order=bundle_order,
                base_price=item.plan.base_price,
                total_paid=item.calculated_price,
                start_date=today,
                base_end_date=end_date,
                adjusted_end_date=end_date,
                status='ACTIVE',
                payment_gateway='razorpay',
                payment_transaction_id=payment_id,
            )
            subscriptions.append(subscription)
        
        # Update bundle order
        bundle_order.status = 'PAID'
        bundle_order.razorpay_payment_id = payment_id
        bundle_order.paid_at = timezone.now()
        bundle_order.save()
        
        # Clear cart
        cart.clear()
        
        return subscriptions
