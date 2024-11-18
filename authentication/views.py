from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from .forms import OTPVerificationForm
from django.http import JsonResponse
from .forms import EmailLoginForm
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
from subscriptions.models import UserProfile, UserDevice
import random,logging,subprocess
from django.shortcuts import render
from .utils import generate_otp, send_otp_email 
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login as django_login,logout
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
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
    # @api_view(['GET'])
    # @permission_classes([AllowAny])
    # def system_info_view(request):
    #     info = get_system_info()
    #     return Response(info)

    # def get_system_info():
    #     try:
    #         command = "wmic csproduct get name, identifyingnumber"
    #         result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
    #         if result.returncode == 0:
    #             output_lines = result.stdout.strip().split("\n")

    #             output_lines = [line.strip() for line in output_lines if line.strip()]

    #             if len(output_lines) >= 2:
    #                 headers = output_lines[0].split() 
    #                 values = output_lines[1].split(maxsplit=1) 

    #                 system_info = {
    #                     "IdentifyingNumber": values[0],
    #                     "Name": values[1] if len(values) > 1 else None
    #                 }
    #             else:
    #                 system_info = {"error": "Unexpected command output"}

    #             return system_info
    #         else:
    #             return {"error": result.stderr}
    #     except Exception as e:
    #         return {"error": str(e)}



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_logged_in_devices(request):
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        return Response({"error": "User is not authenticated"}, status=401)
    

    user = request.user


    user_devices = UserDevice.objects.filter(user=user)


    device_data = []
    for device in user_devices:
        device_data.append({
            'device_name': device.device_name,
            'system_info': device.system_info,
        })
    
    # Return the list of logged-in devices
    return Response({
        'logged_in_devices': device_data,
        'message': 'Logged-in devices fetched successfully'
    })






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
    
    plan_name = getattr(user_profile.plan_name, 'name', None)  # Assuming `plan` is a ForeignKey in UserProfile
    if not plan_name or plan_name.lower() == "basic":
        device_limit = 1
    elif plan_name.lower() == "premium":
        device_limit = 3
    else:
        return Response({'message': 'Invalid plan name.'}, status=400)

    # Get system_info from request data (frontend should send this)
    system_info = request.data.get('system_info')
    if not system_info:
        return Response({'message': 'System info is required.'}, status=400)

    # system_info = json.loads(system_info)

    # Check if the user has exceeded the device limit
    if not check_device_limit(user_profile, system_info,device_limit):
        return Response({
            'message': f'Device limit exceeded. You can only log in on {device_limit} device(s). Please log out from other devices to log in.',
            'logged_in_devices': logged_in_devices(user_profile)
        }, status=200)

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    # Save the device info and token in the database
    existing_devices = UserDevice.objects.filter(user=user_profile.user)
    device_count = existing_devices.count()
    
    # Generate a unique device name, e.g., "device1", "device2", "device3"
    device_name = f"device{device_count + 1}"
    user_device = UserDevice.objects.create(
        user=user,
        device_name=device_name,
        system_info=system_info,  # Save system info for future reference
        token = refresh_token  # Save token for future logout functionality
    )

    return Response({
        'user_id': user.id,
        'access': access_token,
        'refresh': refresh_token,
        'system_info': system_info,
        "device_id": user_device.id,
        'redirect': 'home',
        'message': 'Login successful'
    })




class LogoutDeviceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        device_id = request.data.get('device_id')
        system_info = request.data.get('system_info')

        if not device_id or not system_info:
            return Response({'error': 'Device ID and system info are required'}, status=400)

        try:

            device = get_object_or_404(UserDevice, id=device_id)
            user = device.user
            old_refresh_token = device.token

            if not old_refresh_token:
                return Response({'error': 'No refresh token found for this device'}, status=400)

            try:
                old_token = RefreshToken(old_refresh_token)
                old_token.blacklist()
            except Exception as e:
                return Response({'error': f'Failed to blacklist old token: {str(e)}'}, status=400)

            new_refresh_token = RefreshToken.for_user(user)
            new_access_token = str(new_refresh_token.access_token)

            device.token = str(new_refresh_token) 
            device.system_info = system_info  
            device.save()

            return Response({
                'success': f'Device {device.device_name} updated successfully.',
                'device_id': device_id,
                'access_token': new_access_token,
                'refresh_token': str(new_refresh_token),
                'system_info': device.system_info
            }, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=400)





# @api_view(['POST'])
# @permission_classes([AllowAny])  # Adjust permissions if you need authentication
# def logout_device(request):
#     email = request.data.get('email')
#     password = request.data.get('password') 
#     device_name = request.data.get('device_name')
#     device_id = request.data.get('device_id') 
#     system_info = request.data.get('system_info') 
    
#     # Check if all required data is present
#     if email and password and device_name and device_id:
#         # Authenticate the user with email and password
#         user = authenticate(request, email=email, password=password)
        
#         if user is None:
#             return Response({'message': 'Invalid credentials.'}, status=400)
        
