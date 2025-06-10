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
                'can_add_breakfast': False,
            },
            {
                'code': 'MESS_LD',
                'name': 'Lunch + Dinner - Mess',
                'service_type': 'mess',
                'base_price': 3000,
                'included_meals': ['lunch', 'dinner'],
            },
            {
                'code': 'MESS_SINGLE',
                'name': 'Single Meal - Mess',
                'service_type': 'mess',
                'base_price': 1800,
                'included_meals': ['lunch'],  # User can choose lunch or dinner
            },
            # Tiffin Plans
            {
                'code': 'TIFFIN_ALL',
                'name': 'All Meals - Tiffin',
                'service_type': 'tiffin',
                'base_price': 3800,
                'included_meals': ['breakfast', 'lunch', 'dinner'],
                'can_add_breakfast': False,
            },
            {
                'code': 'TIFFIN_LD',
                'name': 'Lunch + Dinner - Tiffin',
                'service_type': 'tiffin',
                'base_price': 3200,
                'included_meals': ['lunch', 'dinner'],
            },
            {
                'code': 'TIFFIN_SINGLE',
                'name': 'Single Meal - Tiffin',
                'service_type': 'tiffin',
                'base_price': 1800,
                'included_meals': ['lunch'],  # User can choose lunch or dinner
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
