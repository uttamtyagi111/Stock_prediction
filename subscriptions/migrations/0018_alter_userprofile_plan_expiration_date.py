# Generated by Django 5.1.2 on 2025-01-10 16:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0017_alter_userprofile_plan_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='plan_expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 2, 9, 16, 25, 11, 330645, tzinfo=datetime.timezone.utc)),
        ),
    ]
