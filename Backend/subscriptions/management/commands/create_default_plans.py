from django.core.management.base import BaseCommand
from subscriptions.models import Plan

class Command(BaseCommand):
    help = 'Create default subscription plans'

    def handle(self, *args, **options):
        plans = [
            # Mess Plans
            {
                'code': 'MESS_ALL',
                'name': 'All Meals - Mess',
                'service_type': 'mess',
                'base_price': 3500,
                'included_meals': ['breakfast', 'lunch', 'dinner'],
                'duration_days': 30,
                'min_duration_days': 7,
                'max_duration_days': 90,
                'allow_custom_duration': True,
            },
            {
                'code': 'MESS_LD',
                'name': 'Lunch + Dinner - Mess',
                'service_type': 'mess',
                'base_price': 3000,
                'included_meals': ['lunch', 'dinner'],
                'duration_days': 30,
                'min_duration_days': 7,
                'max_duration_days': 90,
                'allow_custom_duration': True,
            },
            {
                'code': 'MESS_SINGLE',
                'name': 'Single Meal - Mess',
                'service_type': 'mess',
                'base_price': 1800,
                'included_meals': ['lunch'],
                'duration_days': 30,
                'min_duration_days': 7,
                'max_duration_days': 90,
                'allow_custom_duration': True,
            },
            {
                'code': 'MESS_BREAKFAST',
                'name': 'Breakfast Only - Mess',
                'service_type': 'mess',
                'base_price': 1200,
                'included_meals': ['breakfast'],
                'duration_days': 30,
                'min_duration_days': 7,
                'max_duration_days': 90,
                'allow_custom_duration': True,
            },
            # Tiffin Plans
            {
                'code': 'TIFFIN_ALL',
                'name': 'All Meals - Tiffin',
                'service_type': 'tiffin',
                'base_price': 3800,
                'included_meals': ['breakfast', 'lunch', 'dinner'],
                'duration_days': 30,
                'min_duration_days': 7,
                'max_duration_days': 90,
                'allow_custom_duration': True,
            },
            {
                'code': 'TIFFIN_LD',
                'name': 'Lunch + Dinner - Tiffin',
                'service_type': 'tiffin',
                'base_price': 3200,
                'included_meals': ['lunch', 'dinner'],
                'duration_days': 30,
                'min_duration_days': 7,
                'max_duration_days': 90,
                'allow_custom_duration': True,
            },
            {
                'code': 'TIFFIN_SINGLE',
                'name': 'Single Meal - Tiffin',
                'service_type': 'tiffin',
                'base_price': 1800,
                'included_meals': ['lunch'],
                'duration_days': 30,
                'min_duration_days': 7,
                'max_duration_days': 90,
                'allow_custom_duration': True,
            },
            {
                'code': 'TIFFIN_BREAKFAST',
                'name': 'Breakfast Only - Tiffin',
                'service_type': 'tiffin',
                'base_price': 1400,
                'included_meals': ['breakfast'],
                'duration_days': 30,
                'min_duration_days': 7,
                'max_duration_days': 90,
                'allow_custom_duration': True,
            },
        ]
        
        for plan_data in plans:
            plan, created = Plan.objects.get_or_create(
                code=plan_data['code'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'Created plan: {plan.name}')
            else:
                self.stdout.write(f'Plan already exists: {plan.name}')
