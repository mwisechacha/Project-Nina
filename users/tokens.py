from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class EmailTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_active}"

email_token = EmailTokenGenerator()