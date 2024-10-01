from rest_framework import serializers
from .models import Sender, SMTPServer,UploadedFile


class SenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sender
        fields = ['id','name', 'email']
        # read_only_fields = ['id', 'user_id'] 
        
class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'user_id', 'name', 'file_url']  
       



class SMTPServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMTPServer
        fields = ['id', 'name', 'host', 'port', 'username', 'password', 'use_tls']


        

class EmailSendSerializer(serializers.Serializer):
    sender_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    smtp_server_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    # your_name = serializers.CharField()
    # your_company = serializers.CharField()
    # your_email = serializers.EmailField()
    # contact_info = serializers.CharField()
    # website_url = serializers.URLField()
    display_name = serializers.CharField()
    subject = serializers.CharField(max_length=255) 
    email_list = serializers.FileField()
    uploaded_file_key = serializers.CharField() 
    
    def validate_email_list(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are accepted.")
        return value

    # def validate(self, data):
    #     if not data.get('sender_ids'):
    #         raise serializers.ValidationError("At least one sender ID is required.")
    #     if not data.get('smtp_server_ids'):
    #         raise serializers.ValidationError("At least one SMTP server ID is required.")
    #     return data
    def validate_sender_ids(self, value):
        if isinstance(value, str):
            # Split the string by commas and convert to a list of integers
            try:
                value = list(map(int, value.split(',')))
            except ValueError:
                raise serializers.ValidationError("Invalid sender IDs format.")
        return value

    def validate(self, data):
        if not data.get('sender_ids'):
            raise serializers.ValidationError("At least one sender ID is required.")
        if not data.get('smtp_server_ids'):
            raise serializers.ValidationError("At least one SMTP server ID is required.")
        return data