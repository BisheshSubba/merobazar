from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )
    phone = models.CharField(max_length=15)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    status = models.BooleanField(default=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    first_name = None
    last_name = None

    def __str__(self):
        return self.username