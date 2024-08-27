from django import forms
from .models import Sender, SMTPServer, EmailTemplate,UserEditedTemplate

class SenderForm(forms.ModelForm):
    class Meta:
        model = Sender
        fields = ['email','name']


class SMTPServerForm(forms.ModelForm):
    class Meta:
        model = SMTPServer
        fields = ['name', 'host', 'port', 'username', 'password', 'use_tls']
        

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'template_path'] 


class UserEditedTemplateForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea, label='Template Content')

    class Meta:
        model = UserEditedTemplate
        fields = ['name']       
        
class EmailSendForm(forms.Form):
    sender_ids = forms.ModelMultipleChoiceField(queryset=Sender.objects.all(), widget=forms.CheckboxSelectMultiple)
    smtp_server_ids = forms.ModelMultipleChoiceField(queryset=SMTPServer.objects.all(), widget=forms.CheckboxSelectMultiple)
    template_id = forms.ModelChoiceField(queryset=EmailTemplate.objects.all())
    email_list = forms.FileField()
    subject = forms.CharField(max_length=255)
    contact_info = forms.CharField(max_length=255)
    website_url = forms.URLField()
    your_name = forms.CharField(max_length=100)
    your_company = forms.CharField(max_length=100)
    your_email = forms.EmailField()
    