from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .forms import OTPVerificationForm
from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import InvalidToken
from .forms import EmailLoginForm
from subscriptions.models import UserProfile
from functools import cache
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib import messages
from .forms import CreateUserForm, EmailLoginForm, PasswordResetRequestForm, SetNewPasswordForm
from .forms import OTPVerificationForm
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from .forms import PasswordResetRequestForm
from .utils import send_password_reset_email  
import random,logging,subprocess
from django.shortcuts import render
from django.core.cache import cache
from .utils import generate_otp, send_otp_email 
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login as django_login,logout
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.views import TokenRefreshView


class ProtectedView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "This is a protected view."})

class CustomTokenRefreshView(TokenRefreshView):
    pass

logger = logging.getLogger(__name__)
# from .utils import get_system_info
@api_view(['GET'])
@permission_classes([AllowAny])
def system_info_view(request):
    info = get_system_info()
    return Response(info)

def get_system_info():
    try:
        command = "wmic csproduct get name, identifyingnumber"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            output_lines = result.stdout.strip().split("\n")

            output_lines = [line.strip() for line in output_lines if line.strip()]

            if len(output_lines) >= 2:
                headers = output_lines[0].split() 
                values = output_lines[1].split(maxsplit=1) 

                system_info = {
                    "IdentifyingNumber": values[0],
                    "Name": values[1] if len(values) > 1 else None
                }
            else:
                system_info = {"error": "Unexpected command output"}

            return system_info
        else:
            return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}


@api_view(['POST'])
@permission_classes([AllowAny])
def loginPage(request):
    form = EmailLoginForm(data=request.data)

    if not form.is_valid():
        return Response({
            'form_valid': form.is_valid(),
            'errors': form.errors
        }, status=400)

    email = form.cleaned_data['email']
    password = form.cleaned_data['password']
    user = authenticate(request, email=email, password=password)

    if not user:
        return Response({'message': 'Email or password is incorrect.'}, status=400)

    if not user.is_active:
        return Response({'message': 'Account is inactive.'}, status=400)

    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return Response({'message': 'User profile not found.'}, status=400)

    # Check and manage device limits
    system_info = get_system_info()
    if not check_device_limit(user_profile, system_info):
        return Response({
            'message': 'Device limit exceeded. You can only log in on 3 devices.',
            'logged_in_devices': user_profile.system_info
        }, status=400)

    # Generate tokens without using django_login
    refresh = RefreshToken.for_user(user)
    user_profile.refresh_token = str(refresh)  # Save new refresh token
    user_profile.system_info = system_info
    user_profile.save()

    return Response({
        'user_id': user.id,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'system_info': system_info,
        'redirect': 'home',
        'message': 'Login successful'
    })


def check_device_limit(user_profile, system_info):
    """
    Checks if the user has exceeded the allowed device limit.
    """
    if user_profile.plan_name == 'basic':
        # Basic Plan: Only 1 device allowed
        if user_profile.refresh_token:  # Clear any existing token
            user_profile.refresh_token = None
            user_profile.save()
        return True

    elif user_profile.plan_name == 'premium':
        # Premium Plan: Up to 3 devices allowed
        existing_tokens_count = UserProfile.objects.filter(
            refresh_token__isnull=False, user=user_profile.user).count()
        if existing_tokens_count >= 3:
            return False  # Exceeds device limit
    return True

# from django.contrib.auth import authenticate, login as django_login, logout
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from rest_framework_simplejwt.tokens import RefreshToken
# from subscriptions.models import UserProfile
# from .forms import EmailLoginForm

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def loginPage(request):
#     logout(request)  # Log out any existing session
#     form = EmailLoginForm(data=request.data)

#     if not form.is_valid():
#         return Response({
#             'form_valid': form.is_valid(),
#             'errors': form.errors
#         }, status=400)

#     # Extract credentials
#     email = form.cleaned_data['email']
#     password = form.cleaned_data['password']
#     user = authenticate(request, email=email, password=password)

#     if not user:
#         return Response({'message': 'Email or password is incorrect.'}, status=400)

#     if not user.is_active:
#         return Response({'message': 'Account is inactive.'}, status=400)

#     try:
#         user_profile = UserProfile.objects.get(user=user)
#     except UserProfile.DoesNotExist:
#         return Response({'message': 'User profile not found.'}, status=400)

#     # Check and manage device limits
#     system_info = get_system_info()
#     if not check_device_limit(user_profile, system_info):
#         return Response({
#             'message': 'Device limit exceeded. You can only log in on 3 devices.',
#             'logged_in_devices': user_profile.system_info
#         }, status=400)

