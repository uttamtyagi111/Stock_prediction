from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status,viewsets
from django.core.mail import EmailMessage, get_connection
from django.utils import timezone
from io import StringIO
from django.template import Template, Context
import csv,time,logging,os,boto3,time,uuid
from django.conf import settings
from .serializers import EmailSendSerializer,SMTPServerSerializer,UploadedFileSerializer
from .models import   SMTPServer, UploadedFile
from django.shortcuts import  get_object_or_404
from .forms import  SMTPServerForm
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import JsonResponse

logger = logging.getLogger(__name__)

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
    smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.user)
    form = SMTPServerForm(request.data, instance=smtp_server)
    
    if form.is_valid():
        smtp_server = form.save(commit=False)
        smtp_server.user = request.user
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
    



class UploadHTMLToS3(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logger.debug(f"FILES: {request.FILES}")
        logger.debug(f"DATA: {request.data}")

        html_content = None

        if 'file' in request.FILES:
            file = request.FILES['file']
            if not file.name.endswith('.html'):
                return Response({'error': 'File must be an HTML file.'}, status=status.HTTP_400_BAD_REQUEST)
            html_content = file.read()  
        
        # Check if raw HTML content is provided
        elif 'html_content' in request.data:
            html_content = request.data.get('html_content')
            if not isinstance(html_content, str):
                return Response({'error': 'HTML content must be a string.'}, status=status.HTTP_400_BAD_REQUEST)
            html_content = html_content.encode('utf-8')
        

        if not html_content:
            return Response({'error': 'No HTML content provided.'}, status=status.HTTP_400_BAD_REQUEST)

        file_name = f"{uuid.uuid4()}.html"

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        try:
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_name,
                Body=html_content,
                ContentType='text/html'
            )
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        file_url = f"{settings.AWS_S3_FILE_URL}{file_name}"

        uploaded_file = UploadedFile.objects.create(
            name=file_name,
            file_url=file_url,
            user=request.user  
        )

        return Response({
            'user_id': request.user.id,
            'name': uploaded_file.name,
            'file_url': uploaded_file.file_url,
            'file_key': file_name  
        }, status=status.HTTP_201_CREATED)



class UploadedFileList(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        uploaded_files = UploadedFile.objects.filter(user=request.user)  
        serializer = UploadedFileSerializer(uploaded_files, many=True)
        return Response(serializer.data)



class UpdateUploadedFile(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, file_id):
        uploaded_file = get_object_or_404(UploadedFile, id=file_id)
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        existing_file_name = uploaded_file.name
        
        try:
            s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=existing_file_name)
        except Exception as e:
            return Response({'error': f'Failed to delete old file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if 'file' not in request.FILES:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']


        counter = 1
        new_file_name = existing_file_name

        while True:
            try:
                s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=new_file_name)
                new_file_name = f"{existing_file_name.split('.')[0]}({counter}).{existing_file_name.split('.')[-1]}"
                counter += 1
            except s3.exceptions.ClientError:
                break
        

        try:
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=new_file_name,
                Body=file,
                ContentType='text/html'  
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Update the uploaded file record in the database
        uploaded_file.name = new_file_name
        uploaded_file.file_url = f"{settings.AWS_S3_FILE_URL}{new_file_name}"  # Assuming you have this field in your model
        uploaded_file.save()

        return Response({'file_name': new_file_name, 'file_url': uploaded_file.file_url}, status=status.HTTP_200_OK)

    



