import random
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp, username):
    """
    Send an OTP email to the specified address with HTML content.
    """
    subject = 'Your WishgeeksTechserve Registration OTP'
    from_email = settings.DEFAULT_FROM_EMAIL

    html_content = render_to_string('emails/otp_email.html', {'otp': otp, 'username': username})

    email_message = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=from_email,
        to=[email],
    )
    email_message.content_subtype = "html"  
    email_message.send()

