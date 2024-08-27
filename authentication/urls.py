from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import (
    # PasswordResetDoneView, 
    PasswordResetCompleteView
)
from . import views
from django.urls import path,include
# from .views import get_csrf_token
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,)

urlpatterns = [
    path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logout_view, name='logout'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-otp/<int:user_id>/',views.verify_otp, name='verify_otp'),
    path('reset_password/', views.request_password_reset, name='password_reset'),
    # path('csrf/', get_csrf_token, name='csrf_token'),
    # path('reset_password/done/', PasswordResetDoneView.as_view(
    #     template_name='registration/password_reset_done.html'
    # ), name='password_reset_done'),
    path('reset_password/<uidb64>/<token>/', views.reset_password, name='password_reset_confirm'),
    # path('reset_password/complete/', PasswordResetCompleteView.as_view(
    #     template_name='registration/password_reset_complete.html'
    # ), name='password_reset_complete'),
    path('home/', views.home, name="home"),
    path('users/', views.user_list, name='user_list'),
    # path('senders/',views.senders_list, name='senders-list'),
    # path('senders/<int:pk>/', views.sender_detail, name='sender-detail'),
    # path('smtp-servers/', views.smtp_servers_list, name='smtp-servers-list'),
    # path('email-templates/', views.email_templates_list, name='email-templates-list'),
]
