# Generated by Django 5.1.2 on 2024-11-08 22:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0006_alter_userprofile_plan_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='plan_expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 12, 8, 22, 27, 44, 735745, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
