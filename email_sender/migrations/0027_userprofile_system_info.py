# Generated by Django 5.1.2 on 2024-10-29 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_sender', '0026_userprofile_refresh_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='system_info',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
