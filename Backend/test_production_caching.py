#!/usr/bin/env python
"""
Test caching in production environment
"""
import requests
import time
import json
from datetime import datetime

# Update this to your Railway production URL
PRODUCTION_URL = "https://api-dev.choolhachowka.com"

def test_cache_status():
    """Test cache status endpoint"""
    print("=== Testing Cache Status ===")
    
    try:
        response = requests.get(f"{PRODUCTION_URL}/api/core/cache/status/")
        data = response.json()
        
        print(f"Status: {data.get('status')}")
        print(f"Cache Working: {data.get('cache_working')}")
        print(f"Data Version: {data.get('data_version')}")
        print(f"Cache TTL: {data.get('cache_ttl_seconds')} seconds")
        print(f"Timestamp: {data.get('timestamp')}")
        
        if data.get('cache_working'):
            print("✅ Cache is working in production!")
        else:
            print("❌ Cache is not working in production")
            if 'error' in data:
                print(f"Error: {data['error']}")
        
        return data.get('cache_working', False)
        
    except Exception as e:
        print(f"❌ Error testing cache status: {e}")
        return False

def test_cache_performance():
    """Test cache performance with repeated requests"""
    print("\n=== Testing Cache Performance ===")
    
    url = f"{PRODUCTION_URL}/api/core/cache/test/"
    
    # First request (cache miss)
    print("1️⃣ First Request (Cache Miss):")
    start_time = time.time()
    response1 = requests.get(url)
    time1 = time.time() - start_time
    
    data1 = response1.json()
    print(f"   Status: {response1.status_code}")
    print(f"   Cache Hit: {data1.get('cache_hit')}")
    print(f"   Response Time: {data1.get('response_time_ms')}ms")
    print(f"   Actual Time: {time1:.3f}s")
    
    # Second request (cache hit)
    print("\n2️⃣ Second Request (Cache Hit):")
    start_time = time.time()
    response2 = requests.get(url)
    time2 = time.time() - start_time
    
    data2 = response2.json()
    print(f"   Status: {response2.status_code}")
    print(f"   Cache Hit: {data2.get('cache_hit')}")
    print(f"   Response Time: {data2.get('response_time_ms')}ms")
    print(f"   Actual Time: {time2:.3f}s")
    
    # Performance analysis
    if time2 < time1:
        improvement = (time1 - time2) / time1 * 100
        print(f"\n🚀 Speed improvement: {improvement:.1f}% faster")
        if improvement > 20:
            print("✅ Significant cache benefit detected")
        else:
            print("⚠️  Minimal cache benefit (network latency may be masking it)")
    else:
        print(f"\n❌ Second request was slower")
    
    return data1.get('cache_hit') == False and data2.get('cache_hit') == True

def test_api_endpoint_caching():
    """Test actual API endpoint caching"""
    print("\n=== Testing API Endpoint Caching ===")
    
    url = f"{PRODUCTION_URL}/api/subscriptions/plans/"
    
    # First request
    print("1️⃣ First Request:")
    start_time = time.time()
    response1 = requests.get(url)
    time1 = time.time() - start_time
    
    print(f"   Status: {response1.status_code}")
    print(f"   Time: {time1:.3f}s")
    print(f"   Response Size: {len(response1.content)} bytes")
    
    # Second request
    print("\n2️⃣ Second Request:")
    start_time = time.time()
    response2 = requests.get(url)
    time2 = time.time() - start_time
    
    print(f"   Status: {response2.status_code}")
    print(f"   Time: {time2:.3f}s")
    print(f"   Response Size: {len(response2.content)} bytes")
    
    # Check if responses are identical
    if response1.content == response2.content:
        print("   ✅ Responses are identical")
    else:
        print("   ❌ Responses differ")
    
    # Performance analysis
    if time2 < time1:
        improvement = (time1 - time2) / time1 * 100
        print(f"\n🚀 Speed improvement: {improvement:.1f}% faster")
    else:
        print(f"\n❌ Second request was slower")
    
    return time2 < time1

def test_cache_invalidation():
    """Test cache invalidation"""
    print("\n=== Testing Cache Invalidation ===")
    
    url = f"{PRODUCTION_URL}/api/core/cache/invalidate/"
    
    try:
        response = requests.post(url)
        data = response.json()
        
        if data.get('success'):
            print("✅ Cache invalidation successful")
            print(f"Old Version: {data.get('old_version')}")
            print(f"New Version: {data.get('new_version')}")
            print(f"Message: {data.get('message')}")
            return True
        else:
            print("❌ Cache invalidation failed")
            print(f"Error: {data.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing cache invalidation: {e}")
        return False

def test_query_param_caching():
    """Test that different query params create different cache keys"""
    print("\n=== Testing Query Parameter Caching ===")
    
    base_url = f"{PRODUCTION_URL}/api/subscriptions/plans/"
    
    test_cases = [
        ("", "No query params"),
        ("?service_type=tiffin", "Tiffin service"),
        ("?service_type=mess", "Mess service"),
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

def main():
    print("🚀 Production Caching Test Suite")
    print("=" * 50)
    print(f"Testing URL: {PRODUCTION_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    try:
        # Test cache status
        cache_working = test_cache_status()
        
        if cache_working:
            # Test cache performance
            performance_ok = test_cache_performance()
            
            # Test API endpoint caching
            api_caching_ok = test_api_endpoint_caching()
            
            # Test query parameter caching
            test_query_param_caching()
            
            # Test cache invalidation
            invalidation_ok = test_cache_invalidation()
            
            print(f"\n✅ Production Caching Test Summary:")
            print(f"- Cache Status: {'✅ Working' if cache_working else '❌ Not Working'}")
            print(f"- Performance: {'✅ Good' if performance_ok else '⚠️  Needs Investigation'}")
            print(f"- API Caching: {'✅ Working' if api_caching_ok else '⚠️  Needs Investigation'}")
            print(f"- Invalidation: {'✅ Working' if invalidation_ok else '❌ Not Working'}")
            
        else:
            print(f"\n❌ Cache is not working in production")
            print(f"Check your Redis configuration and Railway environment variables")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to production server")
        print("Make sure the URL is correct and the server is running")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    main()
