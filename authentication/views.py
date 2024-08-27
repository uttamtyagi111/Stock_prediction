from functools import cache
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.shortcuts import render,get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CreateUserForm, EmailLoginForm, OTPVerificationForm, PasswordResetRequestForm, SetNewPasswordForm
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import random
from email_sender.models import Sender, SMTPServer, EmailTemplate
from email_sender.views import SenderForm,SMTPServerForm,EmailTemplateForm
from django.shortcuts import render
from django.core.cache import cache
from .utils import generate_otp, send_otp_email 
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from .forms import EmailLoginForm
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication




class ProtectedView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "This is a protected view."})




import logging

logger = logging.getLogger(__name__)

import json
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def loginPage(request):
    data = json.loads(request.body)
    form = EmailLoginForm(data)

    logger.debug(f"Request Body: {data}")
    logger.debug(f"Form Valid: {form.is_valid()}")
    logger.debug(f"Form Errors: {form.errors}")

    if form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(request, email=email, password=password)

        if user and user.is_active:
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'redirect': 'home',
                'message': 'Login successful'
            })
        else:
            return JsonResponse({
                'message': 'Email or password is incorrect or account is inactive.'
            }, status=400)

    return JsonResponse({
        'form_valid': form.is_valid(),
        'errors': form.errors
    }, status=400)



from rest_framework_simplejwt.views import TokenRefreshView
class CustomTokenRefreshView(TokenRefreshView):
    pass

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView




    # if request.user.is_authenticated:
    #     return JsonResponse({'message': 'Login successful','status':200}, status=200)
    
    # if request.method == 'POST':
    #     form = EmailLoginForm(request.POST)
    #     if form.is_valid():
    #         user = form.get_user()
    #         if user and user.is_active:
    #             login(request, user)
    #             return JsonResponse({ 'message': 'Login successful'})
    #         else:
    #             return JsonResponse({'errors': {'non_field_errors': ['Email or password is incorrect or account is inactive.']}}, status=400)
    #     else:
    #         return JsonResponse({'errors': form.errors}, status=400)
    
    # return JsonResponse({'error': 'Invalid request method. Use POST for login.'}, status=405)

@login_required
def home(request):
    return render(request, 'home.html', {'current_year': 2024})

# Function to generate a 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))


# def registerPage(request):
#     if request.user.is_authenticated:
#         return redirect('home')

#     if request.method == 'POST':
#         form = CreateUserForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_active = False  # Set user as inactive until OTP verification
#             user.save()
            
#             otp = generate_otp()
#             # Store OTP in cache with a 10-minute timeout
#             cache.set(f'otp_{user.pk}', otp, timeout=600)
#             send_otp_email(user, otp)

#             messages.success(request, 'Account created. Please enter the OTP sent to your email.')
#             return redirect('verify_otp', user_id=user.pk)
#     else:
#         form = CreateUserForm()

#     return render(request, 'authentication/register.html', {'form': form})

def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Set user as inactive until OTP verification
            user.save()
            
            otp = generate_otp()
            cache.set(f'otp_{user.pk}', otp, timeout=600)
            send_otp_email(user, otp)

            messages.success(request, 'Account created. Please enter the OTP sent to your email.')
            return redirect('verify_otp', user_id=user.pk)
    else:
        form = CreateUserForm()

    return JsonResponse({'form': form.as_p()})


# def verify_otp(request, user_id):
#     if request.method == 'POST':
#         otp_input = request.POST.get('otp')
#         otp = cache.get(f'otp_{user_id}')

#         if otp and otp == otp_input:
#             user = User.objects.get(pk=user_id)
#             user.is_active = True
#             user.save()
#             messages.success(request, 'Your email has been verified. You can now log in.')
#             return redirect('login')
#         else:
#             messages.error(request, 'Invalid OTP. Please try again.')

#     return render(request, 'authentication/verify_otp.html', {'user_id': user_id})

def verify_otp(request, user_id):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        otp = cache.get(f'otp_{user_id}')

        if otp and otp == otp_input:
            user = User.objects.get(pk=user_id)
            user.is_active = True
            user.save()
            messages.success(request, 'Your email has been verified. You can now log in.')
            return JsonResponse({'redirect': 'login'})
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return JsonResponse({'user_id': user_id})



from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        # Extract the refresh token from the request data
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return JsonResponse({'message': 'Refresh token is required.'}, status=400)
        
        # Verify the token
        token = RefreshToken(refresh_token)

        # Blacklist the token to invalidate it
        token.blacklist()

        return JsonResponse({'message': 'Logout successful'}, status=200)
    except InvalidToken:
        return JsonResponse({'message': 'Invalid token'}, status=400)
