from django.db import models
from django.conf import settings

class EmailTemplate(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,  # Make it non-nullable
        blank=False)
    name = models.CharField(max_length=100, unique=True, verbose_name='Template Name', help_text='Enter a unique name for the template.')
    subject = models.CharField(max_length=255, verbose_name='Email Subject', help_text='Enter the subject line for the email.')
    body = models.TextField(verbose_name='Email Body', help_text='Enter the HTML content of the email template.')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

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
