from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Plan(models.Model):
    name = models.CharField(max_length=100)
    email_limit = models.IntegerField(default=10)  # 10 emails for trial, unlimited for others
    device_limit = models.IntegerField(default=1)  # 1 device for basic, 3 for premium
    duration_days = models.IntegerField(default=30)  # 30 days expiration
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=20, choices=[('Basic', 'Basic'), ('Premium', 'Premium')], null=True, blank=True)
    plan_status = models.CharField(max_length=20, default='inactive')
    emails_sent = models.IntegerField(default=0)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True,unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True,unique=True)
    plan_expiration_date = models.DateTimeField(default=timezone.now() + timedelta(days=30))
    current_plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    # refresh_token = models.TextField(null=True, blank=True)
    # system_info = models.JSONField(null=True, blank=True)
    
    DEFAULT_TRIAL_LIMIT = 10  # Email limit for trial users

    def can_send_email(self):
        """Check if the user can send an email based on their plan and email limit."""

        # Trial users with no active plan
        if self.current_plan is None:
            # Apply a default trial limit if no plan is set
            if self.emails_sent > self.DEFAULT_TRIAL_LIMIT:
                self.plan_status = "expired"
                self.save()
                return False, "Trial limit exceeded. Please subscribe to a plan."
            return True, "You are on a trial; you can send more emails."

        # If the user has a plan, check if it has expired
        if self.plan_expiration_date <= timezone.now():
            self.plan_status = "expired"
            self.save()
            return False, "Your subscription has expired. Please renew your plan."

        # For active plans, verify the email limit
        if self.emails_sent < self.current_plan.email_limit:
            return True, "You can send emails."

        # Handle cases with unlimited plan (e.g., 'Premium')
        if self.current_plan.name == "Premium" and self.current_plan.email_limit == float("inf"):
            return True, "You have unlimited email sending capabilities."

        # If the email limit has been reached
        self.plan_status = "expired"
        self.save()
        return False, "Email limit exceeded. Please renew or upgrade your plan."

    def activate_plan(self, plan):
        """Activate a new plan for the user."""
        self.current_plan = plan  # Save the selected plan in the current_plan field
        self.plan_name = plan.name  # Set the plan_name as the name of the selected plan
        self.plan_status = 'active'  # Set the plan status to active
        self.plan_expiration_date = timezone.now() + timedelta(days=plan.duration_days)  # Set expiration date based on plan's duration
        self.emails_sent = 0  # Reset the emails sent counter
        self.save()  # Save the changes to the user profile

    def choose_plan_view(self, new_plan):
        """Subscribe the user to a selected plan."""
        self.activate_plan(new_plan)  # Call activate_plan to update all the relevant fields
        self.save()  # Ensure the changes are saved after subscription

    def increment_email_count(self):
        """Increment the number of emails sent by the user."""
        self.emails_sent += 1
        self.save()
        
    def check_plan_status(self):
        # Check if the plan is expired
        if self.plan_expiration_date < timezone.now():
            return 'Expired'
        
        # # Check if the device limit is exceeded
        # if self.devices_used >= self.device_limit:
        #     return 'Device Limit Exceeded'
        
        return 'Active'
    
class UserDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField()
    device_name = models.CharField(max_length=100)  # Device name: device1, device2, etc.
    system_info = models.TextField()  # Information like device type, OS, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device_name} - {self.user.email}"




    # def can_send_email(self):
    #     """Check if the user can send an email based on their plan and email limit."""
    #     if self.plan_name is None or self.plan_name == "":
    #         if self.emails_sent >= 10:
    #             # If the trial limit is exceeded, mark the plan as expired
    #             self.plan_status = "expired"
    #             self.save()
    #             return False, "Trial limit exceeded, please subscribe to a plan."
    #         else:
    #             return True, "You are on a trial, you can send more emails."
        
        
    #     elif self.plan_name in ["Basic", "Premium"] and self.plan_expiration_date <= timezone.now():
    #         # If the plan has expired
    #         self.plan_status = "expired"
    #         self.save()
    #         return False, "Your subscription has expired. Please renew your plan."
        
    #     elif self.plan_name in ["Basic", "Premium"] and self.emails_sent < self.current_plan.email_limit:
    #         # If the user has not exceeded the email limit
    #         return True, "You can send emails."
        
    #     elif self.plan_name == "Premium" and self.emails_sent < float("inf"):  # Unlimited for Premium
    #         return True, "You can send emails."
        
    #     else:
    #         return False, "Unknown error."

        
    
    
