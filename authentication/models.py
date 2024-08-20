from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from phonenumber_field.modelfields import PhoneNumberField  # Import for phone number field

class PasswordResetToken(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Reset token for {self.user.username}"

# Extending the User model using a One-to-One relationship
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = PhoneNumberField(null=False, blank=False, unique=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
