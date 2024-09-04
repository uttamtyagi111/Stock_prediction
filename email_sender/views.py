from datetime import datetime
from django.core.mail import EmailMessage, get_connection
from rest_framework.views import APIView
from rest_framework.response import Response
from django.template import Template, Context
from django.template.exceptions import TemplateDoesNotExist
from rest_framework.permissions import IsAuthenticated
import csv,time,logging,os
from django.conf import settings
from io import StringIO
from .serializers import EmailSendSerializer, EmailTemplateSerializer, SenderSerializer,SMTPServerSerializer
from .models import EmailTemplate, Sender, SMTPServer, UserEditedTemplate
from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404
from .forms import SenderForm, SMTPServerForm, UserEditedTemplateForm
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def senders_list(request):
    request_user_id = request.data.get('user_id')
    senders = Sender.objects.filter(user_id=request_user_id)
    serializer = SenderSerializer(senders, many=True)
    return Response({'senders': serializer.data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sender_detail(request, pk):
    sender = get_object_or_404(Sender, pk=pk, user=request.user)
    serializer = SenderSerializer(sender)
    return Response({'sender': serializer.data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_sender(request):
    serializer = SenderSerializer(data=request.data)
    if serializer.is_valid():
        sender = serializer.save(user=request.user)
        return Response({'message': 'Sender created successfully.', 'sender': SenderSerializer(sender).data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def sender_edit(request, pk):
    sender = get_object_or_404(Sender, pk=pk, user_id=request.user.id)
    form = SenderForm(request.data, instance=sender)
    
    if form.is_valid():
        sender = form.save(commit=False)
        sender.user_id = request.user.id
        sender.save()
        return JsonResponse({'message': 'Sender updated successfully.', 'success': True, 'redirect': 'senders-list'}, status=200)
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def sender_delete(request, pk):
    sender = Sender.objects.filter(pk=pk, user_id=request.user.id).first()
    if sender is None:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    sender.delete()
    return Response({'meesage':'sender deleted successfully'},status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smtp_servers_list(request):
    request_user_id = request.data.get('user_id')
    servers = SMTPServer.objects.filter(user_id=request_user_id)
    serializer = SMTPServerSerializer(servers, many=True)
    return Response({'servers': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smtp_server_detail(request, pk):
    server = get_object_or_404(SMTPServer, pk=pk, user=request.user)
    serializer = SMTPServerSerializer(server)
    return Response({'server': serializer.data}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smtp_server_create(request):
    serializer = SMTPServerSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response({'message': 'SMTP server created successfully.', 'server': serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def smtp_server_edit(request, pk):
    smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.userid)
    form = SMTPServerForm(request.data, instance=smtp_server)
    
    if form.is_valid():
        smtp_server = form.save(commit=False)
        smtp_server.user_id = request.user_id
        smtp_server.save()
        return JsonResponse({'message': 'SMTP server updated successfully.', 'success': True, 'redirect': 'smtp-servers-list'}, status=200)
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def smtp_server_delete(request, pk):
    smtp_server = SMTPServer.objects.filter(pk=pk, user_id=request.user.id).first()
    if smtp_server is None:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    smtp_server.delete()
    return Response({'meesage':'smtp-server deleted successfully'},status=status.HTTP_204_NO_CONTENT)


def replace_special_characters(content):
    replacements = {
        '\u2019': "'",
        '\u2018': "'",
        '\u201C': '"',
        '\u201D': '"',
    }
    if content:
        for unicode_char, replacement in replacements.items():
            content = content.replace(unicode_char, replacement)
    return content
    

def template_to_dict(template):
    return {
        'id': template.id,
        'name': template.name,
        'template_path': template.template_path,
        'content': template.content,
        # Add other fields as needed
    }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def email_template_list(request):
    # Select only the 'id' and 'name' fields from the EmailTemplate model
    templates = EmailTemplate.objects.values('id', 'name')
    return JsonResponse({'templates': list(templates)})
 
@permission_classes([IsAuthenticated])
class ViewTemplateById(APIView):

    def get(self, request, template_id):
        template = get_object_or_404(EmailTemplate, id=template_id)
        
        try:
            with open(template.template_path, 'r', encoding='utf-8') as file:
                content = file.read().replace('\n', '')
        except FileNotFoundError:
            return Response({"error": "Template file not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"id": template.id, "name": template.name, "html_content": content}, status=status.HTTP_200_OK)



@permission_classes([IsAuthenticated])
@api_view(["POST"])
def edit_email_template(request, template_id):
    original_template = get_object_or_404(EmailTemplate, id=template_id)
    template_path = original_template.template_path
    
    try:
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                initial_content = file.read()
                initial_content = replace_special_characters(initial_content)
        else:
            initial_content = ''
    except Exception as e:
        initial_content = ''
    
    # Process form submission
    if request.method == 'POST':
        form = UserEditedTemplateForm(request.POST)
        if form.is_valid():
            edited_template = form.save(commit=False)
            edited_template.original_template = original_template
            edited_template.user = request.user
            
            # Generate a unique name for the edited template
            base_name = f"{original_template.name} - Edited"
            new_name = base_name
            counter = 1
            # Check if the name already exists
            while UserEditedTemplate.objects.filter(name=new_name, user=request.user).exists():
                new_name = f"{base_name} ({counter})"
                counter += 1
            
            edited_template.name = new_name
            file_name = f"{new_name}.html"
            new_file_path = os.path.join(settings.MEDIA_ROOT, 'user_edited_templates', file_name)
            os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            
            print("Before replacement:", request.POST.get('content', ''))
            content = replace_special_characters(request.POST.get('content', ''))
            print("After replacement:", content)
            
            with open(new_file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            edited_template.template_path = new_file_path
            edited_template.save()
            
            return JsonResponse({'message' : 'Your Template is created Sucessfully','success': True, 'redirect': 'user_templates'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    form = UserEditedTemplateForm(initial={'content': replace_special_characters(initial_content)})
    return JsonResponse({'form': form.as_p(), 'initial_content': initial_content})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_templates_view(request):
    if request.user.is_authenticated:
        templates = UserEditedTemplate.objects.filter(user=request.user).values('id', 'name')
        return JsonResponse({'templates': list(templates)})
    else:
        return JsonResponse({'error': 'User is not authenticated'}, status=401)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_template_by_id(request, pk):
    template = get_object_or_404(UserEditedTemplate, pk=pk, user=request.user)
    
    # Read the file content from the path stored in the database
    template_path = template.template_path
    
    if os.path.exists(template_path):
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                content = file.read().replace('\n', '')
        except Exception as e:
            content = f'Error reading file: {str(e)}'
    else:
        content = 'Content not available'
    
    response_data = {
        'id': template.id,
        'name': template.name,
        'content': content,
    }
    
    return JsonResponse(response_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_user_template(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'User must be authenticated.'}, status=401)
    
    template = get_object_or_404(UserEditedTemplate, pk=pk, user=request.user)
    
    try:
        with open(template.template_path, 'r', encoding='utf-8') as file:
            initial_content = file.read()
    except FileNotFoundError:
        return JsonResponse({'success': False, 'error': 'Template file not found.'}, status=404)
    
    if request.method == 'POST':
        form = UserEditedTemplateForm(request.POST, instance=template)
        if form.is_valid():
            updated_template = form.save(commit=False)
            
            new_content = form.cleaned_data['content']
            with open(template.template_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            
            updated_template.save()
            return JsonResponse({'success': True, 'redirect': 'user_templates'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    form = UserEditedTemplateForm(instance=template)
    form.fields['content'].initial = initial_content
    
    return JsonResponse({
        'form': form.as_p(),
        'initial_content': initial_content
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user_template(request):
    form = UserEditedTemplateForm(request.POST)
    if form.is_valid():
        new_template = form.save(commit=False)
        new_template.user = request.user
        
        content = form.cleaned_data['content']
        file_name = f"{new_template.name}.html"
        file_path = os.path.join(settings.MEDIA_ROOT, 'user_edited_templates', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        new_template.template_path = file_path
        new_template.original_template = None
        new_template.save()
        
        return JsonResponse({'success': True, 'redirect': 'user_templates'})
    else:
        return JsonResponse({'success': False, 'errors': form.errors})

@permission_classes([IsAuthenticated])
def delete_user_template(request, pk):  #this is for user edited template 
    template = get_object_or_404(UserEditedTemplate, pk=pk)
    
    if request.method == 'POST':
        try:
            os.remove(template.template_path)
        except FileNotFoundError:
            pass  
        template.delete()
        return JsonResponse({'success': True,'message': 'Template deleted'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
    

class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer

class SenderViewSet(viewsets.ModelViewSet):
    queryset = Sender.objects.all()
    serializer_class = SenderSerializer
    
class SendEmailsView(APIView):
    # permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view
    
    def get(self, request, *args, **kwargs):
        return render(request, 'send_emails.html')
    from django.shortcuts import render


    def post(self, request, *args, **kwargs):
        serializer = EmailSendSerializer(data=request.data)
        if serializer.is_valid():
            sender_ids = serializer.validated_data['sender_ids']
            smtp_server_ids = serializer.validated_data['smtp_server_ids']
            template_id = serializer.validated_data['template_id']
            delay_seconds = serializer.validated_data.get('delay_seconds', 0)
            subject = serializer.validated_data.get('subject') # Get the subject from the request data
            
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

                # Remove extra quotes from the template path
                template_path = template.template_path.strip('"')

                try:
                    with open(template_path, 'r') as file:
                        template_content = file.read()
                except IOError as e:
                    logger.error(f"Error reading template file: {str(e)}")
                    return Response({'error': 'Error reading the template file.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                try:
                    template_instance = Template(template_content)
                    html_content = template_instance.render(Context(context))
                except TemplateDoesNotExist as e:
                    logger.error(f"Template does not exist: {str(e)}")
                    return Response({'error': 'Template does not exist.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Exception as e:
                    logger.error(f"Error rendering template: {str(e)}")
                    return Response({'error': 'Error rendering the template.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                sender = senders[i % num_senders]
                smtp_server = smtp_servers[i % num_smtp_servers]

                logger.info(f"Using SMTP server: {smtp_server.host} for email to {recipient_email}")

                email = EmailMessage(
                    subject=subject, 
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