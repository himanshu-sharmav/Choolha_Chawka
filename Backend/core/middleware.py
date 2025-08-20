import logging
import time
from typing import Callable

from django.http import HttpRequest, HttpResponse


logger = logging.getLogger('app')


class RequestLoggingMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time.time()

        user_id = getattr(request.user, 'id', None)
        method = request.method
        path = request.get_full_path()
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))

        logger.info(f"request started method={method} path={path} user_id={user_id} ip={ip}")

        try:
            response = self.get_response(request)
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.exception(f"request failed method={method} path={path} user_id={user_id} duration_ms={duration_ms}")
            raise

        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"request finished method={method} path={path} status={getattr(response, 'status_code', None)} "
            f"user_id={user_id} duration_ms={duration_ms}"
        )

        return response


