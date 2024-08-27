from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.core.mail import EmailMessage, get_connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.template import Template, Context
# from django.template import Template, Context
from django.template.exceptions import TemplateDoesNotExist
from rest_framework.permissions import IsAuthenticated
import csv,time,logging,shutil,os
from django.conf import settings
from io import StringIO
from django.conf import settings
from .serializers import EmailSendSerializer, EmailTemplateSerializer, SenderSerializer
from .models import EmailTemplate, Sender, SMTPServer, UserEditedTemplate
from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404, redirect
from .forms import SenderForm, SMTPServerForm, EmailTemplateForm, UserEditedTemplateForm
from django.template.loader import get_template
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = '/login/'


# @login_required
# def home(request):
#     senders = Sender.objects.filter(user=request.user)
#     smtp_servers = SMTPServer.objects.filter(user=request.user)
#     templates = EmailTemplate.objects.filter(user=request.user)
    
#     return render(request, 'home.html', {
#         'senders': senders,
#         'smtp_servers': smtp_servers,
#         'templates': templates,
#     })


# @login_required
# def senders_list(request):
#     senders = Sender.objects.filter(user=request.user)
#     return render(request, 'senders_list.html', {'senders': senders})


# @login_required
# def sender_detail(request, pk):
#     sender = get_object_or_404(Sender, pk=pk, user=request.user)
#     return render(request, 'sender_detail.html', {'sender': sender})

# @login_required
# def sender_form(request, pk=None):
#     if pk:
#         sender = get_object_or_404(Sender, pk=pk, user=request.user)
#         form = SenderForm(instance=sender)
#         form_title = 'Edit Sender'
#     else:
#         sender = Sender(user=request.user)  # Initialize with the current user
#         form = SenderForm(instance=sender)
#         form_title = 'Create New Sender'

#     if request.method == 'POST':
#         form = SenderForm(request.POST, instance=sender if pk else None)
#         if form.is_valid():
#             form.save()
#             return redirect('senders-list')

#     return render(request, 'sender_form.html', {'form': form, 'form_title': form_title})




# @login_required
# def sender_create(request):
#     if request.method == 'POST':
#         form = SenderForm(request.POST)
#         if form.is_valid():
#             sender = form.save(commit=False)
#             sender.user = request.user  # Assign the current logged-in user
#             sender.save()
#             return redirect('senders-list')  # Redirect to the sender list page
#     else:
#         form = SenderForm()
    
#     return render(request, 'sender_form.html', {'form': form, 'form_title': 'Create Sender'})

# @login_required
# def sender_delete(request, pk):
#     sender = get_object_or_404(Sender, pk=pk, user=request.user)  # Ensure the sender belongs to the logged-in user
#     if request.method == 'POST':
#         sender.delete()
#         return redirect('senders-list')  # Redirect to the sender list page after deletion
#     return render(request, 'confirm_delete.html', {'sender': sender})


@login_required
def home(request):
    senders = Sender.objects.filter(user=request.user)
    smtp_servers = SMTPServer.objects.filter(user=request.user)
    templates = EmailTemplate.objects.filter(user=request.user)
    
    return JsonResponse({
        'senders': list(senders.values()),
        'smtp_servers': list(smtp_servers.values()),
        'templates': list(templates.values())
    })

@login_required
def senders_list(request):
    senders = Sender.objects.filter(user=request.user)
    return JsonResponse({'senders': list(senders.values())})

@login_required
def sender_detail(request, pk):
    sender = get_object_or_404(Sender, pk=pk, user=request.user)
    return JsonResponse({'sender': sender_to_dict(sender)})

@login_required
def sender_form(request, pk=None):
    if pk:
        sender = get_object_or_404(Sender, pk=pk, user=request.user)
        form = SenderForm(request.POST or None, instance=sender)
    else:
        sender = Sender(user=request.user)
        form = SenderForm(request.POST or None, instance=sender)
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'redirect': 'senders-list'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    return JsonResponse({'form_title': 'Edit Sender' if pk else 'Create New Sender'})

