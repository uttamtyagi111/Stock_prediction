from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.core.mail import EmailMessage, get_connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.template import Template, Context
from rest_framework.permissions import IsAuthenticated
import csv,time,logging
from io import StringIO
from .serializers import EmailSendSerializer, EmailTemplateSerializer, SenderSerializer
from .models import EmailTemplate, Sender, SMTPServer
from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404, redirect
from .forms import SenderForm, SMTPServerForm, EmailTemplateForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.db import connection

logger = logging.getLogger(__name__)

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = '/login/'

# Home page with forms for sending emails, adding senders, SMTP servers, and templates
@login_required
def home(request):
    senders = Sender.objects.all()
    smtp_servers = SMTPServer.objects.all()
    templates = EmailTemplate.objects.all()
    
    return render(request, 'home.html', {
        'senders': senders,
        'smtp_servers': smtp_servers,
        'templates': templates,
    })

# @login_required
# def send_emails(request):
#     # Handle file upload and email sending from the form
#     if request.method == 'POST':
#         # Process form data
#         form = request.POST
#         email_list_file = request.FILES.get('email_list')
#         sender_ids = form.getlist('sender_ids')
#         smtp_server_ids = form.getlist('smtp_server_ids')
#         template_id = form.get('template_id')

#         if not email_list_file:
#             return render(request, 'send_emails.html', {'error': 'No email list file provided.'})

#         email_list = []
#         try:
#             csv_file = email_list_file.read().decode('utf-8')
#             csv_reader = csv.DictReader(StringIO(csv_file))
#             for row in csv_reader:
#                 email_list.append(row)
#         except Exception as e:
#             logger.error(f"Error reading CSV file: {str(e)}")
#             return render(request, 'send_emails.html', {'error': 'Error processing the email list.'})

#         # Get selected senders, SMTP servers, and template
#         senders = Sender.objects.filter(id__in=sender_ids)
#         smtp_servers = SMTPServer.objects.filter(id__in=smtp_server_ids)
#         template = get_object_or_404(EmailTemplate, id=template_id)

#         if not senders or not smtp_servers:
#             return render(request, 'send_emails.html', {'error': 'Invalid sender(s) or SMTP server(s).'})

#         # Send emails
#         total_emails = len(email_list)
#         successful_sends = 0
#         failed_sends = 0
#         email_statuses = []

#         num_senders = len(senders)
#         num_smtp_servers = len(smtp_servers)

#         for i, recipient in enumerate(email_list):
#             recipient_email = recipient.get('Email')
#             context = {
#                 'recipient_firstName': recipient.get('firstName'),
#                 'recipient_lastName': recipient.get('lastName'),
#                 'recipient_company': recipient.get('company'),
#                 'contact_info': form.get('contact_info'),
#                 'website_url': form.get('website_url'),
#                 'your_name': form.get('your_name'),
#                 'your_company': form.get('your_company'),
#                 'your_email': form.get('your_email'),
#             }

#             template_instance = Template(template.body)
#             html_content = template_instance.render(Context(context))

#             sender = senders[i % num_senders]
#             smtp_server = smtp_servers[i % num_smtp_servers]

#             email = EmailMessage(
#                 subject=template.subject,
#                 body=html_content,
#                 from_email=f'{form.get("display_name")} <{sender.email}>',
#                 to=[recipient_email]
#             )
#             email.content_subtype = 'html'

#             try:
#                 connection = get_connection(
#                     backend='django.core.mail.backends.smtp.EmailBackend',
#                     host=smtp_server.host,
#                     port=smtp_server.port,
#                     username=smtp_server.username,
#                     password=smtp_server.password,
#                     use_tls=smtp_server.use_tls
#                 )
#                 email.send()
#                 status_message = 'Sent successfully'
#                 successful_sends += 1
#             except Exception as e:
#                 status_message = f'Failed to send: {str(e)}'
#                 failed_sends += 1
#                 logger.error(f"Error sending email to {recipient_email}: {str(e)}")

#             timestamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

#             email_statuses.append({
#                 'email': recipient_email,
#                 'status': status_message,
#                 'timestamp': timestamp
#             })

#         return render(request, 'send_emails.html', {
#             'status': 'All emails processed',
#             'total_emails': total_emails,
#             'successful_sends': successful_sends,
#             'failed_sends': failed_sends,
#             'email_statuses': email_statuses
#         })

#     return render(request, 'send_emails.html')

# Views for Sender and SMTPServer
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
def sender_create(request):
    if request.method == 'POST':
        form = SenderForm(request.POST)
        if form.is_valid():
            sender = form.save(commit=False)
            sender.user = request.user  # Set the user field to the currently logged-in user
            sender.save()
            return redirect('senders-list')  # Redirect to the list of senders after successful creation
    else:
        form = SenderForm()

    return render(request, 'sender_form.html', {'form': form})


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
def smtp_server_create(request):
    if request.method == 'POST':
        form = SMTPServerForm(request.POST)
        if form.is_valid():
            smtp_server = form.save(commit=False)
            smtp_server.user = request.user  # Set the user field to the currently logged-in user
            smtp_server.save()
            return redirect('smtp-servers-list')  # Redirect to the list of SMTP servers after successful creation
    else:
        form = SMTPServerForm()

    return render(request, 'smtp_server_form.html', {'form': form})


@login_required
def smtp_server_detail(request, pk):
    smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.user)
    return render(request, 'smtp_server_detail.html', {'smtp_server': smtp_server})

