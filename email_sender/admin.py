from django.contrib import admin
from .models import EmailTemplate, Sender, SMTPServer,UserEditedTemplate


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_path')

@admin.register(UserEditedTemplate)
class UserEditedTemplateAdmin(admin.ModelAdmin):
    list_display = ('original_template', 'user', 'name', 'template_path')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Admins see all templates
        return qs.filter(user=request.user)  # Users see only their templates

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user  # Assign the user on creation
        super().save_model(request, obj, form, change)

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

