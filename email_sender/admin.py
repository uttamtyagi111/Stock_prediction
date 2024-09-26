from django.contrib import admin
from .models import Sender, SMTPServer,UploadedFile

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'name', 'file_url')  # Display the ID, name, file URL, and user

@admin.register(Sender)
class SenderAdmin(admin.ModelAdmin):
    list_display = ('id','user_id','name', 'email')
    search_fields = ('name', 'email')
    ordering = ('name',)

@admin.register(SMTPServer)
class SMTPServerAdmin(admin.ModelAdmin):
    list_display = ('id','user_id','name', 'host', 'port', 'username', 'use_tls')
    search_fields = ('name', 'host', 'username')
    ordering = ('name',)

