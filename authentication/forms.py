from django import forms
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from phonenumber_field.formfields import PhoneNumberField
import re

class CreateUserForm(UserCreationForm):
    phone_number = PhoneNumberField(widget=forms.TextInput(attrs={'placeholder': 'Phone Number...'}), required=True)
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password...'}),
        label='Password'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password...'}),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if not self.validate_password(password):
            raise forms.ValidationError(
                "Password must be at least 8 characters long, contain at least one uppercase letter, one number, and one special character."
            )
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def validate_password(self, password):
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        return True

class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email...'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password...'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
                self.user = authenticate(username=user.username, password=password)
                if not self.user:
                    raise forms.ValidationError("Invalid login credentials")
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid login credentials")
        
        return cleaned_data
    
    def get_user(self):
        return self.user

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No user with this email exists.")
        return email

class SetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password...'}),
        label='New Password'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password...'}),
        label='Confirm New Password'
    )

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', None)
        super().__init__(*args, **kwargs)

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if not self.validate_password(password):
            raise forms.ValidationError(
                "Password must be at least 8 characters long, contain at least one uppercase letter, one number, and one special character."
            )
        return password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def clean(self):
        cleaned_data = super().clean()
        if self.token and self.token.is_expired():
            raise forms.ValidationError("This link has expired.")
        return cleaned_data

    def validate_password(self, password):
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        return True

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'placeholder': 'Enter OTP...'}),
        label='OTP'
    )
