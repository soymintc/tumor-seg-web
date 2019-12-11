from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    age = models.PositiveIntegerField(
        null=True, # database-related; can store NULL
        blank=True, # validation-related; allow empty value
    )