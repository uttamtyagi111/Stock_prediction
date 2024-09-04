import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    subject = 'Your WishgeeksTechserve register OTP:'
    # message = f'Hello,\n\nYour OTP for registration is {otp}.\n\nPlease enter this OTP to complete your registration.\n\nThank you!'
    from_email = settings.DEFAULT_FROM_EMAIL
    html_content = render_to_string('emails/otp_email.html', {'otp': otp})

    # Create and send the email
    EmailMessage(
        subject=subject,
        body=html_content,
        from_email=from_email,
        to=[email],
        headers={'Content-Type': 'text/html'}
    ).send()

    # Send the email directly using the provided email address
    # send_mail(subject, message, from_email, [email])

