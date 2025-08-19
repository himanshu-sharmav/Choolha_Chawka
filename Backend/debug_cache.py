#!/usr/bin/env python
"""
Debug script to test cache functionality in detail
"""
import os
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.cache import cache
from django.test import RequestFactory
from core.cache_utils import build_cache_key, get_cache_ttl
from subscriptions.views import PlanViewSet

def test_cache_key_generation():
    """Test cache key generation"""
    print("=== Testing Cache Key Generation ===")
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/api/subscriptions/plans/')
    
    # Generate cache key
    key = build_cache_key(
        namespace='PlanViewSet:list',
        path=request.path,
        query_params=request.GET,
        user_id=None,
        vary_on_user=False
    )
    
    print(f"Generated key: {key}")
    print(f"Key length: {len(key)}")
    print()

def test_cache_set_get():
    """Test basic cache set/get operations"""
    print("=== Testing Cache Set/Get ===")
    
    test_data = {"test": "data", "number": 123}
    test_key = "test_cache_key"
    
    # Set cache
    cache.set(test_key, test_data, 60)
    print(f"Cache set: {test_key}")
    
    # Get cache
    retrieved = cache.get(test_key)
    print(f"Cache get: {retrieved}")
    print(f"Data matches: {retrieved == test_data}")
    print()

def test_viewset_caching():
    """Test ViewSet caching"""
    print("=== Testing ViewSet Caching ===")
    
    factory = RequestFactory()
    viewset = PlanViewSet()
    
    # Create request
    request = factory.get('/api/subscriptions/plans/')
    
    # Test list method
    print("Testing PlanViewSet.list()...")
    
    # First call
    start_time = time.time()
    response1 = viewset.list(request)
    time1 = time.time() - start_time
    print(f"First call: {time1:.3f}s")
    
    # Second call
    start_time = time.time()
    response2 = viewset.list(request)
    time2 = time.time() - start_time
    print(f"Second call: {time2:.3f}s")
    
    print(f"Speed improvement: {time1/time2:.2f}x")
    print()

def check_cache_keys():
    """Check all cache keys"""
    print("=== Checking All Cache Keys ===")
    
    import subprocess
    try:
        result = subprocess.run(['redis-cli', '-n', '1', 'keys', '*'], 
                              capture_output=True, text=True)
        keys = result.stdout.strip().split('\n')
        
        if keys and keys[0]:
            print(f"All keys in database 1:")
            for key in keys:
                print(f"  {key}")
        else:
            print("No keys found")
    except Exception as e:
        print(f"Error: {e}")
    
    print()

if __name__ == "__main__":
    print("Debugging Cache Implementation")
    print("=" * 40)
    print()
    
    test_cache_key_generation()
    test_cache_set_get()
    test_viewset_caching()
    check_cache_keys()
