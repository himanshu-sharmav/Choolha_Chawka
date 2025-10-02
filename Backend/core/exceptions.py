import logging
import traceback
from typing import Any

from rest_framework.views import exception_handler
from rest_framework.response import Response


logger = logging.getLogger('app')


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)

    view = context.get('view')
    request = context.get('request')
    user_id = getattr(getattr(request, 'user', None), 'id', None)
    path = getattr(request, 'get_full_path', lambda: None)()

    if response is not None:
        logger.error(
            "drf exception view=%s path=%s user_id=%s status=%s data=%s",
            getattr(view, '__class__', type('v', (), {})).__name__,
            path,
            user_id,
            response.status_code,
            response.data,
        )
        return response

    # Unhandled -> log stack
    logger.exception(
        "unhandled exception in view=%s path=%s user_id=%s\n%s",
        getattr(view, '__class__', type('v', (), {})).__name__,
        path,
        user_id,
        ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    )
    return response


