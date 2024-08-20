from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SenderViewSet, EmailTemplateViewSet, SendEmailsView,RegisterView, senders_list, sender_create,sender_detail, sender_form,smtp_server_create
from .views import smtp_servers_list, smtp_server_detail, smtp_server_form ,smtp_server_edit
from .views import email_template_delete,email_template_edit,email_template_form,email_template_list,email_template_create
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'senders', SenderViewSet)
router.register(r'email-templates', EmailTemplateViewSet)

urlpatterns = [
    path('api', include(router.urls)),
    path('senders/', senders_list, name='senders-list'),
    path('senders/<int:pk>/', sender_detail, name='sender_detail'),
    path('senders/create/', sender_create, name='sender-create'),
    path('senders/new/', sender_form, name='sender_form'),
    path('senders/edit/<int:pk>/', sender_form, name='sender_form'),
    path('smtp-servers/', smtp_servers_list, name='smtp_servers-list'),
    path('smtp-servers/<int:pk>/', smtp_server_detail, name='smtp-server-detail'),
    path('smtp-servers/new/', smtp_server_form, name='smtp_server_form'),
    path('smtp-servers/create/', smtp_server_create, name='smtp-server-create'),
    path('smtp-servers/edit/<int:pk>/', smtp_server_edit, name='smtp-server-edit'),
    path('send-emails/', SendEmailsView.as_view(), name='send-emails'),
    path('email-template/', email_template_form, name='email-template-form'),
    path('email-template/', email_template_list, name='email_template_list'),
    path('email-templates/<int:pk>/edit/', email_template_edit, name='email-template-edit'),
    path('email-template/create', email_template_create, name='email-template-create'),
    path('email-templates/<int:pk>/delete/', email_template_delete, name='email-template-delete'),
    path('register/', RegisterView.as_view(), name='register'),]
#     path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
#     path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
# ]
