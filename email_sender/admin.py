from django.contrib import admin
from .models import  SMTPServer,UploadedFile,EmailStatusLog

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'name', 'file_url')  # Display the ID, name, file URL, and user


@admin.register(SMTPServer)
class SMTPServerAdmin(admin.ModelAdmin):
    list_display = ('id','user_id','name', 'host', 'port', 'username', 'use_tls')
    search_fields = ('name', 'host', 'username')
    ordering = ('name',)


@admin.register(EmailStatusLog)
class EmailStatusLogAdmin(admin.ModelAdmin):
    list_display = ('email', 'status', 'timestamp', 'user', 'from_email', 'smtp_server')  # Customize fields to display
    list_filter = ('status', 'user', 'smtp_server')  # Add filters for better searchability
    search_fields = ('email', 'status', 'from_email')  # Add a search box for filtering logs

    def user(self, obj):
        return obj.user.username  # Display the username instead of the user object

    user.short_description = 'User' 