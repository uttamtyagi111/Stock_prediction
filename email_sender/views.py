from django.core.mail import EmailMessage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.template import Template, Context
import csv
from io import StringIO
from .serializers import EmailSendSerializer
from .models import EmailTemplate
import time
from datetime import datetime

class SendEmailsView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = EmailSendSerializer(data=request.data)
        if serializer.is_valid():
            from_email = serializer.validated_data['from_email']
            display_name = serializer.validated_data['display_name']
            your_name = serializer.validated_data['your_name']
            your_company = serializer.validated_data['your_company']
            your_email = serializer.validated_data['your_email']
            contact_info = serializer.validated_data['contact_info']
            website_url = serializer.validated_data['website_url']
            email_list_file = request.FILES.get('email_list')
            template_id = request.data.get('template_id')  # Get the template ID

            if not email_list_file or not template_id:
                return Response({'error': 'No file or template ID was submitted.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Fetch the template by ID
                template = EmailTemplate.objects.get(id=template_id)
            except EmailTemplate.DoesNotExist:
                return Response({'error': 'Template not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Read the email list CSV
            email_list = []
            csv_file = email_list_file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(csv_file))
            for row in csv_reader:
                email_list.append(row)

            total_emails = len(email_list)
            try:
                for i, recipient in enumerate(email_list):
                    recipient_email = recipient.get('Email')
                    recipient_firstName = recipient.get('firstName')
                    recipient_lastName = recipient.get('lastName')
                    recipient_company = recipient.get('company')

                    # Render the HTML content with context
                    context = {
                        'recipient_firstName': recipient_firstName,
                        'recipient_lastName': recipient_lastName,
                        'recipient_company': recipient_company,
                        'contact_info': contact_info,
                        'website_url': website_url,
                        'your_name': your_name,
                        'your_company': your_company,
                        'your_email': your_email,
                    }
                    # Render the template from the body field in EmailTemplate
                    template_instance = Template(template.body)  # Load the template from the database
                    html_content = template_instance.render(Context(context))  # Render the template with context

                    email = EmailMessage(
                        subject=template.subject,  # Use the subject from the template
                        body=html_content,
                        from_email=f'{display_name} <{from_email}>',
                        to=[recipient_email]
                    )
                    email.content_subtype = 'html'  # Specify the content type as HTML

                    try:
                        email.send()
                        status_message = f'Successfully sent to {recipient_email}'
                    except Exception as e:
                        status_message = f'Failed to send to {recipient_email}: {str(e)}'

                    # Log the status, timestamp, and progress
                    timestamp = datetime.now().isoformat()
                    print(f'Timestamp: {timestamp} | Email: {recipient_email} | Status: {status_message}')
                    print(f'Progress: {i + 1}/{total_emails} emails sent')

                    time.sleep(15)  # Delay between sending emails

                return Response({'status': 'Emails sent successfully!'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': f'Failed to render template: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import viewsets
from .models import EmailTemplate
from .serializers import EmailTemplateSerializer

class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
