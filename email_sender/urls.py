from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SenderViewSet, EmailTemplateViewSet, SendEmailsView
from .views import sender_edit, senders_list,sender_detail,sender_delete
from .views import email_template_list,create_user_template,edit_user_template,delete_user_template,edit_email_template
from .views import edit_email_template, user_templates_view,edit_user_template,ViewTemplateById,get_user_template_by_id
from . import views

router = DefaultRouter()
# router.register(r'senders', SenderViewSet)
router.register(r'email-templates', EmailTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('send-emails/', SendEmailsView.as_view(), name='send-emails'),
    path('senders/', views.senders_list, name='senders-list'),
    path('senders/<int:pk>/', sender_detail, name='sender_detail'),
    path('sender/create/', views.create_sender, name='create-sender'),
    path('senders/edit/<int:pk>/', sender_edit, name='sender-edit'),
    path('senders/delete/<int:pk>/', sender_delete, name='sender-delete'),
    path('smtp-servers/', views.smtp_servers_list, name='smtp-servers-list'),
    path('smtp-servers/<int:pk>/', views.smtp_server_detail, name='smtp-server-detail'),
    path('smtp-server/create/', views.smtp_server_create, name='smtp-server-create'),
    path('smtp-servers/edit/<int:pk>/', views.smtp_server_edit, name='smtp-server-edit'),
    path('smtp-servers/delete/<int:pk>/', views.smtp_server_delete, name='smtp-server-delete'),
    path('email-templates/', email_template_list, name='email_template_list'),
    path('email-template/<int:template_id>/', ViewTemplateById.as_view(), name='view_template_by_id'),
    path('email-template/edit/<int:template_id>/',edit_email_template, name='edit_template'),
    path('user-templates/', user_templates_view, name='user_templates'),
    path('user-template/<int:pk>/', get_user_template_by_id, name='get_user_template_by_id'),
    path('user-template/edit/<int:pk>/', edit_user_template, name='edit-user-template'),
    path('user-template/create/', create_user_template, name='create-user-template'),
    path('user-templates/delete/<int:pk>/', delete_user_template, name='delete-user-template'),
 ]
