from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SenderViewSet, EmailTemplateViewSet, SendEmailsView, senders_list,sender_detail,smtp_server_create,sender_delete
from .views import smtp_servers_list, smtp_server_detail,smtp_server_edit,sender_edit
from .views import email_template_delete,email_template_form,email_template_list,email_template_create
from .views import default_templates_view, edit_template_view, user_templates_view,edit_user_template
from django.contrib.auth import views as auth_views
from . import views

router = DefaultRouter()
router.register(r'senders', SenderViewSet)
router.register(r'email-templates', EmailTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('send-emails/', SendEmailsView.as_view(), name='send-emails'),
    path('senders/', senders_list, name='senders-list'),
    path('senders/<int:pk>/', sender_detail, name='sender_detail'),
    path('sender/create/', views.create_sender, name='create-sender'),
    path('senders/edit/<int:pk>/', sender_edit, name='sender-edit'),
    path('senders/delete/<int:pk>/', sender_delete, name='sender-delete'),
    path('smtp-servers/', views.smtp_servers_list, name='smtp-servers-list'),
    path('smtp-servers/<int:pk>/', views.smtp_server_detail, name='smtp-server-detail'),
    path('smtp-server/create/', views.smtp_server_create, name='smtp-server-create'),
    path('smtp-servers/edit/<int:pk>/', views.smtp_server_edit, name='smtp-server-edit'),
    path('smtp-servers/delete/<int:pk>/', views.smtp_server_delete, name='smtp-server-delete'),
    # path('email-template/', email_template_form, name='email-template-form'),
    path('email-template/', email_template_list, name='email_template_list'),
    path('default-templates/', default_templates_view, name='default_templates'),
    path('edit-template/<int:template_id>/', edit_template_view, name='edit_template'),
    path('user-templates/', user_templates_view, name='user_templates'),
    path('user-template/edit/<int:pk>/', edit_user_template, name='edit_user_template'),
    path('email-template/create', email_template_create, name='email-template-create'),
    path('email-templates/delete/<int:pk>/', email_template_delete, name='email-template-delete'),
 ]
