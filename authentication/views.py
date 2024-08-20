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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import random
from email_sender.models import Sender, SMTPServer, EmailTemplate
from email_sender.views import SenderForm,SMTPServerForm,EmailTemplateForm

# def smtp_servers_list(request):
#     servers = SMTPServer.objects.all()
#     return render(request, 'smtp_servers_list.html', {'servers': servers})
@login_required
def email_templates_list(request):
    templates = EmailTemplate.objects.all()
    return render(request, 'email_templates_list.html', {'templates': templates})

@login_required
def senders_list(request):
    senders = Sender.objects.all()
    return render(request, 'senders_list.html', {'senders': senders})

@login_required
def sender_detail(request, pk):
    sender = get_object_or_404(Sender, pk=pk)
    return render(request, 'sender_detail.html', {'sender': sender})

@login_required
def sender_form(request, pk=None):
    if pk:
        sender = get_object_or_404(Sender, pk=pk)
    else:
        sender = None
    form = SenderForm(instance=sender)
    if request.method == 'POST':
        form = SenderForm(request.POST, instance=sender)
        if form.is_valid():
            form.save()
            return redirect('senders-list')
    return render(request, 'sender_form.html', {'form': form, 'form_title': 'Edit Sender' if pk else 'Create New Sender'})

@login_required
def smtp_servers_list(request):
    servers = SMTPServer.objects.all()
    return render(request, 'smtp_servers_list.html', {'servers': servers})

@login_required
def smtp_server_detail(request, pk):
    server = get_object_or_404(SMTPServer, pk=pk)
    return render(request, 'smtp_server_detail.html', {'server': server})

@login_required
def smtp_server_form(request, pk=None):
    if pk:
        server = get_object_or_404(SMTPServer, pk=pk)
    else:
        server = SMTPServer()
    form = SMTPServerForm(instance=server)
    if request.method == 'POST':
        form = SMTPServerForm(request.POST, instance=server)
        if form.is_valid():
            form.save()
            return redirect('smtp-servers-list')
    return render(request, 'smtp_server_form.html', {'form': form, 'form_title': 'Edit SMTP Server' if pk else 'Create New SMTP Server'})

@login_required
def email_template_form(request, pk=None):
    if pk:
        template = get_object_or_404(EmailTemplate, pk=pk)
    else:
        template = EmailTemplate()
    form = EmailTemplateForm(instance=template)
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            return redirect('email-templates-list')
    return render(request, 'email_template_form.html', {'form': form, 'form_title': 'Edit Email Template' if pk else 'Create New Email Template'})

def home(request):
    return render(request, 'home.html', {'current_year': 2024})

# Function to generate a 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Function to send OTP via email
def send_otp_email(user, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}'
    html_message = render_to_string('authentication/otp_email.html', {'otp': otp})
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
from .forms import CreateUserForm
from .utils import generate_otp, send_otp_email  # Ensure these functions are defined

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
            # Store OTP in cache with a 10-minute timeout
            cache.set(f'otp_{user.pk}', otp, timeout=600)
            send_otp_email(user, otp)

            messages.success(request, 'Account created. Please enter the OTP sent to your email.')
            return redirect('verify_otp', user_id=user.pk)
    else:
        form = CreateUserForm()

    return render(request, 'authentication/register.html', {'form': form})

def verify_otp(request, user_id):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        otp = cache.get(f'otp_{user_id}')

        if otp and otp == otp_input:
            user = User.objects.get(pk=user_id)
            user.is_active = True
            user.save()
            messages.success(request, 'Your email has been verified. You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'authentication/verify_otp.html', {'user_id': user_id})



def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = EmailLoginForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            user = form.get_user()
            if user and user.is_active:  # Check if the user is active
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Email or password is incorrect or account is inactive.')
        return render(request, 'authentication/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login') 

@login_required(login_url='login')
def home(request):
    return render(request, 'authentication/home.html')

def user_list(request):
    users = User.objects.all()
    return render(request, 'authentication/user_list.html', {'users': users})

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
            else:
                messages.error(request, 'No user found with this email address.')
            return redirect('login')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'authentication/request_password_reset.html', {'form': form})

def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if not default_token_generator.check_token(user, token):
            messages.error(request, 'Invalid reset link.')
            return redirect('request_password_reset')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid reset link.')
        return redirect('request_password_reset')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password has been reset successfully.')
            return redirect('login')
    else:
        form = SetNewPasswordForm()
    
    return render(request, 'authentication/reset_password.html', {'form': form})

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
                return redirect('home')
            except User.DoesNotExist:
                messages.error(request, 'Invalid or expired OTP.')
        return render(request, 'authentication/otp_verification.html', {'form': form})
    
    else:
        form = OTPVerificationForm()
        return render(request, 'authentication/otp_verification.html', {'form': form})

