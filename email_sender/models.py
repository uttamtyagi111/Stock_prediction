from django.db import models

class EmailTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Template Name', help_text='Enter a unique name for the template.')
    subject = models.CharField(max_length=255, verbose_name='Email Subject', help_text='Enter the subject line for the email.')
    body = models.TextField(verbose_name='Email Body', help_text='Enter the HTML content of the email template.')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']