@login_required
def sender_create(request):
    if request.method == 'POST':
        form = SenderForm(request.POST)
        if form.is_valid():
            sender = form.save(commit=False)
            sender.user = request.user
            sender.save()
            return JsonResponse({'success': True, 'redirect': 'senders-list'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    form = SenderForm()
    return JsonResponse({ 'form_title': 'Create Sender'})

@login_required
def sender_delete(request, pk):
    sender = get_object_or_404(Sender, pk=pk, user=request.user)
    
    if request.method == 'POST':
        sender.delete()
        return JsonResponse({'success': True, 'redirect': 'senders-list'})
    
    return JsonResponse({'sender': sender_to_dict(sender)})

# Helper method for converting Sender to a dict for JSON response
def sender_to_dict(sender):
    return {
        'id': sender.id,
        'name': sender.name,
        'email': sender.email,
        # Add other fields as needed
    }



# @login_required
# def smtp_servers_list(request):
#     servers = SMTPServer.objects.filter(user=request.user)
#     return render(request, 'smtp_servers_list.html', {'servers': servers})


# @login_required
# def smtp_server_detail(request, pk):
#     server = get_object_or_404(SMTPServer, pk=pk, user=request.user)
#     return render(request, 'smtp_server_detail.html', {'server': server})


# @login_required
# def smtp_server_form(request, pk=None):
#     if pk:
#         smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.user)
#         form_title = 'Edit SMTP Server'
#     else:
#         smtp_server = SMTPServer(user=request.user)
#         form_title = 'Create New SMTP Server'
    
#     if request.method == 'POST':
#         form = SMTPServerForm(request.POST, instance=smtp_server)
#         if form.is_valid():
#             form.save()
#             return redirect('smtp-servers-list')
#     else:
#         form = SMTPServerForm(instance=smtp_server)

#     return render(request, 'smtp_server_form.html', {'form': form, 'form_title': form_title})


# @login_required
# def smtp_server_edit(request, pk):
#     smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.user)

#     if request.method == "POST":
#         form = SMTPServerForm(request.POST, instance=smtp_server)
#         if form.is_valid():
#             form.save()
#             return redirect('smtp-servers-list')
#     else:
#         form = SMTPServerForm(instance=smtp_server)

#     return render(request, 'smtp_server_edit.html', {'form': form, 'smtp_server': smtp_server})

# @login_required
# def smtp_server_create(request):
#     if request.method == 'POST':
#         form = SMTPServerForm(request.POST)
#         if form.is_valid():
#             smtp_server = form.save(commit=False)
#             smtp_server.user = request.user  # Associate the new server with the current user
#             smtp_server.save()
#             return redirect('smtp-servers-list')  # Redirect to the list of SMTP servers after successful creation
#     else:
#         form = SMTPServerForm()

#     return render(request, 'smtp_server_form.html', {'form': form, 'form_title': 'Create New SMTP Server'})


# @login_required
# def smtp_server_detail(request, pk):
#     smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.user)
#     return render(request, 'smtp_server_detail.html', {'smtp_server': smtp_server})


# from django.http import JsonResponse
# from django.shortcuts import get_object_or_404
# from django.contrib.auth.decorators import login_required
# from .forms import SMTPServerForm
# from email_sender.models import SMTPServer

# @login_required
# def smtp_servers_list(request):
#     servers = SMTPServer.objects.filter(user=request.user)
#     return JsonResponse({'servers': list(servers.values())})

# @login_required
# def smtp_server_detail(request, pk):
#     server = get_object_or_404(SMTPServer, pk=pk, user=request.user)
#     return JsonResponse({'server': server_to_dict(server)})

# @login_required
# def smtp_server_form(request, pk=None):
#     if pk:
#         smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.user)
#         form = SMTPServerForm(request.POST or None, instance=smtp_server)
#         form_title = 'Edit SMTP Server'
#     else:
#         smtp_server = SMTPServer(user=request.user)
#         form = SMTPServerForm(request.POST or None, instance=smtp_server)
#         form_title = 'Create New SMTP Server'
    
#     if request.method == 'POST':
#         if form.is_valid():
#             form.save()
#             return JsonResponse({'success': True, 'redirect': 'smtp-servers-list'})
#         else:
#             return JsonResponse({'success': False, 'errors': form.errors})

#     return JsonResponse({'form': form.as_p(), 'form_title': form_title})

# @login_required
# def smtp_server_create(request):
#     if request.method == 'POST':
#         form = SMTPServerForm(request.POST)
#         if form.is_valid():
#             smtp_server = form.save(commit=False)
#             smtp_server.user = request.user
#             smtp_server.save()
#             return JsonResponse({'success': True, 'redirect': 'smtp-servers-list'})
#         else:
#             return JsonResponse({'success': False, 'errors': form.errors})
    
#     form = SMTPServerForm()
#     return JsonResponse({'form': form.as_p(), 'form_title': 'Create New SMTP Server'})

# @login_required
# def smtp_server_edit(request, pk):
#     smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.user)

#     if request.method == 'POST':
#         form = SMTPServerForm(request.POST, instance=smtp_server)
#         if form.is_valid():
#             form.save()
#             return JsonResponse({'success': True, 'redirect': 'smtp-servers-list'})
#         else:
#             return JsonResponse({'success': False, 'errors': form.errors})
    
#     form = SMTPServerForm(instance=smtp_server)
#     return JsonResponse({'form': form.as_p(), 'smtp_server': smtp_server_to_dict(smtp_server)})

# # Helper method for converting SMTPServer to a dict for JSON response
# def smtp_server_to_dict(smtp_server):
#     return {
#         'id': smtp_server.id,
#         'name': smtp_server.name,
#         'host': smtp_server.host,
#         'port': smtp_server.port,
#         'username': smtp_server.username,
#         'email': smtp_server.email,
        
#     }

####### SMTP SERVERS 

# Helper method for converting SMTPServer to a dict for JSON response
def smtp_server_to_dict(smtp_server):
    return {
        'id': smtp_server.id,
        'name': smtp_server.name,
        'host': smtp_server.host,
        'port': smtp_server.port,
        'username': smtp_server.username,
        'email': smtp_server.email,
        'use_tls': smtp_server.use_tls,
        'use_ssl': smtp_server.use_ssl,
        # 'created_at': smtp_server.created_at.isoformat(),  # Include other fields as necessary
    }

# @login_required
# def smtp_servers_list(request):
#     servers = SMTPServer.objects.filter(user=request.user)
#     return JsonResponse({'servers': [smtp_server_to_dict(server) for server in servers]})
@login_required
def smtp_servers_list(request):
    if request.method == 'GET':
        servers = SMTPServer.objects.filter(user=request.user)
        servers_list = [smtp_server_to_dict(server) for server in servers]
        return JsonResponse({'servers': servers_list, 'form_valid': True}, status=200)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@login_required
def smtp_server_detail(request, pk):
    server = get_object_or_404(SMTPServer, pk=pk, user=request.user)
    return JsonResponse({'server': smtp_server_to_dict(server)})

@login_required
def smtp_server_form(request, pk=None):
    if pk:
        smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.user)
        form = SMTPServerForm(request.POST or None, instance=smtp_server)
        form_title = 'Edit SMTP Server'
    else:
        smtp_server = SMTPServer(user=request.user)
        form = SMTPServerForm(request.POST or None, instance=smtp_server)
        form_title = 'Create New SMTP Server'
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'redirect': 'smtp-servers-list'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    return JsonResponse({'form': form.as_p(), 'form_title': form_title})

@login_required
def smtp_server_create(request):
    if request.method == 'POST':
        form = SMTPServerForm(request.POST)
        if form.is_valid():
            smtp_server = form.save(commit=False)
            smtp_server.user = request.user
            smtp_server.save()
            return JsonResponse({'success': True, 'redirect': 'smtp-servers-list'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    form = SMTPServerForm()
    return JsonResponse({'form': form.as_p(), 'form_title': 'Create New SMTP Server'})

@login_required
def smtp_server_edit(request, pk):
    smtp_server = get_object_or_404(SMTPServer, pk=pk, user=request.user)

    if request.method == 'POST':
        form = SMTPServerForm(request.POST, instance=smtp_server)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'redirect': 'smtp-servers-list'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    form = SMTPServerForm(instance=smtp_server)
    return JsonResponse({'form': form.as_p(), 'smtp_server': smtp_server_to_dict(smtp_server)})





# @login_required
# def email_template_form(request, pk=None):
#     if pk:
#         template = get_object_or_404(EmailTemplate, pk=pk)
#         form_title = 'Edit Email Template'
#     else:
#         template = EmailTemplate()
#         form_title = 'Create New Email Template'
    
#     form = EmailTemplateForm(instance=template)
    
#     if request.method == 'POST':
#         form = EmailTemplateForm(request.POST, instance=template)
#         if form.is_valid():
#             form.save()  # Save the path of the original template
#             return redirect('email_template_list')
    
#     return render(request, 'email_template_form.html', {'form': form, 'form_title': form_title})

# @login_required
# def edit_template(request, pk): #edit email template by different users 
#     original_template = get_object_or_404(EmailTemplate, pk=pk)
#     if request.method == 'POST':
#         form = UserEditedTemplateForm(request.POST)
#         if form.is_valid():
#             user_edited_template = form.save(commit=False)
#             user_edited_template.original_template = original_template
#             user_edited_template.user = request.user
#             template_path = os.path.join(settings.EDITED_TEMPLATES_DIR, os.path.basename(user_edited_template.template_path))
#             shutil.copy(user_edited_template.template_path, template_path)
#             user_edited_template.template_path = template_path
#             user_edited_template.save()
#             return redirect('email_template_list')
#     else:
#         form = UserEditedTemplateForm()
#     return render(request, 'edit_template.html', {'form': form, 'form_title': 'Edit Template'})

# @login_required
# def email_template_list(request):
#     templates = EmailTemplate.objects.all()
#     return render(request, 'email_templates_list.html', {'templates': templates})

# @login_required
# def default_templates_view(request):
#     templates = EmailTemplate.objects.all()
#     return render(request, 'default_templates.html', {'templates': templates})


# @login_required
# def edit_template_view(request, template_id):
#     # Fetch the original template by ID
#     original_template = get_object_or_404(EmailTemplate, id=template_id)
    
#     # Try to load the content from the original template
#     template_path = original_template.template_path
#     print("Loading content from:", template_path)  # Debug statement
    
#     try:
#         if os.path.exists(template_path):
#             with open(template_path, 'r', encoding='utf-8') as file:
#                 initial_content = file.read()  # Load the HTML content from the original template
#         else:
#             print("File not found:", template_path)  # Debug statement
#             initial_content = ''
#     except FileNotFoundError:
#         print("FileNotFoundError:", template_path)  # Debug statement
#         initial_content = ''
#     except Exception as e:
#         print("Error reading file:", e)  # Debug statement
#         initial_content = ''
    
#     if request.method == 'POST':
#         form = UserEditedTemplateForm(request.POST)
#         if form.is_valid():
#             edited_template = form.save(commit=False)
#             edited_template.original_template = original_template
#             edited_template.user = request.user
            
#             # Generate a unique name for the edited template
#             base_name = f"{original_template.name} - Edited"
#             counter = 1
#             new_name = base_name
#             while UserEditedTemplate.objects.filter(name=new_name).exists():
#                 new_name = f"{base_name} ({counter})"
#                 counter += 1
            
#             edited_template.name = new_name
            
#             # Save the edited content to a new file
#             file_name = f"{new_name}.html"
#             new_file_path = os.path.join(settings.MEDIA_ROOT, 'user_edited_templates', file_name)
            
#             os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            
#             with open(new_file_path, 'w', encoding='utf-8') as file:
#                 file.write(request.POST.get('content'))
            
#             edited_template.template_path = new_file_path
#             edited_template.save()
            
#             return redirect('user_templates')
#     else:
#         form = UserEditedTemplateForm(initial={'content': initial_content})

#     return render(request, 'edit_template.html', {
#         'form': form,
#         'original_template': original_template,
#         'initial_content': initial_content
#     })

# @login_required
# def user_templates_view(request):
#     # Fetch user-edited templates for the logged-in user
#     templates = UserEditedTemplate.objects.filter(user=request.user)
    
#     # Load content of each template
#     for template in templates:
#         try:
#             with open(template.template_path, 'r', encoding='utf-8') as file:
#                 template.content = file.read()  # Add content to the template object
#         except FileNotFoundError:
#             template.content = 'Content not available'  # Handle file not found
    
#     # Render the templates with their content
#     return render(request, 'user_templates.html', {'templates': templates})


# @login_required
# def edit_user_template(request, pk):
#     # Get the user-edited template for the logged-in user
#     template = get_object_or_404(UserEditedTemplate, pk=pk, user=request.user)
    
#     # Load the existing content of the template
#     try:
#         with open(template.template_path, 'r', encoding='utf-8') as file:
#             initial_content = file.read()
#     except FileNotFoundError:
#         initial_content = ''
    
#     if request.method == 'POST':
#         form = UserEditedTemplateForm(request.POST, instance=template)
#         if form.is_valid():
#             updated_template = form.save(commit=False)
#             updated_template.user = request.user
            
#             # Save the updated content to the file
#             new_content = request.POST.get('content')
#             with open(template.template_path, 'w', encoding='utf-8') as file:
#                 file.write(new_content)
            
#             updated_template.save()
#             return redirect('user_templates')
#     else:
#         # Ensure that the form is initialized with the current content
#         form = UserEditedTemplateForm(instance=template)
#         form.fields['content'].initial = initial_content
    
#     return render(request, 'edit_user_template.html', {
#         'form': form,
#         'template': template,
#     })


# @login_required
# def email_template_create(request):
#     if request.method == 'POST':
#         form = UserEditedTemplateForm(request.POST)
#         if form.is_valid():
#             new_template = form.save(commit=False)
#             new_template.user = request.user
            
#             # Get the HTML content from the form
#             content = form.cleaned_data['content']
            
#             # Save the content to a new file in the user_edited_templates directory
#             file_name = f"{new_template.name}.html"
#             file_path = os.path.join(settings.MEDIA_ROOT, 'user_edited_templates', file_name)
            
#             # Ensure the directory exists
#             os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
#             # Save the HTML content to the file
#             with open(file_path, 'w', encoding='utf-8') as file:
#                 file.write(content)
            
#             # Update the path in the model and save it
#             new_template.template_path = file_path
#             new_template.original_template = None  # Since it's a new template
#             new_template.save()
            
#             return redirect('user_templates')
#     else:
#         form = UserEditedTemplateForm()

#     return render(request, 'email_template_form.html', {
#         'form': form,
#     })


# @login_required
# def email_template_delete(request, pk):   # this is user edited template delete only name change 
#     template = get_object_or_404(UserEditedTemplate, pk=pk)
    
#     if request.method == 'POST':
#         try:
#             os.remove(template.template_path)
#         except FileNotFoundError:
#             pass  
#         template.delete()
#         return redirect('user_templates') 
    
#     return render(request, 'email_template_form.html', {'template': template})


def template_to_dict(template):
    return {
        'id': template.id,
        'name': template.name,
        'template_path': template.template_path,
        'content': template.content,
        # Add other fields as needed
    }

@login_required
def email_template_form(request, pk=None):
    if pk:
        template = get_object_or_404(EmailTemplate, pk=pk)
        form_title = 'Edit Email Template'
    else:
        template = EmailTemplate()
        form_title = 'Create New Email Template'
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'redirect': 'email_template_list'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    form = EmailTemplateForm(instance=template)
    return JsonResponse({'form': form.as_p(), 'form_title': form_title})

@login_required
def edit_template(request, pk):
    original_template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        form = UserEditedTemplateForm(request.POST)
        if form.is_valid():
            user_edited_template = form.save(commit=False)
            user_edited_template.original_template = original_template
            user_edited_template.user = request.user
            
            # Copy and save the edited template
            template_path = os.path.join(settings.EDITED_TEMPLATES_DIR, os.path.basename(user_edited_template.template_path))
            shutil.copy(user_edited_template.template_path, template_path)
            user_edited_template.template_path = template_path
            user_edited_template.save()
            
            return JsonResponse({'success': True, 'redirect': 'email_template_list'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    form = UserEditedTemplateForm()
    return JsonResponse({'form': form.as_p(), 'form_title': 'Edit Template'})

@login_required
def email_template_list(request):
    templates = EmailTemplate.objects.all()
    return JsonResponse({'templates': list(templates.values())})

@login_required
def default_templates_view(request):
    templates = EmailTemplate.objects.all()
    return JsonResponse({'templates': list(templates.values())})

@login_required
def edit_template_view(request, template_id):
    original_template = get_object_or_404(EmailTemplate, id=template_id)
    template_path = original_template.template_path
    
    try:
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                initial_content = file.read()
        else:
            initial_content = ''
    except Exception as e:
        initial_content = ''
    
    if request.method == 'POST':
        form = UserEditedTemplateForm(request.POST)
        if form.is_valid():
            edited_template = form.save(commit=False)
            edited_template.original_template = original_template
            edited_template.user = request.user
            
            # Generate a unique name for the edited template
            base_name = f"{original_template.name} - Edited"
            counter = 1
            new_name = base_name
            while UserEditedTemplate.objects.filter(name=new_name).exists():
                new_name = f"{base_name} ({counter})"
                counter += 1
            
            edited_template.name = new_name
            file_name = f"{new_name}.html"
            new_file_path = os.path.join(settings.MEDIA_ROOT, 'user_edited_templates', file_name)
            os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            
            with open(new_file_path, 'w', encoding='utf-8') as file:
                file.write(request.POST.get('content'))
            
            edited_template.template_path = new_file_path
            edited_template.save()
            
            return JsonResponse({'success': True, 'redirect': 'user_templates'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    form = UserEditedTemplateForm(initial={'content': initial_content})
    return JsonResponse({'form': form.as_p(), 'initial_content': initial_content})

@login_required
def user_templates_view(request):
    templates = UserEditedTemplate.objects.filter(user=request.user)
    
    for template in templates:
        try:
            with open(template.template_path, 'r', encoding='utf-8') as file:
                template.content = file.read()
        except FileNotFoundError:
            template.content = 'Content not available'
    
    return JsonResponse({'templates': [template_to_dict(t) for t in templates]})

@login_required
def edit_user_template(request, pk):
    template = get_object_or_404(UserEditedTemplate, pk=pk, user=request.user)
    
    try:
        with open(template.template_path, 'r', encoding='utf-8') as file:
            initial_content = file.read()
    except FileNotFoundError:
        initial_content = ''
    
    if request.method == 'POST':
        form = UserEditedTemplateForm(request.POST, instance=template)
        if form.is_valid():
            updated_template = form.save(commit=False)
            updated_template.user = request.user
            
            new_content = request.POST.get('content')
            with open(template.template_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            
            updated_template.save()
            return JsonResponse({'success': True, 'redirect': 'user_templates'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    form = UserEditedTemplateForm(instance=template)
    form.fields['content'].initial = initial_content
    
    return JsonResponse({'form': form.as_p(), 'template': template_to_dict(template)})

@login_required
def email_template_create(request):
    if request.method == 'POST':
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
    
    form = UserEditedTemplateForm()
    return JsonResponse({'form': form.as_p()})

@login_required
def email_template_delete(request, pk):  #this is for user edited template 
    template = get_object_or_404(UserEditedTemplate, pk=pk)
    
    if request.method == 'POST':
        try:
            os.remove(template.template_path)
        except FileNotFoundError:
            pass  
        template.delete()
        return JsonResponse({'success': True,'message': 'Template deleted'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
# Helper method for converting UserEditedTemplate to a dict for JSON response



class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer

class SenderViewSet(viewsets.ModelViewSet):
    queryset = Sender.objects.all()
    serializer_class = SenderSerializer
    

class SendEmailsView(APIView):
    # LoginRequiredMixin
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