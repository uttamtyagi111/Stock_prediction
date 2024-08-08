from django.contrib import admin
from .models import EmailTemplate

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')  # Customize this list based on your model fields
    search_fields = ('name', 'subject')  # Add fields you want to be searchable
