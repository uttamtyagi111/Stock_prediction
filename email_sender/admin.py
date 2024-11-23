from django.contrib import admin
from .models import  SMTPServer,UploadedFile,EmailStatusLog

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'name', 'file_url')

@admin.register(SMTPServer)
class SMTPServerAdmin(admin.ModelAdmin):
    list_display = ('id','user_id','name', 'host', 'port', 'username', 'use_tls')
    search_fields = ('name', 'host', 'username')
    ordering = ('name',)


@admin.register(EmailStatusLog)
class EmailStatusLogAdmin(admin.ModelAdmin):
    list_display = ('id','email', 'status', 'timestamp', 'user', 'from_email', 'smtp_server')  
    search_fields = ('email', 'status', 'from_email')

    def user(self, obj):
        return obj.user.username  

    user.short_description = 'User' 