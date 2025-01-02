from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from .tenant_models import Tenant
from .properties_models import Unit



class WaterUnitPrice(models.Model):
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=200)
    effective_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.price_per_unit} effective from {self.effective_date}"


class WaterMeter(models.Model):
    unit = models.OneToOneField("Unit", on_delete=models.CASCADE)
    previous_reading = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_reading = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reading_date = models.DateField(auto_now=True)

    def units_used(self):
        return max(0, self.current_reading - self.previous_reading)

    def water_bill(self):
        price_per_unit = WaterUnitPrice.objects.all().first()
        return self.units_used() * price_per_unit

    def clean(self):
        """
        Custom validation to prevent saving if current reading is less than previous reading.
        """
        # Check if the instance exists (i.e., it's an update)
        if self.pk is not None:
            old_instance = WaterMeter.objects.get(pk=self.pk)
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
            old_instance = WaterMeter.objects.get(pk=self.pk)
            self.previous_reading = old_instance.current_reading

        # Call the original save method
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Meter reading for {self.unit} on {self.reading_date}"
    
       

class UtilityInvoice(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, blank=True, null=True
    )
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    previous_water_reading = models.DecimalField(
        max_digits=10, decimal_places=2, null=True
    )  # Specific to water billing
    water_consumption = models.DecimalField(
        max_digits=10, default=0, decimal_places=2, null=True
    )  # Specific to water
    current_water_reading = models.DecimalField(
        max_digits=10, decimal_places=2, null=True
    )  # Specific to water billing
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    reading_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    file = models.FileField(upload_to="invoices/waterbill/", blank=True, null=True)


