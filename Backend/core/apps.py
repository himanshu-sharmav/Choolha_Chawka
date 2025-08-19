from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Register cache invalidation signals on model changes
        try:
            from . import cache_signals  # noqa: F401
        except Exception:
            # Avoid crashing app startup if migrations are running
            pass
