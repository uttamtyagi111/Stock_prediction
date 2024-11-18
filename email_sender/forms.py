from django import forms
from .models import  SMTPServer


class SMTPServerForm(forms.ModelForm):
    class Meta:
        model = SMTPServer
        fields = ['name', 'host', 'port', 'username', 'password', 'use_tls']
        

class EmailSendForm(forms.Form):
    smtp_server_ids = forms.ModelMultipleChoiceField(queryset=SMTPServer.objects.all(), widget=forms.CheckboxSelectMultiple)
    # upload_file_key = forms.ModelChoiceField(queryset=upload_file_key.all())
    email_list = forms.FileField()
    subject = forms.CharField(max_length=255)
    # contact_info = forms.CharField(max_length=255)
    # website_url = forms.URLField()
    your_name = forms.CharField(max_length=100)
    # your_company = forms.CharField(max_length=100)
    # your_email = forms.EmailField()
    