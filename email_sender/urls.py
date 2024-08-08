from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'templates', views.EmailTemplateViewSet)

urlpatterns = [
    path('send-emails/', views.SendEmailsView.as_view(), name='send-emails'),
    path('', include(router.urls)),  # Include the router URLs for templates
]
