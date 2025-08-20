from functools import wraps
from typing import Callable, Optional
import logging

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest
from rest_framework.response import Response

from .cache_utils import build_cache_key, get_cache_ttl

logger = logging.getLogger('app')


def cache_get(ttl: Optional[int] = None, *, vary_on_user: bool = True, namespace: Optional[str] = None):
    """Decorator to cache GET/HEAD DRF responses per path+query (+user if enabled).

    Only caches DRF Response.data payloads. Avoid using for non-JSON responses.
    """

    def decorator(view_func: Callable):
        @wraps(view_func)
        def wrapper(self, request: HttpRequest, *args, **kwargs):
            if request.method not in ("GET", "HEAD"):
                return view_func(self, request, *args, **kwargs)

            ns = namespace or f"{self.__class__.__name__}:{view_func.__name__}"
            cache_key = build_cache_key(
                namespace=ns,
                path=request.path,
                query_params=request.GET,
                user_id=getattr(request.user, "id", None),
                vary_on_user=vary_on_user,
            )

            cached = cache.get(cache_key)
            if cached is not None:
                logger.info(f"cache hit ns={ns} path={request.path}")
                return Response(cached.get("data"), status=cached.get("status", 200))

            response = view_func(self, request, *args, **kwargs)
            try:
                payload = {"data": getattr(response, "data", None), "status": response.status_code}
                cache.set(cache_key, payload, timeout=get_cache_ttl(ttl))
                logger.info(f"cache set ns={ns} path={request.path} ttl={get_cache_ttl(ttl)}")
            except Exception:
                # Do not break the request if caching fails
                logger.warning(f"cache set failed ns={ns} path={request.path}")
                pass
            return response

        return wrapper

    return decorator


class ListRetrieveCacheMixin:
    """Mixin that caches list and retrieve responses for DRF ViewSets.

    Set the following optional class attributes to customize behavior:
    - cache_ttl: int (seconds)
    - cache_vary_on_user: bool
    """

    cache_ttl: Optional[int] = None
    cache_vary_on_user: bool = True

    def _build_key(self, request: HttpRequest, action_name: str) -> str:
        return build_cache_key(
            namespace=f"{self.__class__.__name__}:{action_name}",
            path=request.path,
            query_params=request.GET,
            user_id=getattr(request.user, "id", None) if hasattr(request, 'user') else None,
            vary_on_user=self.cache_vary_on_user,
        )

    def list(self, request: HttpRequest, *args, **kwargs):  # type: ignore[override]
        if request.method not in ("GET", "HEAD"):
            return super().list(request, *args, **kwargs)

        cache_key = self._build_key(request, "list")
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"cache hit ns={self.__class__.__name__}:list path={request.path}")
            return Response(cached.get("data"), status=cached.get("status", 200))

        response = super().list(request, *args, **kwargs)
        try:
            payload = {"data": getattr(response, "data", None), "status": response.status_code}
            cache.set(cache_key, payload, timeout=get_cache_ttl(self.cache_ttl))
            logger.info(f"cache set ns={self.__class__.__name__}:list path={request.path} ttl={get_cache_ttl(self.cache_ttl)}")
        except Exception:
            logger.warning(f"cache set failed ns={self.__class__.__name__}:list path={request.path}")
            pass
        return response

    def retrieve(self, request: HttpRequest, *args, **kwargs):  # type: ignore[override]
        if request.method not in ("GET", "HEAD"):
            return super().retrieve(request, *args, **kwargs)

        cache_key = self._build_key(request, "retrieve")
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"cache hit ns={self.__class__.__name__}:retrieve path={request.path}")
            return Response(cached.get("data"), status=cached.get("status", 200))

        response = super().retrieve(request, *args, **kwargs)
        try:
            payload = {"data": getattr(response, "data", None), "status": response.status_code}
            cache.set(cache_key, payload, timeout=get_cache_ttl(self.cache_ttl))
            logger.info(f"cache set ns={self.__class__.__name__}:retrieve path={request.path} ttl={get_cache_ttl(self.cache_ttl)}")
        except Exception:
            logger.warning(f"cache set failed ns={self.__class__.__name__}:retrieve path={request.path}")
            pass
        return response


