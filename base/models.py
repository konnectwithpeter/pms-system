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
        return self.email


class WaterPrice(models.Model):
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.price_per_unit} effective from {self.effective_date}"


class Property(models.Model):
    landlord = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"user_type": "landlord"}
    )

    image1 = models.ImageField(upload_to="property_images/", null=True, blank=True)

    # New fields for location, block, and house number
    location = models.CharField(max_length=100, blank=True, null=True)
    block = models.CharField(max_length=10, blank=True, null=True)  # E.g., "3F"
    house = models.CharField(max_length=10, blank=True, null=True)  # E.g., "F012"

    water_price = models.ForeignKey(
        WaterPrice, on_delete=models.SET_NULL, null=True, blank=True
    )

    description = models.TextField()
    bathrooms = models.IntegerField(default=1)
    bedrooms = models.IntegerField(default=1)
    parking = models.IntegerField(default=1)
    rent_price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.house}  {self.block} {self.location}"

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"


class WaterMeterReading(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
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
                tenant_profile.total_monthly_bill = (
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
                from .tasks import generate_invoice

                # generate an invoice for the tenant
                generate_invoice.delay(
                    tenant_profile.id,
                    self.previous_reading,
                    self.current_reading,
                    reading_date=self.reading_date,
                )

    def __str__(self):
        return f"Meter reading for {self.property} on {self.reading_date}"


class TenantProfile(models.Model):
    PAYMENT_CHOICES = [
        ("paid", "Paid"),
        ("partially_paid", "Partially Paid"),
        ("overdue", "Overdue"),
    ]
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, limit_choices_to={"user_type": "tenant"}
    )  # Link to tenant user
    property = models.ForeignKey(
        Property,
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
    total_monthly_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
        return f"Tenant Profile: {self.user.first_name} - {self.property.house}"

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
        if self.total_monthly_bill == 0:
            self.rent_status = "paid"
            self.arrears = 0
        else:
            self.rent_status = "overdue"
            self.arrears = self.total_billed - self.total_paid
        self.save()


class RentInvoice(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="invoices/", blank=True, null=True)
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="invoices",
        null=True,
        blank=True,
    )
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    previous_water_reading = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    current_water_reading = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    water_consumption = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    water_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reading_date = models.DateField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    billing_period_start = models.DateField(auto_now_add=True)
    billing_period_end = models.DateField(blank=True, null=True)
    price_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice for {self.recipient} - {self.total_amount} due"

    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Automatically set the property field based on the tenant's property."""
        if not self.property and self.recipient:
            tenant_profile = TenantProfile.objects.filter(user=self.recipient).first()
            if tenant_profile and tenant_profile.property:
                self.property = tenant_profile.property
        super().save(*args, **kwargs)


class Transaction(models.Model):
    TRANSACTION_STATUS_CHOICES = [
        ("success", "Success"),
        ("fail", "Fail"),
    ]

    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.CASCADE, related_name="transactions"
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    transaction_status = models.CharField(
        max_length=10,
        choices=TRANSACTION_STATUS_CHOICES,
        default="fail",  # Default value can be set as needed
    )
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.transaction_status}"


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
        User, on_delete=models.CASCADE, limit_choices_to={"user_type": "tenant"}
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
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
        return f"Request by {self.tenant.first_name} - {self.property.house}"


class VacateNotice(models.Model):
    tenant = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"user_type": "tenant"}
    )
    notice_date = models.DateField(auto_now_add=True)
    vacate_date = models.DateField()
    reason = models.TextField(null=True, blank=True)
    reviewed = models.BooleanField(
        default=False
    )  # New field for tracking review status

    def __str__(self):
        return f"{self.tenant} - Vacate on {self.vacate_date}"


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
