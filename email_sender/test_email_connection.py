import smtplib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get email credentials from environment variables
email_user = os.getenv('EMAIL_HOST_USER')
email_password = os.getenv('EMAIL_HOST_PASSWORD')

try:
    # Connect to the SMTP server
    server = smtplib.SMTP('mail.wishgeekstechserve.com', 587)
    server.starttls()  # Start TLS encryption
    server.login(email_user, email_password)  # Login to the email account

    # Send a test email
    from_address = email_user
    to_address = 'uttam@wishgeekstechserve.com'  # Replace with the recipient's email address
    subject = 'Test Email'
    body = 'This is a test email to check SMTP connection.'

    message = f'Subject: {subject}\n\n{body}'
    server.sendmail(from_address, to_address, message)

    print('Email sent successfully!')

except Exception as e:
    print(f'Failed to send email: {e}')

finally:
    server.quit()
import os
print(os.getenv('EMAIL_HOST_USER'))
print(os.getenv('EMAIL_HOST_PASSWORD'))