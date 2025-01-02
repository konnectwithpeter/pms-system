from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from management.models import Unit
from management.models import User

class MaintenanceRequest(models.Model):
    TYPE_CHOICES = [
        ("Plumbing", "Plumbing"),
        ("Electrical", "Electrical"),
        ("Structural", "Structural"),
        ("Other", "Other"),
    ]
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]
    PRIORITY_CHOICES = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
    ]
    tenant = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"user_type": "tenant"}, null=True, blank=True
    )
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=TYPE_CHOICES, default="Other")
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    severity = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="Medium"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    image1 = models.ImageField(upload_to="maintenance-requests/", null=True, blank=True)
    image2 = models.ImageField(upload_to="maintenance-requests/", null=True, blank=True)
    image3 = models.ImageField(upload_to="maintenance-requests/", null=True, blank=True)
    video = models.FileField(upload_to="maintenance-requests/", null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Request by {self.tenant.first_name} - {self.unit}"