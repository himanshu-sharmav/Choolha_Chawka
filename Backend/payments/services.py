import razorpay
import hmac
import hashlib
from django.conf import settings
from django.utils import timezone
from .models import RazorpayOrder, Payment, RefundRequest

class RazorpayService:
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    
    def create_order(self, subscription):
        """Create Razorpay order for subscription"""
        amount = subscription.total_paid * 100  # Convert to paise
        receipt = f"sub_{subscription.id}_{int(timezone.now().timestamp())}"
        
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'receipt': receipt,
            'payment_capture': 1  # Auto capture
        }
        
        try:
            razorpay_order = self.client.order.create(data=order_data)
            
            # Create order record in database
            order = RazorpayOrder.objects.create(
                order_id=razorpay_order['id'],
                amount=amount,
                currency='INR',
                subscription=subscription,
                user=subscription.user,
                receipt=receipt,
                status='created'
            )
            
            return order, razorpay_order
        except Exception as e:
            raise Exception(f"Razorpay order creation failed: {str(e)}")
    
    def verify_payment(self, order_id, payment_id, signature):
        """Verify Razorpay payment signature"""
        try:
            # Get order from database
            order = RazorpayOrder.objects.select_related(
                'subscription', 'user'
            ).get(order_id=order_id)
            
            # Verify signature
            generated_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
                f"{order_id}|{payment_id}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if generated_signature != signature:
                raise Exception("Invalid payment signature")
            
            # Update order
            order.payment_id = payment_id
            order.signature = signature
            order.status = 'paid'
            order.save()
            
            # Create payment record
            payment = Payment.objects.create(
                user=order.user,
                subscription=order.subscription,
                payment_gateway='razorpay',
                transaction_id=payment_id,
                amount=order.amount,
                status='SUCCESS',
                gateway_order_id=order_id,
                gateway_payment_id=payment_id,
                gateway_signature=signature
            )
            
            # Update subscription status
            subscription = order.subscription
            subscription.status = 'ACTIVE'
            subscription.payment_gateway = 'razorpay'
            subscription.payment_transaction_id = payment_id
            subscription.save()
            
            return payment, subscription
            
        except RazorpayOrder.DoesNotExist:
            raise Exception("Invalid order ID")
        except Exception as e:
            # Create failed payment record
            try:
                order = RazorpayOrder.objects.get(order_id=order_id)
                Payment.objects.create(
                    user=order.user,
                    subscription=order.subscription,
                    payment_gateway='razorpay',
                    transaction_id=payment_id or f"failed_{timezone.now().timestamp()}",
                    amount=order.amount,
                    status='FAILED',
                    gateway_order_id=order_id,
                    failure_reason=str(e)
                )
            except:
                pass
            raise e

razorpay_service = RazorpayService()
