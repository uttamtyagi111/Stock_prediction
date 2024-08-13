# email_sender/forms.py
from django import forms
from .models import Sender, SMTPServer

class SenderForm(forms.ModelForm):
    class Meta:
        model = Sender
        fields = ['name', 'email']
        from .models import SMTPServer

class SMTPServerForm(forms.ModelForm):
    class Meta:
        model = SMTPServer
        fields = ['name', 'host', 'port', 'username', 'password', 'use_tls']