# @login_required(login_url='login')
# def home(request):
#     return render(request, 'authentication/home.html')

@login_required(login_url='login')
def home(request):
    if request.method == 'GET':
        return JsonResponse({'message': 'Welcome to the home page!'})
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def user_list(request):
    users = User.objects.all()
    return render(request, 'authentication/user_list.html', {'users': users})

# def request_password_reset(request):
#     if request.method == 'POST':
#         form = PasswordResetRequestForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             user = User.objects.filter(email=email).first()
#             if user:
#                 uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
#                 token = default_token_generator.make_token(user)
#                 reset_link = request.build_absolute_uri(
#                     reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
#                 )
#                 send_mail(
#                     'Password Reset Request',
#                     f'Click the link to reset your password: {reset_link}',
#                     settings.DEFAULT_FROM_EMAIL,
#                     [email],
#                     fail_silently=False,
#                 )
#                 messages.success(request, 'Password reset email sent.')
#             else:
#                 messages.error(request, 'No user found with this email address.')
#             return redirect('login')
#     else:
#         form = PasswordResetRequestForm()
#     return render(request, 'authentication/request_password_reset.html', {'form': form})
def request_password_reset(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
                )
                send_mail(
                    'Password Reset Request',
                    f'Click the link to reset your password: {reset_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'Password reset email sent.')
                return JsonResponse({'message': 'Password reset email sent.'})
            else:
                messages.error(request, 'No user found with this email address.')
                return JsonResponse({'errors': {'email': ['No user found with this email address.']}}, status=400)
    else:
        form = PasswordResetRequestForm()
    return JsonResponse({'form': form.as_p()})

# def reset_password(request, uidb64, token):
#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#         if not default_token_generator.check_token(user, token):
#             messages.error(request, 'Invalid reset link.')
#             return redirect('request_password_reset')
#     except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#         messages.error(request, 'Invalid reset link.')
#         return redirect('request_password_reset')

#     if request.method == 'POST':
#         form = SetNewPasswordForm(request.POST)
#         if form.is_valid():
#             new_password = form.cleaned_data['new_password1']
#             user.set_password(new_password)
#             user.save()
#             messages.success(request, 'Password has been reset successfully.')
#             return redirect('login')
#     else:
#         form = SetNewPasswordForm()
    
#     return render(request, 'authentication/reset_password.html', {'form': form})

def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if not default_token_generator.check_token(user, token):
            messages.error(request, 'Invalid reset link.')
            return JsonResponse({'redirect': 'request_password_reset'})
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid reset link.')
        return JsonResponse({'redirect': 'request_password_reset'})

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password has been reset successfully.')
            return JsonResponse({'redirect': 'login'})
    else:
        form = SetNewPasswordForm()
    
    return JsonResponse({'form': form.as_p()})




# def otp_verification(request):
#     if request.method == 'POST':
#         form = OTPVerificationForm(request.POST)
#         if form.is_valid():
#             otp = form.cleaned_data['otp']
#             try:
#                 user = User.objects.get(profile__otp=otp, profile__otp_expiry__gte=timezone.now())
#                 user.is_active = True
#                 user.profile.otp = ''  # Clear OTP after successful verification
#                 user.profile.save()
#                 user.save()
#                 login(request, user)
#                 messages.success(request, 'Your email has been verified. You are now logged in.')
#                 return redirect('home')
#             except User.DoesNotExist:
#                 messages.error(request, 'Invalid or expired OTP.')
#         return render(request, 'authentication/otp_verification.html', {'form': form})
    
#     else:
#         form = OTPVerificationForm()
#         return render(request, 'authentication/otp_verification.html', {'form': form})

def otp_verification(request):
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            try:
                user = User.objects.get(profile__otp=otp, profile__otp_expiry__gte=timezone.now())
                user.is_active = True
                user.profile.otp = ''  # Clear OTP after successful verification
                user.profile.save()
                user.save()
                login(request, user)
                messages.success(request, 'Your email has been verified. You are now logged in.')
                return JsonResponse({'redirect': 'home'})
            except User.DoesNotExist:
                messages.error(request, 'Invalid or expired OTP.')
                return JsonResponse({'errors': {'otp': ['Invalid or expired OTP.']}}, status=400)
    else:
        form = OTPVerificationForm()
    return JsonResponse({'form': form.as_p()})
