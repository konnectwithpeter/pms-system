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


class TenantProfile(models.Model):
    user = models.OneToOneField(
        "User", on_delete=models.CASCADE, limit_choices_to={"user_type": "tenant"}
    )  # Link to tenant user
    property = models.ForeignKey(
        "Property",
        on_delete=models.SET_NULL,
        null=True,
        related_name="tenants",
        limit_choices_to={"available": True},
    )

    # Tenant-specific details
    move_in_date = models.DateField(auto_now_add=True)  # Track when the tenant moved in
    move_out_date = models.DateField(null=True, blank=True)  # If tenant has moved out

    # Payment-related fields
    water_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_billed = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=0
    )  # New field for total billed
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_payment_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Tenant Profile: {self.user.first_name} - {self.property.unit}"

    def clean(self):
        # Ensure that the user is a tenant and does not already have a tenant profile
        if self.user.user_type != "tenant":
            raise ValidationError("User must be of type 'tenant'.")

    def update_pending_bill(self):
        """Update the pending bill based on total billed and total paid."""
        print(self.total_billed, self.total_paid)
        self.pending_bill = self.total_billed - self.total_paid

    def save(self, *args, **kwargs):
        self.clean()  # Call the clean method to validate
        # Calculate pending bill and update rent status
        self.update_pending_bill()

        # Call the original save method
        super().save(*args, **kwargs)

        # Set the property as unavailable if linked
        if self.property:
            self.property.available = False
            self.property.save()  # Save the updated property

