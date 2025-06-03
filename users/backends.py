# users/backends.py
from django.contrib.auth.backends import ModelBackend
from users.models import CustomUser

class UserIDBackend(ModelBackend):
    def authenticate(self, request, user_id=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(user_id=user_id)
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None
