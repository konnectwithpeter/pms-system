from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

from .tenant_models import TenantProfile


class WaterPrice(models.Model):
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.price_per_unit} effective from {self.effective_date}"


class Property(models.Model):
    landlord = models.ForeignKey(
        "User", on_delete=models.CASCADE, limit_choices_to={"user_type": "landlord"}
    )

    image1 = models.ImageField(upload_to="property_images/", null=True, blank=True)

    # New fields for location, block, and unit number
    estate = models.CharField(max_length=100, blank=True, null=True)
    block = models.CharField(max_length=10, blank=True, null=True)  # E.g., "3F"
    unit = models.CharField(max_length=10, blank=True, null=True)  # E.g., "F012"

    water_price = models.ForeignKey(
        "WaterPrice", on_delete=models.SET_NULL, null=True, blank=True
    )
    water_meter_present = models.BooleanField(default=True)

    description = models.TextField()
    rent_price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.unit}  {self.block} {self.estate}"

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"


class WaterMeterReading(models.Model):
    property = models.ForeignKey("Property", on_delete=models.CASCADE)
    previous_reading = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_reading = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reading_date = models.DateField(auto_now_add=True)

    def units_used(self):
        return max(0, self.current_reading - self.previous_reading)

    def water_bill(self):
        price_per_unit = (
            self.property.water_price.price_per_unit if self.property.water_price else 0
        )
        return self.units_used() * price_per_unit

    def clean(self):
        """
        Custom validation to prevent saving if current reading is less than previous reading.
        """
        # Check if the instance exists (i.e., it's an update)
        if self.pk is not None:
            old_instance = WaterMeterReading.objects.get(pk=self.pk)
            previous_reading = old_instance.current_reading
        else:
            previous_reading = self.previous_reading

        if self.current_reading < previous_reading:
            raise ValidationError(
                {
                    "current_reading": "Current reading must be greater than or equal to the previous reading."
                }
            )

    def save(self, *args, **kwargs):
        # Perform validation (this will call the clean method)
        self.full_clean()  # This calls the clean method

        # Set the previous reading only if this is an update
        if self.pk is not None:  # Check if this is an update
            old_instance = WaterMeterReading.objects.get(pk=self.pk)
            self.previous_reading = old_instance.current_reading

        # Call the original save method
        super().save(*args, **kwargs)

        # Update the corresponding TenantProfile if needed
        if self.current_reading >= self.previous_reading:
            bill_amount = self.water_bill()
            tenant_profile = TenantProfile.objects.filter(
                property=self.property
            ).first()
            if tenant_profile:
                tenant_profile.water_bill = bill_amount
                tenant_profile.pending_bill = (
                    bill_amount
                    + tenant_profile.property.rent_price
                    + tenant_profile.arrears
                )
                tenant_profile.total_billed = (
                    tenant_profile.total_billed
                    + bill_amount
                    + tenant_profile.property.rent_price
                )
                tenant_profile.save()
                from base.tasks import generate_invoice

                # generate an invoice for the tenant
                generate_invoice.delay(
                    tenant_profile.id,
                    self.previous_reading,
                    self.current_reading,
                    reading_date=self.reading_date,
                )

    def __str__(self):
        return f"Meter reading for {self.property} on {self.reading_date}"


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
        "User", on_delete=models.CASCADE, limit_choices_to={"user_type": "tenant"}
    )
    property = models.ForeignKey("Property", on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="Other")
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
        return f"Request by {self.tenant.first_name} - {self.property.unit}"


class VacateNotice(models.Model):
    tenant = models.ForeignKey(
        "User", on_delete=models.CASCADE, limit_choices_to={"user_type": "tenant"}
    )
    notice_date = models.DateField(auto_now_add=True)
    vacate_date = models.DateField()
    reason = models.TextField(null=True, blank=True)
    reviewed = models.BooleanField(
        default=False
    )  # New field for tracking review status

    def __str__(self):
        return f"{self.tenant} - Vacate on {self.vacate_date}"
