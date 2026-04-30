# Generated migration for multi-plan cart feature

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subscriptions', '0006_subscription_subscriptio_user_id_2a19e8_idx_and_more'),
    ]

    operations = [
        # 1. Add new fields to Plan for custom duration support
        migrations.AddField(
            model_name='plan',
            name='min_duration_days',
            field=models.PositiveIntegerField(default=7),
        ),
        migrations.AddField(
            model_name='plan',
            name='max_duration_days',
            field=models.PositiveIntegerField(default=90),
        ),
        migrations.AddField(
            model_name='plan',
            name='allow_custom_duration',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='daily_rate_override',
            field=models.DecimalField(
                blank=True, 
                decimal_places=2, 
                help_text='Optional: Override calculated daily rate', 
                max_digits=10, 
                null=True
            ),
        ),
        
        # 2. Remove breakfast fields from Plan
        migrations.RemoveField(
            model_name='plan',
            name='can_add_breakfast',
        ),
        migrations.RemoveField(
            model_name='plan',
            name='breakfast_addon_price',
        ),
        
        # 3. Create Cart model
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cart', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        
        # 4. Create BundleOrder model
        migrations.CreateModel(
            name='BundleOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_amount', models.PositiveIntegerField()),
                ('status', models.CharField(
                    choices=[
                        ('PENDING', 'Pending Payment'), 
                        ('PAID', 'Paid'), 
                        ('PARTIALLY_CANCELLED', 'Partially Cancelled'), 
                        ('CANCELLED', 'Cancelled')
                    ], 
                    default='PENDING', 
                    max_length=20
                )),
                ('razorpay_order_id', models.CharField(blank=True, max_length=100)),
                ('razorpay_payment_id', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bundle_orders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # 5. Create CartItem model
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('custom_duration_days', models.PositiveIntegerField(default=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='subscriptions.cart')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subscriptions.plan')),
            ],
        ),
        migrations.AddConstraint(
            model_name='cartitem',
            constraint=models.UniqueConstraint(fields=['cart', 'plan'], name='unique_cart_plan'),
        ),
        
        # 6. Add bundle_order FK to Subscription
        migrations.AddField(
            model_name='subscription',
            name='bundle_order',
            field=models.ForeignKey(
                blank=True, 
                null=True, 
                on_delete=django.db.models.deletion.SET_NULL, 
                related_name='subscriptions', 
                to='subscriptions.bundleorder'
            ),
        ),
        
        # 7. Remove breakfast fields from Subscription
        migrations.RemoveField(
            model_name='subscription',
            name='breakfast_included',
        ),
        migrations.RemoveField(
            model_name='subscription',
            name='breakfast_addon_price',
        ),
    ]
