from django.contrib import admin
from .models import EmailTemplate, Sender, SMTPServer

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    search_fields = ('name', 'subject')
    ordering = ('name',)

@admin.register(Sender)
class SenderAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name', 'email')
    ordering = ('name',)

@admin.register(SMTPServer)
class SMTPServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'port', 'username', 'use_tls')
    search_fields = ('name', 'host', 'username')
    ordering = ('name',)

