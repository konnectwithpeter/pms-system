
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from base.models import TenantProfile,Property
from django.contrib.auth import get_user_model

User = get_user_model()




class RentInvoice(models.Model):
    tenant = models.ForeignKey(TenantProfile, on_delete=models.CASCADE, blank=True, null=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    file = models.FileField(upload_to="invoices/rent/", blank=True, null=True)

class WaterBillInvoice(models.Model):
    tenant = models.ForeignKey(TenantProfile, on_delete=models.CASCADE, blank=True, null=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    meter_reading = models.DecimalField(max_digits=10, decimal_places=2)  # Specific to water billing
    issued_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    file = models.FileField(upload_to="invoices/waterbill/", blank=True, null=True)

class ServiceFeeInvoice(models.Model):
    landlord = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    total_units = models.IntegerField()  # Number of properties owned by the landlord
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateField(auto_now_add=True)
    file = models.FileField(upload_to="invoices/service-fee/", blank=True, null=True)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
