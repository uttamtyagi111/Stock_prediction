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
import random,logging
from django.shortcuts import render
from django.core.cache import cache
from .utils import generate_otp, send_otp_email 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.views import APIView
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

@api_view(['POST'])
@permission_classes([AllowAny])
def loginPage(request):
    print("Request received:", request.data) 
    
    form = EmailLoginForm(request.data or None)
    
    if form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        print(f"Email: {email}, Password: {password}")  
        
        user = authenticate(request, email=email, password=password)
        print(f"User: {user}") 
        
        if user:
            if user.is_active:
                refresh = RefreshToken.for_user(user)
                return JsonResponse({
                    'user_id': user.id,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'redirect': 'home',
                    'message': 'Login successful'
                })
            else:
                return JsonResponse({'message': 'Account is inactive.'}, status=400)
        else:
            return JsonResponse({
                'message': 'Email or password is incorrect.'
            }, status=400)
    
    return JsonResponse({
        'form_valid': form.is_valid(),
        'errors': form.errors
    }, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return JsonResponse({'message': 'Refresh token is required.'}, status=400)
        
        token = RefreshToken(refresh_token)

        token.blacklist()

        return JsonResponse({'message': 'Logout successful'}, status=200)
    except InvalidToken:
        return JsonResponse({'message': 'Invalid token'}, status=400)


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
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                user.is_active = True
                user.save()

                cache.delete(f'otp_{request.data.get("email")}')
                cache.delete(f'register_data_{request.data.get("email")}')

                return Response({'message': 'Email verified and account created successfully.'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'User data not found. Please register again.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'Invalid OTP. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'form_valid': form.is_valid(), 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)




def user_list(request):
    users = User.objects.all()
    return render(request, 'authentication/user_list.html', {'users': users})

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    form = PasswordResetRequestForm(data=request.data)

    if form.is_valid():
        email = form.cleaned_data['email']
        user = User.objects.filter(email=email).first()

        if user:
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://localhost:3000/reset_password/{uidb64}/{token}/"
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
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



