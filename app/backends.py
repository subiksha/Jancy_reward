from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        try:
            # Try to find user by username
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # If not found, try email
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password):
            return user
        
        return None
