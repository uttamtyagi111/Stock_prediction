from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class EmailTemplate(models.Model):
    name = models.CharField(max_length=255) 
    template_path = models.CharField(max_length=255)  

    def __str__(self):
        return self.name

from django.conf import settings
from django.db import models

class UserEditedTemplate(models.Model):
    original_template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Updated to use custom user model
    name = models.CharField(max_length=255)
    template_path = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Sender(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name

class SMTPServer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)

    def __str__(self):
        return self.name
