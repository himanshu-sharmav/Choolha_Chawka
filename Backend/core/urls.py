from django.urls import path
from . import views

urlpatterns = [
    # Cache monitoring endpoints
    path('cache/status/', views.cache_status, name='cache_status'),
    path('cache/test/', views.cache_test, name='cache_test'),
    path('cache/invalidate/', views.cache_invalidation_test, name='cache_invalidation_test'),
]