#     # Log in user and generate tokens
#     django_login(request, user)
#     refresh = RefreshToken.for_user(user)
#     user_profile.refresh_token = str(refresh)  # Save new refresh token
#     user_profile.system_info = system_info
#     user_profile.save()

#     return Response({
#         'user_id': user.id,
#         'access': str(refresh.access_token),
#         'refresh': str(refresh),
#         'system_info': system_info,
#         'redirect': 'home',
#         'message': 'Login successful'
#     })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({'message': 'Refresh token is required.'}, status=400)
        
        token = RefreshToken(refresh_token)
        token.blacklist()  # Blacklist the token on logout

        return Response({'message': 'Logout successful'}, status=200)
    except InvalidToken:
        return Response({'message': 'Invalid token'}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def home(request):
    user = request.user
    data = {
        'message': 'Welcome to the home page!',
        'current_year': 2024,
        'user': {
            'username': user.username,
            'email': user.email
        }
    }
    return JsonResponse(data)

def generate_otp():
    return str(random.randint(100000, 999999))

@api_view(['POST'])
@permission_classes([AllowAny])
def registerPage(request):
    if request.user.is_authenticated:
        return Response({'redirect': 'home'}, status=status.HTTP_302_FOUND)

    form = CreateUserForm(data=request.data)

    if form.is_valid():
        email = form.cleaned_data.get('email')
        username = form.cleaned_data.get('username')

        if User.objects.filter(email=email).exists():
            return Response({
                'message': 'Email is already registered. Please log in or use a different email.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        otp = generate_otp()
        cache.set(f'otp_{email}', otp, timeout=600) 
        send_otp_email(email, otp,username) 

        user_data = {
            'username': form.cleaned_data.get('username'),
            'email': email,
            'password': form.cleaned_data.get('password'),
        }
        cache.set(f'register_data_{email}', user_data, timeout=600)

        return Response({
            'message': 'OTP sent to your email. Please verify to complete registration.',
            'email': email,
        }, status=status.HTTP_200_OK)
    
    return Response({
        'form_valid': form.is_valid(),
        'errors': form.errors
    }, status=status.HTTP_400_BAD_REQUEST)

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    form = OTPVerificationForm(data=request.data)
    
    if form.is_valid():
        otp_input = form.cleaned_data.get('otp')
        otp_stored = cache.get(f'otp_{request.data.get("email")}')
        
        if otp_input == otp_stored:
            user_data = cache.get(f'register_data_{request.data.get("email")}')
            
            if user_data:
                # Unpack the result from get_or_create
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )

                # If the user was just created, set it as active and save
                if created:
                    user.is_active = True
                    user.set_password(user_data['password'])  # Hash the password before saving
                    user.save()

                   
                cache.delete(f'otp_{request.data.get("email")}')
                cache.delete(f'register_data_{request.data.get("email")}')

                return Response({'message': 'Email verified and account created successfully.'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'User data not found. Please register again.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'Invalid OTP. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'form_valid': form.is_valid(), 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)



# from functools import cache
# from django.contrib.auth.models import User
# from django.contrib.auth.tokens import default_token_generator
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
# from django.utils.encoding import force_bytes, force_str
# from django.shortcuts import render
# from django.contrib.auth import authenticate
# from django.contrib import messages
# from .forms import CreateUserForm, EmailLoginForm, PasswordResetRequestForm, SetNewPasswordForm
# from .forms import OTPVerificationForm
# from django.core.mail import send_mail
# from django.conf import settings
# from rest_framework.decorators import api_view, permission_classes
# from .forms import PasswordResetRequestForm
# from .utils import send_password_reset_email  
# import random,logging
# from django.shortcuts import render
# from django.core.cache import cache
# from .utils import generate_otp, send_otp_email 
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from rest_framework import status
# from django.http import JsonResponse
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework.views import APIView
# from django.contrib.auth import authenticate, login as django_login,logout
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework_simplejwt.exceptions import InvalidToken
# from rest_framework_simplejwt.views import TokenRefreshView


# class ProtectedView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         return Response({"message": "This is a protected view."})

# class CustomTokenRefreshView(TokenRefreshView):
#     pass

# logger = logging.getLogger(__name__)

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def loginPage(request):
#     logout(request)
#     # print("Request received:", request.data) 
    
#     form = EmailLoginForm(request.data or None)
    
#     if form.is_valid():
#         email = form.cleaned_data['email']
#         password = form.cleaned_data['password']
#         # print(f"Email: {email}, Password: {password}") 
#         print(f"Attempting login with email: {email}") 
        
#         user = authenticate(request, email=email, password=password)
#         # print(f"User: {user}") 
#         print(f"Authenticated user: {user}")
        
#         if user:
#             if user.is_active:
#                 django_login(request, user)
#                 refresh = RefreshToken.for_user(user)
#                 print(f"Logged-in user: {user.username} (ID: {user.id})")
#                 return JsonResponse({
#                     'user_id': user.id,
#                     'access': str(refresh.access_token),
#                     'refresh': str(refresh),
#                     'redirect': 'home',
#                     'message': 'Login successful'
#                 })
#             else:
#                 return JsonResponse({'message': 'Account is inactive.'}, status=400)
#         else:
#             return JsonResponse({
#                 'message': 'Email or password is incorrect.'
#             }, status=400)
    
#     return JsonResponse({
#         'form_valid': form.is_valid(),
#         'errors': form.errors
#     }, status=400)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def logout_view(request):
#     try:
#         refresh_token = request.data.get('refresh')

#         if not refresh_token:
#             return JsonResponse({'message': 'Refresh token is required.'}, status=400)
        
#         token = RefreshToken(refresh_token)

#         token.blacklist()

#         return JsonResponse({'message': 'Logout successful'}, status=200)
#     except InvalidToken:
#         return JsonResponse({'message': 'Invalid token'}, status=400)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def home(request):
#     user = request.user
#     data = {
#         'message': 'Welcome to the home page!',
#         'current_year': 2024,
#         'user': {
#             'username': user.username,
#             'email': user.email
#         }
#     }
#     return JsonResponse(data)

# def generate_otp():
#     return str(random.randint(100000, 999999))

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def registerPage(request):
#     if request.user.is_authenticated:
#         return Response({'redirect': 'home'}, status=status.HTTP_302_FOUND)

#     form = CreateUserForm(data=request.data)

#     if form.is_valid():
#         email = form.cleaned_data.get('email')
#         username = form.cleaned_data.get('username')

#         if User.objects.filter(email=email).exists():
#             return Response({
#                 'message': 'Email is already registered. Please log in or use a different email.'
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         otp = generate_otp()
#         cache.set(f'otp_{email}', otp, timeout=600) 
#         send_otp_email(email, otp,username) 

#         user_data = {
#             'username': form.cleaned_data.get('username'),
#             'email': email,
#             'password': form.cleaned_data.get('password'),
#         }
#         cache.set(f'register_data_{email}', user_data, timeout=600)

#         return Response({
#             'message': 'OTP sent to your email. Please verify to complete registration.',
#             'email': email,
#         }, status=status.HTTP_200_OK)
    
#     return Response({
#         'form_valid': form.is_valid(),
#         'errors': form.errors
#     }, status=status.HTTP_400_BAD_REQUEST)



# @api_view(['POST'])
# @permission_classes([AllowAny])
# def verify_otp(request):
#     form = OTPVerificationForm(data=request.data)
    
#     if form.is_valid():
#         otp_input = form.cleaned_data.get('otp')

#         otp_stored = cache.get(f'otp_{request.data.get("email")}')

#         if otp_input == otp_stored:
#             user_data = cache.get(f'register_data_{request.data.get("email")}')
#             if user_data:
#                 user = User.objects.create_user(
#                     username=user_data['username'],
#                     email=user_data['email'],
#                     password=user_data['password']
#                 )
#                 user.is_active = True
#                 user.save()

#                 cache.delete(f'otp_{request.data.get("email")}')
#                 cache.delete(f'register_data_{request.data.get("email")}')

#                 return Response({'message': 'Email verified and account created successfully.'}, status=status.HTTP_201_CREATED)
#             else:
#                 return Response({'message': 'User data not found. Please register again.'}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({'message': 'Invalid OTP. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
    
#     return Response({'form_valid': form.is_valid(), 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)




def user_list(request):
    users = User.objects.all()
    return render(request, 'authentication/user_list.html', {'users': users})


import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL')


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    form = PasswordResetRequestForm(data=request.data)

    if form.is_valid():
        email = form.cleaned_data['email']
        user = User.objects.filter(email=email).first()

        if user:
            # Use the utility function to send the reset email
            send_password_reset_email(user, settings.BASE_URL)
            return Response({'message': 'Password reset email sent.'}, status=status.HTTP_200_OK)
        else:
            return Response({'errors': {'email': ['No user found with this email address.']}}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'form_valid': form.is_valid(), 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if not default_token_generator.check_token(user, token):
            messages.error(request, 'Invalid or expired reset link.')
            return Response({'redirect': 'request_password_reset'}, status=status.HTTP_400_BAD_REQUEST)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid or expired reset link.')
        return Response({'redirect': 'request_password_reset'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password has been reset successfully.')
            return Response({'redirect': 'login'}, status=status.HTTP_200_OK)
    else:
        form = SetNewPasswordForm()

    return Response({'form': form.as_p()}, status=status.HTTP_200_OK)




