import hashlib
import json
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache


GLOBAL_VERSION_KEY = "GLOBAL_DATA_VERSION"


def get_cache_ttl(default: Optional[int] = None) -> int:
    if default is None:
        default = 120
    return int(getattr(settings, "CACHE_TTL", default))


def get_data_version() -> int:
    version = cache.get(GLOBAL_VERSION_KEY)
    if version is None:
        cache.add(GLOBAL_VERSION_KEY, 1)
        version = 1
    return int(version)


def bump_data_version() -> int:
    try:
        # Using incr ensures atomicity on Redis
        return int(cache.incr(GLOBAL_VERSION_KEY))
    except Exception:
        # Fallback if backend doesn't support incr
        current = get_data_version()
        new_value = current + 1
        cache.set(GLOBAL_VERSION_KEY, new_value, timeout=None)
        return new_value


def normalize_query_params(query_dict) -> Dict[str, Any]:
    items = []
    for key in sorted(query_dict.keys()):
        values = query_dict.getlist(key)
        items.append((key, sorted(values)))
    return dict(items)


def build_cache_key(
    *,
    namespace: str,
    path: str,
    query_params,
    user_id: Optional[int] = None,
    vary_on_user: bool = True,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    payload = {
        "ns": namespace,
        "path": path,
        "q": normalize_query_params(query_params),
        "v": get_data_version(),
    }
    if vary_on_user:
        payload["u"] = user_id or 0
    if extra:
        payload["x"] = extra

    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"cc:{digest}"