#         try:
#             # Check if the user's profile and device exist
#             user_profile = UserProfile.objects.get(user=user)
#             user_device = UserDevice.objects.get(user=user_profile.user, id=user_device.id)
            
#             # Delete the existing device entry and blacklist the token
#             refresh_token = user_device.token
#             token = RefreshToken(refresh_token)
#             user_device.delete()
#             token.blacklist()

#             # Create new tokens for the user
#             refresh = RefreshToken.for_user(user)
#             access_token = str(refresh.access_token)
#             refresh_token = str(refresh)

#             # Save the device info and token in the database
#             UserDevice.objects.create(
#                 user=user,
#                 device_name=device_name,
#                 device_id=device_id,
#                 system_info=system_info,
#                 token=refresh_token  # Store the refresh token
#             )

#             return Response({
#                 'user_id': user.id,
#                 'access': access_token,
#                 'refresh': refresh_token,
#                 'system_info': system_info,
#                 'redirect': 'home',
#                 'message': 'Login successful'
#             }, status=200)

#         except UserProfile.DoesNotExist:
#             return Response({'message': 'User profile not found.'}, status=400)
#         except UserDevice.DoesNotExist:
#             return Response({'message': 'Device not found.'}, status=400)

#     # If any required field is missing
#     return Response({'message': 'Invalid request data.'}, status=400)
    


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])  # Ensure the user is authenticated for logout
# def logout_view(request):
#     device_name = request.data.get('device_name')
#     device_id = request.data.get('device_id')  # This will be the 'id' field in UserDevice model

#     if not device_name:
#         return Response({'message': 'Device name is required.'}, status=400)
#     if not device_id:
#         return Response({'message': 'Device ID is required.'}, status=400)

#     try:
#         # Find the UserDevice instance by user, device name, and device ID (using 'id' field)
#         user_device = UserDevice.objects.get(user=request.user, device_name=device_name, id=device_id)
#     except UserDevice.DoesNotExist:
#         return Response({'message': 'Device not found.'}, status=400)

#     # Blacklist the refresh token associated with this device to ensure logout
#     refresh_token = user_device.token
#     token = RefreshToken(refresh_token)
#     token.blacklist()

#     # Delete the device record from the database
#     user_device.delete()

#     return Response({'message': 'Device logged out successfully.'})





def check_device_limit(user_profile, system_info,device_limit):
    """
    Checks if the user has exceeded the allowed device limit.
    """

    if user_profile.plan_name == None:
        existing_devices = UserDevice.objects.filter(user=user_profile.user)
        if existing_devices.count() >= 1:
            return False  
    elif user_profile.plan_name == 'Basic':
        existing_devices = UserDevice.objects.filter(user=user_profile.user)
        if existing_devices.count() >= 1:
            return False  
    elif user_profile.plan_name == 'Premium':
        existing_devices = UserDevice.objects.filter(user=user_profile.user)
        if existing_devices.count() >= 3:
            return False  
    return True



def logged_in_devices(user_profile):
    """
    Returns the list of devices the user is logged in on.
    """
    devices = UserDevice.objects.filter(user=user_profile.user)
    devices_info = [{"device_name": device.device_name,"device_id":device.id, "system_info": device.system_info} for device in devices]
    return devices_info





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:

        refresh_token = request.data.get('refresh')
        device_id = request.data.get('device_id')

        if not refresh_token:
            return Response({'message': 'Refresh token is required.'}, status=400)
        if not device_id:
            return Response({'message': 'Device ID is required.'}, status=400)


        token = RefreshToken(refresh_token)
        token.blacklist()

        device = get_object_or_404(UserDevice, id=device_id)

        if device.user != request.user:
            return Response({'message': 'You do not have permission to delete this device.'}, status=403)

        device.delete()

        return Response({'message': 'Logout successful and device removed.'}, status=200)

    except InvalidToken:
        return Response({'message': 'Invalid token'}, status=400)
    except Exception as e:
        return Response({'message': f'Error: {str(e)}'}, status=500)
    


@api_view(['POST'])
@permission_classes([AllowAny]) 
def check_blacklisted_token(request):
    """
    This API checks if a given refresh token is blacklisted.
    """
    refresh_token = request.data.get('refresh_token') 
    if not refresh_token:
        return Response({'message': 'Refresh token is required.'}, status=400)
    
    try:
        token = RefreshToken(refresh_token)

        try:
            BlacklistedToken.objects.get(token__jti=token['jti'])
            return Response({"message": "The token is blacklisted."}, status=200)
        except ObjectDoesNotExist:
            return Response({"message": "The token is not blacklisted."}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


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
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                if created:
                    user.is_active = True
                    user.set_password(user_data['password'])  
                    user.save()
                    
                cache.delete(f'otp_{request.data.get("email")}')
                cache.delete(f'register_data_{request.data.get("email")}')

                return Response({'message': 'Email verified and account created successfully.'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'User data not found. Please register again.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'Invalid OTP. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'form_valid': form.is_valid(), 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)





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




