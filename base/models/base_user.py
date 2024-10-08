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
from .estate_models import Property
from .tenant_models import TenantProfile


class CustomUserManager(BaseUserManager):
    def create_user(
        self,
        email,
        first_name,
        last_name,
        user_type=None,
        password=None,
        **extra_fields,
    ):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)

        # Ensure 'user_type' is included only in `extra_fields` if not already present
        extra_fields.setdefault("user_type", user_type)

        user = self.model(
            email=email, first_name=first_name, last_name=last_name, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, first_name, last_name, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(
            email, first_name, last_name, password=password, **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ("tenant", "Tenant"),
        ("landlord", "Landlord"),
        ("admin", "Admin"),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "user_type"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Transaction(models.Model):
    payee = models.ForeignKey("User", null=True, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    receipt  = models.FileField(upload_to="receipts/", blank=True, null=True)

    def __str__(self):
        return f"Transaction {self.transaction_id}"


@receiver(post_save, sender=Transaction)
def process_payment(sender, instance, created, **kwargs):
    # Check if the transaction is created and if it's successful
    from django.db import transaction as db_transaction

    if created and instance.transaction_status == "success":
        print("provisioning transaction....")
        try:
            # Start a database transaction
            with db_transaction.atomic():
                invoice = instance.invoice
                tenant_profile = TenantProfile.objects.get(user=invoice.recipient)

                if instance.amount == invoice.total_amount:
                    # Mark invoice as paid
                    invoice.paid = True
                    invoice.save()

                    # Update tenant profile
                    tenant_profile.arrears = 0
                    tenant_profile.total_paid += instance.amount
                    tenant_profile.update_rent_status()  # Update status
                elif instance.amount < invoice.total_amount:
                    # Partial payment
                    tenant_profile.arrears = invoice.total_amount - (
                        tenant_profile.total_paid + instance.amount
                    )
                    tenant_profile.total_paid += instance.amount
                    tenant_profile.update_rent_status()  # Update status

                tenant_profile.save()  # Save tenant profile
        except TenantProfile.DoesNotExist:
            print(
                f"Tenant profile not found for invoice recipient: {invoice.recipient}"
            )
        except Exception as e:
            print(f"An error occurred while processing payment: {e}")


class Notification(models.Model):
    TYPE_CHOICES = [
        ("Info", "Info"),
        ("Warning", "Warning"),
        ("Reminder", "Reminder"),
    ]

    title = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    notification_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default="Info"
    )

    # Using the custom User model for sender and recipient
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_notifications"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_notifications"
    )

    def __str__(self):
        return f"{self.title} - {self.recipient.first_name}"
