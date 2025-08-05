# accounts/filters.py
from django_filters import rest_framework as filters
from .models import User

class UserFilter(filters.FilterSet):
    """
    Custom filter for Users to allow filtering by meal type
    through their active subscriptions.
    """
    meal_type = filters.CharFilter(method='filter_by_meal_type')

    class Meta:
        model = User
        fields = [
            'user_type', 
            'is_active', 
            'phone_verified',
            'is_mess_user',
            'is_tiffin_user'
        ]

    def filter_by_meal_type(self, queryset, name, value):
        """
        Filters the queryset to include only users who have an active
        subscription to a plan that includes the specified meal type.
        
        Example values: 'breakfast', 'lunch', 'dinner'
        """
        if value:
            # This filters users based on the 'included_meals' field of their plan
            return queryset.filter(
                subscriptions__status='ACTIVE',
                subscriptions__plan__included_meals__contains=value
            ).distinct()
        return queryset