class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_serializer = UploadedFileSerializer(data=request.data)
        if file_serializer.is_valid():
            file_serializer.save()
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SendEmailsView(APIView):
    
    def get_html_content_from_s3(self, uploaded_file_key):
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            s3_object = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=uploaded_file_key)
            return s3_object['Body'].read().decode('utf-8')
        except Exception as e:
            logger.error(f"Error fetching file from S3: {str(e)}")
            raise
    
    
    
    def post(self, request, *args, **kwargs):
        serializer = EmailSendSerializer(data=request.data)
        if serializer.is_valid():
            smtp_server_ids = serializer.validated_data['smtp_server_ids']
            delay_seconds = serializer.validated_data.get('delay_seconds', 0)
            subject = serializer.validated_data.get('subject')
            uploaded_file_key = serializer.validated_data['uploaded_file_key'] 


            # Get the HTML content from S3
            try:
                file_content = self.get_html_content_from_s3(uploaded_file_key)
            except Exception as e:
                return Response({'error': f'Error fetching file from S3: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

            # Email list CSV file handling
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
                logger.error(f"Error processing email list: {str(e)}")
                return Response({'error': 'Error processing the email list.'}, status=status.HTTP_400_BAD_REQUEST)

            total_emails = len(email_list)
            successful_sends = 0
            failed_sends = 0
            email_statuses = []

            smtp_servers = SMTPServer.objects.filter(id__in=smtp_server_ids)
            num_smtp_servers = len(smtp_servers)

            for i, recipient in enumerate(email_list):
                recipient_email = recipient.get('Email')
                context = {
                    'firstName': recipient.get('firstName'),
                    'lastName': recipient.get('lastName'),
                    'recipient_company': recipient.get('company'),
                    # 'contact_info': serializer.validated_data['contact_info'],
                    # 'website_url': serializer.validated_data['website_url'],
                    'display_name': serializer.validated_data['display_name'],
                    # 'your_name': serializer.validated_data['your_name'],
                    # 'your_company': serializer.validated_data['your_company'],
                    # 'your_email': serializer.validated_data['your_email'],
                }


                try:
                    template = Template(file_content)
                    context_data = Context(context)  
                    email_content = template.render(context_data)
                except Exception as e:
                    logger.error(f"Error formatting email content: {str(e)}")
                    return Response({'error': f'Error formatting email content: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                smtp_server = smtp_servers[i % num_smtp_servers]

                email = EmailMessage(
                    subject=subject,
                    body=email_content,
                    from_email=f'{serializer.validated_data["display_name"]} <{smtp_server.username}>',
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
                    )
                    email.connection = connection
                    email.send()
                    status_message = 'Sent successfully'
                    successful_sends += 1
                except Exception as e:
                    status_message = f'Failed to send: {str(e)}'
                    failed_sends += 1
                    logger.error(f"Error sending email to {recipient_email}: {str(e)}")

                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

                email_statuses.append({
                    'email': recipient_email,
                    'status': status_message,
                    'timestamp': timestamp,
                    'from_email':smtp_server.username,
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
    
    
# import asyncio
# import csv
# from io import StringIO
# import logging
# import boto3
# from django.utils import timezone
# from django.core.mail import EmailMessage, get_connection
# from django.conf import settings
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.template import Context, Template
# from asgiref.sync import sync_to_async  # Wrap sync operations
# from .serializers import EmailSendSerializer
# from .models import SMTPServer

# logger = logging.getLogger(__name__)

# class SendEmailsView(APIView):

#     async def send_email_async(self, recipient_email, subject, email_content, smtp_server):
#         """Send an email asynchronously."""
#         email = EmailMessage(
#             subject=subject,
#             body=email_content,
#             from_email=f'{smtp_server.username}',
#             to=[recipient_email],
#         )
#         email.content_subtype = 'html'
        
#         try:
#             # Wrap email sending in a thread since it's synchronous
#             connection = get_connection(
#                 backend='django.core.mail.backends.smtp.EmailBackend',
#                 host=smtp_server.host,
#                 port=smtp_server.port,
#                 username=smtp_server.username,
#                 password=smtp_server.password,
#                 use_tls=smtp_server.use_tls,
#             )
#             email.connection = connection
#             await asyncio.to_thread(email.send)
#             return 'Sent successfully'
#         except Exception as e:
#             logger.error(f"Error sending email to {recipient_email}: {str(e)}")
#             return f'Failed to send: {str(e)}'

#     async def get_html_content_from_s3(self, uploaded_file_key):
#         """Fetch HTML content from S3 asynchronously."""
#         try:
#             s3 = boto3.client(
#                 's3',
#                 aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#                 region_name=settings.AWS_S3_REGION_NAME
#             )
#             # Wrap S3 object fetching in a thread since it's blocking I/O
#             s3_object = await asyncio.to_thread(s3.get_object, Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=uploaded_file_key)
#             return s3_object['Body'].read().decode('utf-8')
#         except Exception as e:
#             logger.error(f"Error fetching file from S3: {str(e)}")
#             raise

#     async def post(self, request, *args, **kwargs):
#         """Handle the POST request to send emails."""
#         serializer = EmailSendSerializer(data=request.data)
#         if serializer.is_valid():
#             smtp_server_ids = serializer.validated_data['smtp_server_ids']
#             delay_seconds = serializer.validated_data.get('delay_seconds', 0)
#             subject = serializer.validated_data.get('subject')
#             uploaded_file_key = serializer.validated_data['uploaded_file_key']

#             # Get the HTML content from S3 asynchronously
#             try:
#                 file_content = await self.get_html_content_from_s3(uploaded_file_key)
#             except Exception as e:
#                 return Response({'error': f'Error fetching file from S3: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             # Handle email list CSV file asynchronously
#             email_list_file = request.FILES.get('email_list')
#             if not email_list_file:
#                 return Response({'error': 'No email list file provided.'}, status=status.HTTP_400_BAD_REQUEST)

#             email_list = []
#             try:
#                 # Async file read
#                 csv_file = await asyncio.to_thread(email_list_file.read)
#                 csv_file = csv_file.decode('utf-8')
#                 csv_reader = csv.DictReader(StringIO(csv_file))
#                 for row in csv_reader:
#                     email_list.append(row)
#             except Exception as e:
#                 logger.error(f"Error processing email list: {str(e)}")
#                 return Response({'error': 'Error processing the email list.'}, status=status.HTTP_400_BAD_REQUEST)

#             total_emails = len(email_list)
#             successful_sends = 0
#             failed_sends = 0
#             email_statuses = []

#             # Fetch SMTP servers asynchronously
#             smtp_servers = await sync_to_async(list)(SMTPServer.objects.filter(id__in=smtp_server_ids))
#             num_smtp_servers = len(smtp_servers)

#             for i, recipient in enumerate(email_list):
#                 recipient_email = recipient.get('Email')
#                 context = {
#                     'firstName': recipient.get('firstName'),
#                     'lastName': recipient.get('lastName'),
#                     'recipient_company': recipient.get('company'),
#                     'display_name': serializer.validated_data['display_name'],
#                 }

#                 # Render the email content asynchronously
#                 try:
#                     template = Template(file_content)
#                     context_data = Context(context)
#                     email_content = await asyncio.to_thread(template.render, context_data)
#                 except Exception as e:
#                     logger.error(f"Error formatting email content: {str(e)}")
#                     return Response({'error': f'Error formatting email content: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#                 # Cycle through the SMTP servers
#                 smtp_server = smtp_servers[i % num_smtp_servers]

#                 # Send the email asynchronously
#                 status_message = await self.send_email_async(recipient_email, subject, email_content, smtp_server)

#                 if "Sent successfully" in status_message:
#                     successful_sends += 1
#                 else:
#                     failed_sends += 1

#                 timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

#                 # Append email sending status
#                 email_statuses.append({
#                     'email': recipient_email,
#                     'status': status_message,
#                     'timestamp': timestamp,
#                     'from_email': smtp_server.username,
#                     'smtp_server': smtp_server.host,
#                 })

#                 # Add a delay between sending each email if specified
#                 if delay_seconds > 0:
#                     await asyncio.sleep(delay_seconds)

#             return Response({
#                 'status': 'All emails processed',
#                 'total_emails': total_emails,
#                 'successful_sends': successful_sends,
#                 'failed_sends': failed_sends,
#                 'email_statuses': email_statuses
#             }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    
    
    

