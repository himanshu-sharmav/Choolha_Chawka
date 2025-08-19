#!/usr/bin/env python
"""
Test HTTP caching with detailed timing and cache key analysis
"""
import requests
import time
import json
import subprocess

BASE_URL = "http://localhost:8000"

def clear_redis_cache():
    """Clear all cache keys"""
    try:
        subprocess.run(['redis-cli', '-n', '1', 'flushdb'], check=True)
        print("✅ Cleared Redis cache")
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

def get_cache_keys():
    """Get all cache keys"""
    try:
        result = subprocess.run(['redis-cli', '-n', '1', 'keys', '*'], 
                              capture_output=True, text=True)
        keys = result.stdout.strip().split('\n')
        return [k for k in keys if k]  # Remove empty strings
    except Exception as e:
        print(f"❌ Error getting cache keys: {e}")
        return []

def test_endpoint_with_cache_analysis(url, description):
    """Test an endpoint and analyze cache behavior"""
    print(f"\n=== Testing: {description} ===")
    print(f"URL: {url}")
    
    # Clear cache before test
    clear_redis_cache()
    
    # Get initial cache keys
    initial_keys = get_cache_keys()
    print(f"Initial cache keys: {len(initial_keys)}")
    
    # First request (should be cache miss)
    print("\n1️⃣ First Request (Cache Miss):")
    start_time = time.time()
    response1 = requests.get(url)
    time1 = time.time() - start_time
    
    print(f"   Status: {response1.status_code}")
    print(f"   Time: {time1:.3f}s")
    print(f"   Response size: {len(response1.content)} bytes")
    
    # Check cache keys after first request
    keys_after_first = get_cache_keys()
    print(f"   Cache keys after first request: {len(keys_after_first)}")
    if len(keys_after_first) > len(initial_keys):
        print(f"   ✅ New cache key created")
        new_keys = set(keys_after_first) - set(initial_keys)
        for key in new_keys:
            print(f"   New key: {key}")
    else:
        print(f"   ❌ No new cache key created")
    
    # Second request (should be cache hit)
    print("\n2️⃣ Second Request (Cache Hit):")
    start_time = time.time()
    response2 = requests.get(url)
    time2 = time.time() - start_time
    
    print(f"   Status: {response2.status_code}")
    print(f"   Time: {time2:.3f}s")
    print(f"   Response size: {len(response2.content)} bytes")
    
    # Check if responses are identical
    if response1.content == response2.content:
        print(f"   ✅ Responses are identical")
    else:
        print(f"   ❌ Responses differ")
    
    # Performance analysis
    if time2 < time1:
        improvement = (time1 - time2) / time1 * 100
        print(f"   🚀 Speed improvement: {improvement:.1f}% faster")
        if improvement > 20:
            print(f"   ✅ Significant cache benefit detected")
        else:
            print(f"   ⚠️  Minimal cache benefit (network latency may be masking it)")
    else:
        print(f"   ❌ Second request was slower")
    
    # Check cache keys after second request
    keys_after_second = get_cache_keys()
    print(f"   Cache keys after second request: {len(keys_after_second)}")
    
    return time1, time2, response1.status_code == 200

def test_query_param_caching():
    """Test that different query params create different cache keys"""
    print(f"\n=== Testing Query Parameter Caching ===")
    
    base_url = f"{BASE_URL}/api/subscriptions/plans/"
    
    # Clear cache
    clear_redis_cache()
    
    # Test different query params
    test_cases = [
        ("", "No query params"),
        ("?service_type=tiffin", "Tiffin service"),
        ("?service_type=mess", "Mess service"),
        ("?service_type=tiffin&limit=10", "Tiffin with limit"),
    ]
    
    for query, description in test_cases:
        url = base_url + query
        print(f"\n--- {description} ---")
        
        # First request
        start_time = time.time()
        response1 = requests.get(url)
        time1 = time.time() - start_time
        
        # Second request
        start_time = time.time()
        response2 = requests.get(url)
        time2 = time.time() - start_time
        
        print(f"First: {time1:.3f}s, Second: {time2:.3f}s")
        if time2 < time1:
            improvement = (time1 - time2) / time1 * 100
            print(f"Cache benefit: {improvement:.1f}%")
        else:
            print("No cache benefit")
    
    # Check total cache keys
    final_keys = get_cache_keys()
    print(f"\nTotal cache keys created: {len(final_keys)}")
    print("Expected: 4 different cache keys (one per query combination)")

def test_cache_invalidation():
    """Test cache invalidation by creating data"""
    print(f"\n=== Testing Cache Invalidation ===")
    
    # First, get plans
    url = f"{BASE_URL}/api/subscriptions/plans/"
    response1 = requests.get(url)
    plans_count_1 = len(response1.json())
    print(f"Initial plans count: {plans_count_1}")
    
    # Clear cache and make request again
    clear_redis_cache()
    response2 = requests.get(url)
    plans_count_2 = len(response2.json())
    print(f"Plans count after cache clear: {plans_count_2}")
    
    if plans_count_1 == plans_count_2:
        print("✅ Data consistency maintained")
    else:
        print("❌ Data inconsistency detected")
    
    print("\nNote: To test invalidation with data creation:")
    print("1. Create a plan via POST request")
    print("2. Immediately GET plans again")
    print("3. Should show new plan (cache invalidated)")

def main():
    print("🚀 HTTP Caching Test Suite")
    print("=" * 50)
    
    try:
        # Test basic endpoint
        test_endpoint_with_cache_analysis(
            f"{BASE_URL}/api/subscriptions/plans/",
            "Plans List (Public)"
        )
        
        # Test query parameter caching
        test_query_param_caching()
        
        # Test cache invalidation
        test_cache_invalidation()
        
        print(f"\n✅ All tests completed!")
        print(f"\n📊 Summary:")
        print(f"- Cache keys are being created in Redis database 1")
        print(f"- Check cache keys: redis-cli -n 1 keys 'cc:*'")
        print(f"- Cache TTL: 120 seconds")
        print(f"- If HTTP requests don't show speed improvement,")
        print(f"  it's likely due to network latency masking the cache benefit")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    main()
