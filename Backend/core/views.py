from django.shortcuts import render
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .cache_utils import get_data_version, get_cache_ttl
import json
import time


# Create your views here.


@require_http_methods(["GET"])
def cache_status(request):
    """Get cache status and statistics"""
    try:
        # Test cache functionality
        test_key = f"cache_test_{int(time.time())}"
        test_value = {"timestamp": timezone.now().isoformat(), "test": True}
        
        # Set cache
        cache.set(test_key, test_value, 60)
        
        # Get cache
        retrieved = cache.get(test_key)
        
        # Clean up
        cache.delete(test_key)
        
        cache_working = retrieved == test_value
        
        # Get cache statistics
        data_version = get_data_version()
        cache_ttl = get_cache_ttl()
        
        return JsonResponse({
            "cache_working": cache_working,
            "data_version": data_version,
            "cache_ttl_seconds": cache_ttl,
            "timestamp": timezone.now().isoformat(),
            "status": "healthy" if cache_working else "error"
        })
        
    except Exception as e:
        return JsonResponse({
            "cache_working": False,
            "error": str(e),
            "timestamp": timezone.now().isoformat(),
            "status": "error"
        }, status=500)


@require_http_methods(["GET"])
def cache_test(request):
    """Test cache performance with a simple endpoint"""
    start_time = time.time()
    
    # Generate cache key based on request
    cache_key = f"cache_test_endpoint_{request.path}_{request.GET.urlencode()}"
    
    # Try to get from cache first
    cached_response = cache.get(cache_key)
    
    if cached_response:
        # Cache hit
        response_time = time.time() - start_time
        return JsonResponse({
            "cache_hit": True,
            "response_time_ms": round(response_time * 1000, 2),
            "data": cached_response,
            "timestamp": timezone.now().isoformat()
        })
    else:
        # Cache miss - simulate some work
        time.sleep(0.1)  # Simulate database query
        
        # Create response data
        response_data = {
            "message": "Cache test response",
            "cache_key": cache_key,
            "generated_at": timezone.now().isoformat(),
            "random_data": list(range(10))
        }
        
        # Cache the response
        cache.set(cache_key, response_data, 30)  # 30 seconds TTL
        
        response_time = time.time() - start_time
        
        return JsonResponse({
            "cache_hit": False,
            "response_time_ms": round(response_time * 1000, 2),
            "data": response_data,
            "timestamp": timezone.now().isoformat()
        })


@csrf_exempt
@require_http_methods(["POST"])
def cache_invalidation_test(request):
    """Test cache invalidation by bumping data version"""
    try:
        from .cache_utils import bump_data_version
        
        old_version = get_data_version()
        new_version = bump_data_version()
        
        return JsonResponse({
            "success": True,
            "old_version": old_version,
            "new_version": new_version,
            "timestamp": timezone.now().isoformat(),
            "message": "Cache invalidated - all cached GET requests will be refreshed"
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=500)
