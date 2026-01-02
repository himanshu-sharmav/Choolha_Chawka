#!/usr/bin/env python
"""
Test script for Cart API endpoints.
Tests the multi-plan cart system with custom duration feature.
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


def test_cart_api():
    """Test all cart API endpoints"""
    print("=" * 60)
    print("CART API TEST SUITE")
    print("=" * 60)
    
    # First, let's check if we have a test user
    try:
        user = User.objects.filter(user_type='student').first()
        if not user:
            user = User.objects.filter(user_type='regular').first()
        if not user:
            print("No customer user found. Creating test user...")
            user = User.objects.create_user(
                email='testcustomer@test.com',
                username='testcustomer',
                password='testpass123',
                user_type='student',
                phone='9999999999'
            )
            print(f"Created test user: {user.email}")
    except Exception as e:
        print(f"Error getting/creating user: {e}")
        return
    
    # Get auth token
    print(f"\n1. Getting auth token for {user.username}...")
    token = get_auth_token(user.username, 'testpass123')
    
    if not token:
        # Try with a known password or create new user
        print("   Trying to reset password and login again...")
        user.set_password('testpass123')
        user.save()
        token = get_auth_token(user.username, 'testpass123')
    
    if not token:
        print("   FAILED: Could not get auth token")
        return
    
    print(f"   SUCCESS: Got token")
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test 1: Get plans
    print("\n2. Testing GET /api/subscriptions/plans/...")
    response = requests.get(f'{BASE_URL}/subscriptions/plans/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        plans = response.json()
        print(f"   SUCCESS: Found {len(plans)} plans")
        for plan in plans[:3]:
            print(f"   - {plan.get('name')}: ₹{plan.get('base_price')} ({plan.get('min_duration_days')}-{plan.get('max_duration_days')} days)")
    else:
        print(f"   FAILED: {response.text}")
        return
    
    # Test 2: Get cart (should be empty or create new)
    print("\n3. Testing GET /api/subscriptions/cart/...")
    response = requests.get(f'{BASE_URL}/subscriptions/cart/', headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        cart = response.json()
        print(f"   SUCCESS: Cart has {len(cart.get('items', []))} items, total: ₹{cart.get('total', 0)}")
    else:
        print(f"   FAILED: {response.text}")
    
    # Test 3: Add item to cart
    if plans:
        plan_id = plans[0]['id']
        print(f"\n4. Testing POST /api/subscriptions/cart/add/ (plan_id={plan_id}, duration=15 days)...")
        response = requests.post(
            f'{BASE_URL}/subscriptions/cart/add/',
            headers=headers,
            json={'plan_id': plan_id, 'duration_days': 15}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"   SUCCESS: {data.get('message')}")
            item_id = data.get('item', {}).get('id')
        else:
            print(f"   Response: {response.text}")
            # Try to get existing item
            cart_response = requests.get(f'{BASE_URL}/subscriptions/cart/', headers=headers)
            if cart_response.status_code == 200:
                cart = cart_response.json()
                if cart.get('items'):
                    item_id = cart['items'][0]['id']
                    print(f"   Using existing cart item: {item_id}")
                else:
                    item_id = None
            else:
                item_id = None
    
    # Test 4: Get cart again to see the item
    print("\n5. Testing GET /api/subscriptions/cart/ (after adding item)...")
    response = requests.get(f'{BASE_URL}/subscriptions/cart/', headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        cart = response.json()
        print(f"   SUCCESS: Cart has {len(cart.get('items', []))} items")
        for item in cart.get('items', []):
            print(f"   - {item.get('plan_name')}: {item.get('custom_duration_days')} days = ₹{item.get('calculated_price')}")
        print(f"   Total: ₹{cart.get('total', 0)}")
    
    # Test 5: Update duration
    if item_id:
        print(f"\n6. Testing PATCH /api/subscriptions/cart/{item_id}/update/ (duration=20 days)...")
        response = requests.patch(
            f'{BASE_URL}/subscriptions/cart/{item_id}/update/',
            headers=headers,
            json={'duration_days': 20}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   SUCCESS: {data.get('message')}")
        else:
            print(f"   Response: {response.text}")
    
    # Test 6: Add another plan
    if len(plans) > 1:
        plan_id_2 = plans[1]['id']
        print(f"\n7. Testing POST /api/subscriptions/cart/add/ (second plan, id={plan_id_2})...")
        response = requests.post(
            f'{BASE_URL}/subscriptions/cart/add/',
            headers=headers,
            json={'plan_id': plan_id_2, 'duration_days': 10}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    
    # Test 7: Get final cart
    print("\n8. Testing GET /api/subscriptions/cart/ (final state)...")
    response = requests.get(f'{BASE_URL}/subscriptions/cart/', headers=headers)
    if response.status_code == 200:
        cart = response.json()
        print(f"   SUCCESS: Cart summary:")
        for item in cart.get('items', []):
            print(f"   - {item.get('plan_name')}: {item.get('custom_duration_days')} days = ₹{item.get('calculated_price')}")
        print(f"   TOTAL: ₹{cart.get('total', 0)}")
    
    # Test 8: Remove item
    if item_id:
        print(f"\n9. Testing DELETE /api/subscriptions/cart/{item_id}/remove/...")
        response = requests.delete(
            f'{BASE_URL}/subscriptions/cart/{item_id}/remove/',
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   SUCCESS: {response.json().get('message')}")
        else:
            print(f"   Response: {response.text}")
    
    # Test 9: Clear cart
    print("\n10. Testing DELETE /api/subscriptions/cart/clear/...")
    response = requests.delete(f'{BASE_URL}/subscriptions/cart/clear/', headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   SUCCESS: {response.json().get('message')}")
    
    # Test 10: Verify cart is empty
    print("\n11. Verifying cart is empty...")
    response = requests.get(f'{BASE_URL}/subscriptions/cart/', headers=headers)
    if response.status_code == 200:
        cart = response.json()
        print(f"   Cart items: {len(cart.get('items', []))}")
        print(f"   Total: ₹{cart.get('total', 0)}")
    
    print("\n" + "=" * 60)
    print("CART API TESTS COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    test_cart_api()
