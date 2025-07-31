from django.db import models
from django.contrib.auth.models import User


class UserRole(User):
    class Meta:
        proxy = True

    @property
    def is_admin(self):
        return self.is_staff or self.is_superuser or self.groups.filter(name='Администраторы').exists()