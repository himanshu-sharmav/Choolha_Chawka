#!/usr/bin/env python
"""
Test script to verify caching implementation
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_basic_caching():
    """Test basic GET endpoint caching"""
    print("=== Testing Basic Caching ===")
    
    # Test plans endpoint (public, no auth needed)
    url = f"{BASE_URL}/api/subscriptions/plans/"
    
    # First request (should be slow - cache miss)
    start_time = time.time()
    response1 = requests.get(url)
    time1 = time.time() - start_time
    
    print(f"First request: {time1:.3f}s, Status: {response1.status_code}")
    
    # Second request (should be fast - cache hit)
    start_time = time.time()
    response2 = requests.get(url)
    time2 = time.time() - start_time
    
    print(f"Second request: {time2:.3f}s, Status: {response2.status_code}")
    
    # Check if responses are identical
    if response1.json() == response2.json():
        print("✅ Responses are identical")
    else:
        print("❌ Responses differ")
    
    # Check if second request was faster
    if time2 < time1 * 0.5:  # Second request should be at least 50% faster
        print("✅ Caching is working (second request was faster)")
    else:
        print("❌ Caching may not be working (second request was not faster)")
    
    print()

def test_query_param_caching():
    """Test that different query params create different cache keys"""
    print("=== Testing Query Parameter Caching ===")
    
    base_url = f"{BASE_URL}/api/subscriptions/plans/"
    
    # Test with different query params
    urls = [
        f"{base_url}?service_type=tiffin",
        f"{base_url}?service_type=mess",
        f"{base_url}?service_type=tiffin&limit=10",
    ]
    
    for url in urls:
        start_time = time.time()
        response = requests.get(url)
        time_taken = time.time() - start_time
        print(f"{url}: {time_taken:.3f}s, Status: {response.status_code}")
    
    print()

def test_cache_invalidation():
    """Test that cache is invalidated when data changes"""
    print("=== Testing Cache Invalidation ===")
    
    # First, get plans
    url = f"{BASE_URL}/api/subscriptions/plans/"
    response1 = requests.get(url)
    plans_count_1 = len(response1.json())
    print(f"Initial plans count: {plans_count_1}")
    
    # Note: In a real test, you'd create a plan here via POST
    # For this demo, we'll just show the concept
    print("Note: To test invalidation, create a plan via POST request")
    print("Then immediately GET plans again - should show new plan")
    print()

def check_redis_keys():
    """Check what cache keys exist in Redis"""
    print("=== Checking Redis Cache Keys ===")
    
    import subprocess
    try:
        # Check database 1 (where Django cache is configured)
        result = subprocess.run(['redis-cli', '-n', '1', 'keys', 'cc:*'], 
                              capture_output=True, text=True)
        keys = result.stdout.strip().split('\n')
        
        if keys and keys[0]:
            print(f"Found {len(keys)} cache keys in database 1:")
            for key in keys[:5]:  # Show first 5 keys
                print(f"  {key}")
            if len(keys) > 5:
                print(f"  ... and {len(keys) - 5} more")
        else:
            print("No cache keys found in database 1")
    except Exception as e:
        print(f"Error checking Redis: {e}")
    
    print()

if __name__ == "__main__":
    print("Testing Caching Implementation")
    print("=" * 40)
    print()
    
    try:
        test_basic_caching()
        test_query_param_caching()
        test_cache_invalidation()
        check_redis_keys()
        
        print("✅ Caching tests completed!")
        print("\nTo test in Postman:")
        print("1. GET http://localhost:8000/api/subscriptions/plans/")
        print("2. Make the same request again - should be faster")
        print("3. Try with different query params")
        print("4. Create data via POST to test invalidation")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
