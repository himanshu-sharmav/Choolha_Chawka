from django.apps import apps
from django.db.models.signals import post_delete, post_save

from .cache_utils import bump_data_version


def _invalidate_on_change(sender, **kwargs):
    # Bump global data version on any model change
    try:
        bump_data_version()
    except Exception:
        # Never block writes due to caching errors
        pass


def connect_signals():
    # Connect to all models in installed apps for broad invalidation
    for model in apps.get_models():
        post_save.connect(_invalidate_on_change, sender=model, dispatch_uid=f"cache_ps_{model._meta.label}")
        post_delete.connect(_invalidate_on_change, sender=model, dispatch_uid=f"cache_pd_{model._meta.label}")


# Connect on import (apps.CoreConfig.ready imports this module)
connect_signals()


