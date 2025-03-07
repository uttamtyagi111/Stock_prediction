# Generated by Django 5.1.2 on 2025-03-03 18:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_sender', '0040_rename_created_at_subjectfile_uploaded_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaign',
            name='uploaded_file_name',
        ),
        migrations.AddField(
            model_name='campaign',
            name='uploaded_file',
            field=models.ForeignKey(blank=True, help_text='Template Associated with the campaign', null=True, on_delete=django.db.models.deletion.CASCADE, to='email_sender.uploadedfile'),
        ),
    ]
