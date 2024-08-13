from datetime import datetime
from django.core.mail import EmailMessage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.template import Template, Context
import csv,time
from io import StringIO
from .serializers import EmailSendSerializer, EmailTemplateSerializer
from .models import EmailTemplate, Sender, SMTPServer
from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404, redirect
from .models import Sender,SMTPServer
from .forms import SenderForm,SMTPServerForm

def senders_list(request):
    senders = Sender.objects.all()
    return render(request, 'senders_list.html', {'senders': senders})

def sender_detail(request, pk):
    sender = get_object_or_404(Sender, pk=pk)
    return render(request, 'sender_detail.html', {'sender': sender})

def sender_form(request, pk=None):
    if pk:
        sender = get_object_or_404(Sender, pk=pk)
        form = SenderForm(instance=sender)
        form_title = 'Edit Sender'
    else:
        sender = None
        form = SenderForm()
        form_title = 'Create New Sender'
        
    if request.method == 'POST':
        form = SenderForm(request.POST, instance=sender)
        if form.is_valid():
            form.save()
            return redirect('senders-list')
    
    return render(request, 'sender_form.html', {'form': form, 'form_title': form_title})

def smtp_servers_list(request):
    servers = SMTPServer.objects.all()
    return render(request, 'smtp_servers_list.html', {'servers': servers})

def smtp_server_detail(request, pk):
    server = get_object_or_404(SMTPServer, pk=pk)
    return render(request, 'smtp_server_detail.html', {'server': server})

def smtp_server_form(request, pk=None):
    if pk:
        server = get_object_or_404(SMTPServer, pk=pk)
    else:
        server = SMTPServer()
    
    if request.method == 'POST':
        form = SMTPServerForm(request.POST, instance=server)
        if form.is_valid():
            form.save()
            return redirect('smtp-servers-list')
    else:
        form = SMTPServerForm(instance=server)
    
    return render(request, 'smtp_server_form.html', {'form': form})


class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    
from rest_framework import serializers

class SenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sender
        fields = '__all__'

class SMTPServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMTPServer
        fields = '__all__'

class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = '__all__'
        
class SenderViewSet(viewsets.ModelViewSet):
    queryset = Sender.objects.all()
    serializer_class = SenderSerializer


class SendEmailsView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = EmailSendSerializer(data=request.data)
        if serializer.is_valid():
            sender_id = serializer.validated_data['sender_id']
            smtp_server_id = serializer.validated_data['smtp_server_id']
            from_email = serializer.validated_data['from_email']
            display_name = serializer.validated_data['display_name']
            your_name = serializer.validated_data['your_name']
            your_company = serializer.validated_data['your_company']
            your_email = serializer.validated_data['your_email']
            contact_info = serializer.validated_data['contact_info']
            website_url = serializer.validated_data['website_url']
            email_list_file = request.FILES.get('email_list')
            template_id = request.data.get('template_id')
            


            try:
                sender = Sender.objects.get(id=sender_id)
                smtp_server = SMTPServer.objects.get(id=smtp_server_id)
                template = EmailTemplate.objects.get(id=template_id)
            except (Sender.DoesNotExist, SMTPServer.DoesNotExist, EmailTemplate.DoesNotExist):
                return Response({'error': 'Invalid sender, SMTP server, or template.'}, status=status.HTTP_404_NOT_FOUND)

            email_list = []
            csv_file = email_list_file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(csv_file))
            for row in csv_reader:
                email_list.append(row)

            total_emails = len(email_list)
            successful_sends = 0
            failed_sends = 0
            email_statuses = []
            
            try:
                for recipient in email_list:
                    recipient_email = recipient.get('Email')
                    recipient_firstName = recipient.get('firstName')
                    recipient_lastName = recipient.get('lastName')
                    recipient_company = recipient.get('company')

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

                    template_instance = Template(template.body)
                    html_content = template_instance.render(Context(context))

                    email = EmailMessage(
                        subject=template.subject,
                        body=html_content,
                        from_email=f'{display_name} <{from_email}>',
                        to=[recipient_email]
                    )
                    email.content_subtype = 'html'

                    try:
                        email.send()
                        status_message = 'Sent successfully'
                        successful_sends += 1
                    except Exception as e:
                        status_message = f'Failed to send: {str(e)}'
                        failed_sends += 1
                        
                    
                    timestamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                    email_statuses.append({
                        'email': recipient_email,
                        'status': status_message,
                        'timestamp': timestamp
                    })

                return Response({
                    'status': 'All emails processed',
                    'total_emails': total_emails,
                    'successful_sends': successful_sends,
                    'failed_sends': failed_sends,
                    'email_statuses': email_statuses
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({'error': f'Failed to process emails: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

