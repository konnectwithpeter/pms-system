
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
    PAYMENT_CHOICES = [
        ("paid", "Paid"),
        ("partially_paid", "Partially Paid"),
        ("overdue", "Overdue"),
    ]
    user = models.OneToOneField(
        'User', on_delete=models.CASCADE, limit_choices_to={"user_type": "tenant"}
    )  # Link to tenant user
    property = models.ForeignKey(
        'Property',
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
        max_digits=10, decimal_places=2, default=0
    )  # New field for total billed
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_payment_date = models.DateField(null=True, blank=True)
    rent_status = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="overdue",
    )  # Rent payment status

    def __str__(self):
        return f"Tenant Profile: {self.user.first_name} - {self.property.unit}"

    def clean(self):
        # Ensure that the user is a tenant and does not already have a tenant profile
        if self.user.user_type != "tenant":
            raise ValidationError("User must be of type 'tenant'.")

    def save(self, *args, **kwargs):
        self.clean()  # Call the clean method to validate
        super().save(*args, **kwargs)  # Call the original save method
        if self.property:
            self.property.available = False
            self.property.save()  # Save the updated property

    def update_rent_status(self):
        """Update rent status based on the payment and arrears."""
        if self.pending_bill == 0:
            self.rent_status = "paid"
            self.arrears = 0
        else:
            self.rent_status = "overdue"
            self.arrears = self.total_billed - self.total_paid
        self.save()
        
        
        
        
# class RentInvoice(models.Model):
#     recipient = models.ForeignKey('User', on_delete=models.CASCADE)
#     file = models.FileField(upload_to="invoices/", blank=True, null=True)
#     property = models.ForeignKey(
#         'Property',
#         on_delete=models.CASCADE,
#         related_name="invoices",
#         null=True,
#         blank=True,
#     )
#     monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     previous_water_reading = models.DecimalField(
#         max_digits=10, decimal_places=2, default=0
#     )
#     current_water_reading = models.DecimalField(
#         max_digits=10, decimal_places=2, default=0
#     )
#     water_consumption = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     water_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     reading_date = models.DateField(blank=True, null=True)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     created_at = models.DateTimeField(auto_now_add=True)
#     billing_period_start = models.DateField(auto_now_add=True)
#     billing_period_end = models.DateField(blank=True, null=True)
#     price_per_unit = models.DecimalField(
#         max_digits=10, decimal_places=2, null=True, blank=True
#     )
#     paid = models.BooleanField(default=False)

#     def __str__(self):
#         return f"Invoice for {self.recipient} - {self.total_amount} due"

#     class Meta:
#         verbose_name = "Invoice"
#         verbose_name_plural = "Invoices"
#         ordering = ["-created_at"]

#     def save(self, *args, **kwargs):
#         """Automatically set the property field based on the tenant's property."""
#         if not self.property and self.recipient:
#             tenant_profile = TenantProfile.objects.filter(user=self.recipient).first()
#             if tenant_profile and tenant_profile.property:
#                 self.property = tenant_profile.property
#         super().save(*args, **kwargs)