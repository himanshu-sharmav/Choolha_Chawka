"""
Tests for the modify_days endpoint
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from subscriptions.models import Plan, Subscription


class ModifySubscriptionDaysTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create mess owner
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            phone='+919876543210',
            user_type='mess_owner',
            password='testpass123'
        )
        
        # Create customer
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            phone='+919876543211',
            user_type='customer',
            password='testpass123'
        )
        
        # Create plan
        self.plan = Plan.objects.create(
            code='TEST_PLAN',
            name='Test Plan',
            service_type='mess',
            base_price=3000,
            duration_days=30
        )
        
        # Create active subscription
        today = timezone.now().date()
        self.subscription = Subscription.objects.create(
            user=self.customer,
            plan=self.plan,
            base_price=3000,
            total_paid=3000,
            start_date=today,
            base_end_date=today + timedelta(days=30),
            adjusted_end_date=today + timedelta(days=30),
            status='ACTIVE'
        )
        
        self.client = APIClient()
    
    def test_add_days_success(self):
        """Test successfully adding days to subscription"""
        self.client.force_authenticate(user=self.owner)
        
        original_end_date = self.subscription.adjusted_end_date
        
        response = self.client.post(
            f'/api/subscriptions/{self.subscription.id}/modify_days/',
            {
                'days_to_add': 5,
                'reason': 'Test compensation'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['modification']['days_modified'], 5)
        
        # Verify subscription was updated
        self.subscription.refresh_from_db()
        self.assertEqual(
            self.subscription.adjusted_end_date,
            original_end_date + timedelta(days=5)
        )
    
    def test_remove_days_success(self):
        """Test successfully removing days from subscription"""
        self.client.force_authenticate(user=self.owner)
        
        original_end_date = self.subscription.adjusted_end_date
        
        response = self.client.post(
            f'/api/subscriptions/{self.subscription.id}/modify_days/',
            {
                'days_to_add': -3,
                'reason': 'Test correction'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['modification']['days_modified'], -3)
        
        # Verify subscription was updated
        self.subscription.refresh_from_db()
        self.assertEqual(
            self.subscription.adjusted_end_date,
            original_end_date - timedelta(days=3)
        )
    
    def test_reactivate_expired_subscription(self):
        """Test that adding days to expired subscription reactivates it"""
        self.client.force_authenticate(user=self.owner)
        
        # Set subscription to expired
        self.subscription.status = 'EXPIRED'
        self.subscription.adjusted_end_date = timezone.now().date() - timedelta(days=5)
        self.subscription.save()
        
        response = self.client.post(
            f'/api/subscriptions/{self.subscription.id}/modify_days/',
            {
                'days_to_add': 30,
                'reason': 'Reactivation'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status']['changed'])
        self.assertEqual(response.data['status']['original'], 'EXPIRED')
        self.assertEqual(response.data['status']['current'], 'ACTIVE')
        
        # Verify subscription was reactivated
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'ACTIVE')
    
    def test_zero_days_fails(self):
        """Test that zero days is rejected"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.post(
            f'/api/subscriptions/{self.subscription.id}/modify_days/',
            {'days_to_add': 0},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_past_date_fails(self):
        """Test that setting end date to past is rejected"""
        self.client.force_authenticate(user=self.owner)
        
        # Try to remove more days than available
        response = self.client.post(
            f'/api/subscriptions/{self.subscription.id}/modify_days/',
            {'days_to_add': -100},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('past', response.data['message'].lower())
    
    def test_non_owner_forbidden(self):
        """Test that non-owners cannot modify days"""
        self.client.force_authenticate(user=self.customer)
        
        response = self.client.post(
            f'/api/subscriptions/{self.subscription.id}/modify_days/',
            {'days_to_add': 5},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_forbidden(self):
        """Test that unauthenticated users cannot modify days"""
        response = self.client.post(
            f'/api/subscriptions/{self.subscription.id}/modify_days/',
            {'days_to_add': 5},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
