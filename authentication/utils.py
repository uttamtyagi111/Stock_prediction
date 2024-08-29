import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    subject = 'Your OTP for Registration'
    message = f'Hello,\n\nYour OTP for registration is {otp}.\n\nPlease enter this OTP to complete your registration.\n\nThank you!'
    from_email = settings.DEFAULT_FROM_EMAIL

    # Send the email directly using the provided email address
    send_mail(subject, message, from_email, [email])

