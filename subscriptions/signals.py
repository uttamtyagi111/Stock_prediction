from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from .models import UserProfile

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(
#             user=instance,
#             plan_name='Trial',
#             plan_status='trial',
#             plan_expiration_date=timezone.now() + timedelta(days=15)  # 15-day trial period
#         )

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
         # Create user profile
        profile = UserProfile.objects.create(user=instance)
        # Set plan_expiration_date as 30 days from user creation date
        profile.plan_expiration_date = instance.date_joined + timedelta(days=30)
        profile.save()
        # instance.UserProfile.save()
        
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.contrib.auth.models import User
# from .models import UserProfile

# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     # If the user is created, create the UserProfile
#     if created:
#         profile = UserProfile.objects.create(user=instance)
#         # Set plan_expiration_date as 30 days from user creation date
#         profile.plan_expiration_date = instance.date_joined + timedelta(days=30)
#         profile.save()
#     else:
#         # If the user already exists, save the existing UserProfile
#         instance.userprofile.save()