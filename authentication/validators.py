import re
from django.core.exceptions import ValidationError

class CustomPasswordValidator:
    def validate(self, password, user=None):
        # Ensure the password has at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                "The password must contain at least one uppercase letter.",
                code='password_no_upper'
            )
        # Ensure the password has at least one digit
        if not re.search(r'\d', password):
            raise ValidationError(
                "The password must contain at least one digit.",
                code='password_no_number'
            )
        # Ensure the password has at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                "The password must contain at least one special character.",
                code='password_no_special'
            )

    def get_help_text(self):
        return (
            "Your password must contain at least one uppercase letter, "
            "one digit, and one special character."
        )
