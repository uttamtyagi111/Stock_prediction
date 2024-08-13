from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SenderViewSet, EmailTemplateViewSet, SendEmailsView, senders_list, sender_detail, sender_form
from .views import smtp_servers_list, smtp_server_detail, smtp_server_form 

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'senders', SenderViewSet)
router.register(r'email-templates', EmailTemplateViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('api/', include(router.urls)),
    path('send-emails/', SendEmailsView.as_view(), name='send-emails'),
    
    # Add these new URL patterns for traditional Django views
    path('senders/', senders_list, name='senders-list'),
    path('senders/<int:pk>/', sender_detail, name='sender-detail'),
    path('senders/create/', sender_form, name='sender-create'),
    path('senders/<int:pk>/edit/', sender_form, name='sender-edit'),
    path('smtp-servers/', smtp_servers_list, name='smtp-servers-list'),
    path('smtp-servers/<int:pk>/', smtp_server_detail, name='smtp-server-detail'),
    path('smtp-servers/create/', smtp_server_form, name='smtp-server-create'),
    path('smtp-servers/<int:pk>/edit/', smtp_server_form, name='smtp-server-edit'),
]
