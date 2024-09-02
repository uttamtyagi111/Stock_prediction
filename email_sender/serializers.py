from rest_framework import serializers
from .models import Sender, SMTPServer, EmailTemplate


class SenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sender
        fields = ['id', 'name', 'email'] 



class SMTPServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMTPServer
        fields = ['id', 'name', 'host', 'port', 'username', 'password', 'use_tls', 'use_ssl']

class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = ['id', 'name'] 
        

class EmailSendSerializer(serializers.Serializer):
    sender_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    smtp_server_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    display_name = serializers.CharField()
    your_name = serializers.CharField()
    your_company = serializers.CharField()
    your_email = serializers.EmailField()
    contact_info = serializers.CharField()
    subject = serializers.CharField(max_length=255) 
    website_url = serializers.URLField()
    email_list = serializers.FileField()
    template_id = serializers.IntegerField()
    
    def validate_email_list(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are accepted.")
        return value

    def validate(self, data):
        if not data.get('sender_ids'):
            raise serializers.ValidationError("At least one sender ID is required.")
        if not data.get('smtp_server_ids'):
            raise serializers.ValidationError("At least one SMTP server ID is required.")
        return data