@login_required
def smtp_server_edit(request, pk):
    smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.user)

    if request.method == "POST":
        form = SMTPServerForm(request.POST, instance=smtp_server)
        if form.is_valid():
            form.save()
            return redirect('smtp-servers-list')
    else:
        form = SMTPServerForm(instance=smtp_server)

    return render(request, 'smtp_server_edit.html', {'form': form, 'smtp_server': smtp_server})

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
            return redirect('email_template_list')
    return render(request, 'email_template_form.html', {'form': form, 'form_title': 'Edit Email Template' if pk else 'Create New Email Template'})

@login_required
def email_template_list(request):
    templates = EmailTemplate.objects.all()
    return render(request, 'email_templates_list.html', {'templates': templates})

@login_required
def email_template_edit(request, pk):
    template = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            return redirect('email-templates-list')
    else:
        form = EmailTemplateForm(instance=template)
    return render(request, 'email_template_edit.html', {'form': form})

@login_required
def email_template_create(request):
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('email-templates-list')  # Redirect to the list after creation
    else:
        form = EmailTemplateForm()
    return render(request, 'email_template_form.html', {'form': form})

@login_required
def email_template_delete(request, pk):
    template = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == 'POST':
        template.delete()
        return redirect('email-templates-list')  # Redirect to the list after deletion
    return render(request, 'email_template_form.html', {'template': template})




class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer

class SenderViewSet(viewsets.ModelViewSet):
    queryset = Sender.objects.all()
    serializer_class = SenderSerializer

class SendEmailsView(APIView):
    # LoginRequiredMixin
    # permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request, *args, **kwargs):
        serializer = EmailSendSerializer(data=request.data)
        if serializer.is_valid():
            sender_ids = serializer.validated_data['sender_ids']
            smtp_server_ids = serializer.validated_data['smtp_server_ids']
            template_id = serializer.validated_data['template_id']
            delay_seconds = serializer.validated_data.get('delay_seconds', 0)  # Retrieve delay value from request

            try:
                senders = Sender.objects.filter(id__in=sender_ids)
                smtp_servers = SMTPServer.objects.filter(id__in=smtp_server_ids)
                template = EmailTemplate.objects.get(id=template_id)

                if not senders or not smtp_servers:
                    return Response({'error': 'Invalid sender(s) or SMTP server(s).'}, status=status.HTTP_404_NOT_FOUND)
            except EmailTemplate.DoesNotExist:
                return Response({'error': 'Invalid email template.'}, status=status.HTTP_404_NOT_FOUND)

            email_list_file = request.FILES.get('email_list')
            if not email_list_file:
                return Response({'error': 'No email list file provided.'}, status=status.HTTP_400_BAD_REQUEST)

            email_list = []
            try:
                csv_file = email_list_file.read().decode('utf-8')
                csv_reader = csv.DictReader(StringIO(csv_file))
                for row in csv_reader:
                    email_list.append(row)
            except Exception as e:
                logger.error(f"Error reading CSV file: {str(e)}")
                return Response({'error': 'Error processing the email list.'}, status=status.HTTP_400_BAD_REQUEST)


            # Log senders and SMTP servers for debugging
            logger.info(f"Available senders: {[sender.email for sender in senders]}")
            logger.info(f"Available SMTP servers: {[smtp_server.host for smtp_server in smtp_servers]}")

            total_emails = len(email_list)
            successful_sends = 0
            failed_sends = 0
            email_statuses = []

            num_senders = len(senders)
            num_smtp_servers = len(smtp_servers)
            
            
            

            for i, recipient in enumerate(email_list):
                recipient_email = recipient.get('Email')
                context = {
                    'recipient_firstName': recipient.get('firstName'),
                    'recipient_lastName': recipient.get('lastName'),
                    'recipient_company': recipient.get('company'),
                    'contact_info': serializer.validated_data['contact_info'],
                    'website_url': serializer.validated_data['website_url'],
                    'your_name': serializer.validated_data['your_name'],
                    'your_company': serializer.validated_data['your_company'],
                    'your_email': serializer.validated_data['your_email'],
                }

                template_instance = Template(template.body)
                html_content = template_instance.render(Context(context))

                sender = senders[i % num_senders]
                smtp_server = smtp_servers[i % num_smtp_servers]

                logger.info(f"Using SMTP server: {smtp_server.host} for email to {recipient_email}")
                
                email = EmailMessage(
                    subject=template.subject,
                    body=html_content,
                    from_email=f'{serializer.validated_data["display_name"]} <{sender.email}>',
                    to=[recipient_email]
                )
                email.content_subtype = 'html'

                try:
                    connection = get_connection(
                        backend='django.core.mail.backends.smtp.EmailBackend',
                        host=smtp_server.host,
                        port=smtp_server.port,
                        username=smtp_server.username,
                        password=smtp_server.password,
                        use_tls=smtp_server.use_tls,
                        use_ssl=smtp_server.use_ssl
                    )
                    
                    email.connection = connection
                    email.send()
                    status_message = 'Sent successfully'
                    successful_sends += 1
                except Exception as e:
                    status_message = f'Failed to send: {str(e)}'
                    failed_sends += 1
                    logger.error(f"Error sending email to {recipient_email}: {str(e)}")

                timestamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                email_statuses.append({
                    'email': recipient_email,
                    'status': status_message,
                    'timestamp': timestamp,
                    'sender': sender.email,
                    'smtp_server': smtp_server.host,
                })
                
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

            return Response({
                'status': 'All emails processed',
                'total_emails': total_emails,
                'successful_sends': successful_sends,
                'failed_sends': failed_sends,
                'email_statuses': email_statuses
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
