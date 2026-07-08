from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [
        ("landlord", "Landlord"),
        ("tenant", "Tenant"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    contact_number = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="tenant")

    def __str__(self):
        return f"{self.user.email} ({self.role})"
