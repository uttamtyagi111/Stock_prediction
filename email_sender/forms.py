from django import forms
from .models import Sender, SMTPServer, EmailTemplate

class SenderForm(forms.ModelForm):
    class Meta:
        model = Sender
        fields = ['email','name']
        # from .models import SMTPServer

class SMTPServerForm(forms.ModelForm):
    class Meta:
        model = SMTPServer
        fields = ['name', 'host', 'port', 'username', 'password', 'use_tls']
        
class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
        }
        
class EmailSendForm(forms.Form):
    sender_ids = forms.ModelMultipleChoiceField(queryset=Sender.objects.all(), widget=forms.CheckboxSelectMultiple)
    smtp_server_ids = forms.ModelMultipleChoiceField(queryset=SMTPServer.objects.all(), widget=forms.CheckboxSelectMultiple)
    template_id = forms.ModelChoiceField(queryset=EmailTemplate.objects.all())
    email_list = forms.FileField()
    contact_info = forms.CharField(max_length=255)
    website_url = forms.URLField()
    your_name = forms.CharField(max_length=100)
    your_company = forms.CharField(max_length=100)
    your_email = forms.EmailField()