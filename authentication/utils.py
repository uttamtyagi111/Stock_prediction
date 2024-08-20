import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(user, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}.'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email
    send_mail(subject, message, from_email, [to_email])
