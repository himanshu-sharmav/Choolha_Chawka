#!/usr/bin/env python
"""
Test script for Checkout API endpoints.
Tests the checkout flow for multi-plan cart system.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import requests
from django.contrib.auth import get_user_model

User = get_user_model()
BASE_URL = 'http://127.0.0.1:8001/api'


def get_auth_token(username, password):
    """Get JWT token for authentication"""
    response = requests.post(f'{BASE_URL}/accounts/login/', json={
        'username': username,
        'password': password
    })
    if response.status_code == 200:
        data = response.json()
        return data.get('access') or data.get('tokens', {}).get('access')
    print(f"Login failed: {response.status_code} - {response.text}")
    return None


def test_checkout_api():
    """Test checkout API endpoints"""
    print("=" * 60)
    print("CHECKOUT API TEST SUITE")
    print("=" * 60)
    
    # Get test user
    try:
        user = User.objects.get(username='testcustomer')
    except User.DoesNotExist:
        print("Test user not found. Run test_cart_api.py first.")
        return
    
    # Get auth token
    print(f"\n1. Getting auth token for {user.username}...")
    token = get_auth_token(user.username, 'testpass123')
    
    if not token:
        print("   FAILED: Could not get auth token")
        return
    
    print(f"   SUCCESS: Got token")
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get plans
    print("\n2. Getting available plans...")
    response = requests.get(f'{BASE_URL}/subscriptions/plans/')
    if response.status_code != 200:
        print(f"   FAILED: {response.text}")
        return
    plans = response.json()
    print(f"   Found {len(plans)} plans")
    
    # Clear cart first
    print("\n3. Clearing cart...")
    requests.delete(f'{BASE_URL}/subscriptions/cart/clear/', headers=headers)
    
    # Add items to cart
    print("\n4. Adding items to cart...")
    for i, plan in enumerate(plans[:2]):  # Add first 2 plans
        response = requests.post(
            f'{BASE_URL}/subscriptions/cart/add/',
            headers=headers,
            json={'plan_id': plan['id'], 'duration_days': 10 + i * 5}
        )
        if response.status_code in [200, 201]:
            print(f"   Added: {plan['name']} ({10 + i * 5} days)")
        else:
            print(f"   Failed to add {plan['name']}: {response.text}")
    
    # Get cart
    print("\n5. Getting cart summary...")
    response = requests.get(f'{BASE_URL}/subscriptions/cart/', headers=headers)
    if response.status_code == 200:
        cart = response.json()
        print(f"   Items: {cart.get('item_count', 0)}")
        print(f"   Total: ₹{cart.get('total', 0)}")
    
    # Test checkout (create Razorpay order)
    print("\n6. Testing POST /api/subscriptions/cart/checkout/...")
    response = requests.post(f'{BASE_URL}/subscriptions/cart/checkout/', headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   SUCCESS: Razorpay order created")
        print(f"   - Bundle Order ID: {data.get('bundle_order_id')}")
        print(f"   - Razorpay Order ID: {data.get('razorpay_order_id')}")
        print(f"   - Amount: ₹{data.get('amount')}")
        print(f"   - Key ID: {data.get('key_id')[:10]}...")
        
        # Test verify endpoint (will fail without real payment)
        print("\n7. Testing POST /api/subscriptions/cart/verify/ (expected to fail)...")
        verify_response = requests.post(
            f'{BASE_URL}/subscriptions/cart/verify/',
            headers=headers,
            json={
                'bundle_order_id': data.get('bundle_order_id'),
                'razorpay_payment_id': 'fake_payment_id',
                'razorpay_signature': 'fake_signature'
            }
        )
        print(f"   Status: {verify_response.status_code}")
        print(f"   Response: {verify_response.json()}")
    else:
        print(f"   Response: {response.json()}")
    
    # Test empty cart checkout
    print("\n8. Testing checkout with empty cart...")
    requests.delete(f'{BASE_URL}/subscriptions/cart/clear/', headers=headers)
    response = requests.post(f'{BASE_URL}/subscriptions/cart/checkout/', headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print("\n" + "=" * 60)
    print("CHECKOUT API TESTS COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    test_checkout_api()
