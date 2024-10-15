from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from base.models import TenantProfile, Property
from django.contrib.auth import get_user_model
from .landlord_models import LandlordProfile

User = get_user_model()


class RentInvoice(models.Model):
    tenant = models.ForeignKey(
        TenantProfile, on_delete=models.CASCADE, blank=True, null=True
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    file = models.FileField(upload_to="invoices/rent/", blank=True, null=True)


class WaterBillInvoice(models.Model):
    tenant = models.ForeignKey(
        TenantProfile, on_delete=models.CASCADE, blank=True, null=True
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
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


class ServiceFeeInvoice(models.Model):
    landlord = models.ForeignKey('LandlordProfile', on_delete=models.CASCADE, blank=True, null=True)
    total_units = models.IntegerField()  # Number of properties owned by the landlord
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateField(auto_now_add=True)
    file = models.FileField(upload_to="invoices/service-fee/", blank=True, null=True)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)


    


class Transaction(models.Model):
    payee = models.ForeignKey("User", null=True, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    receipt = models.FileField(upload_to="receipts/", blank=True, null=True)

    def __str__(self):
        return f"Transaction {self.transaction_id}"


@receiver(post_save, sender=Transaction)
def process_payment(sender, instance, created, **kwargs):
    # Check if the transaction is created and if it's successful
    from django.db import transaction as db_transaction

    if created:
        print("provisioning transaction....")
        payee = User.objects.get(email=instance.payee.email)
        from django.db.models import Sum

        if payee.user_type == "tenant":
            # Send a notification to the tenant
            # Send email to the tenant
            tenant = TenantProfile.objects.get(user=payee)
            total_transactions = Transaction.objects.filter(payee=payee).aggregate(
                total=Sum("amount")
            )["total"]
            tenant.total_paid = total_transactions
            tenant.save()
        elif payee.user_type == "landlord":
            # Send a notification to the landlord
            # Send email to the landlord
            landlord = LandlordProfile.objects.get(user=payee)
            print(landlord)
            total_transactions = Transaction.objects.filter(payee=payee).aggregate(
                total=Sum("amount")
            )["total"]
            landlord.total_paid = total_transactions
            landlord.save()
