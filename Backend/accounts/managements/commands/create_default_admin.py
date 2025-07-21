from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a default admin user if none exists'

    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='himanshusharma.dev80.com',
                password='defaultpassword123',
                user_type='student'
            )
            self.stdout.write(
                self.style.SUCCESS('Default admin user created successfully')
            )
        else:
            self.stdout.write('Admin user already exists')
