from rest_framework import serializers
from .models import Sender, SMTPServer, EmailTemplate

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

class EmailSendSerializer(serializers.Serializer):
    sender_id = serializers.IntegerField()
    smtp_server_id = serializers.IntegerField()
    from_email = serializers.EmailField()
    display_name = serializers.CharField()
    your_name = serializers.CharField()
    your_company = serializers.CharField()
    your_email = serializers.EmailField()
    contact_info = serializers.CharField()
    website_url = serializers.URLField()
    email_list = serializers.FileField()
    template_id = serializers.IntegerField()  # Include template_id
    
    def validate_email_list(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are accepted.")
        return value
