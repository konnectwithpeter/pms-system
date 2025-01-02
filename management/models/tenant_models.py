from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .base_user import User
import uuid, base64


def generate_id():
    uid = uuid.uuid4()
    return base64.urlsafe_b64encode(uid.bytes).decode("utf-8")[:7]


class Tenant(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={
            "user_type": "unassigned"
        },  # Only unassigned users can be selected
    )
    unit = models.OneToOneField(
        "Unit",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    lease_start_date = models.DateField(auto_now_add=True)
    lease_end_date = models.DateField(null=True, blank=True)
    total_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Tenant Profile: {self.user.first_name} {self.user.last_name} - Unit {self.unit}"

    def clean(self):
        # Ensure the user is currently unassigned
        if self.user.user_type != "unassigned":
            raise ValidationError("Assigned user must be of user_type 'unassigned'.")

    def save(self, *args, **kwargs):
        # Call clean method to validate data before saving
        self.clean()

        # Set user_type to 'tenant' and unit to unavailable if assigning a unit
        if self.unit:
            self.unit.available = False
            self.unit.save()

        # Update the user's user_type to 'tenant'
        self.user.user_type = "tenant"
        self.user.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Revert the user_type to 'unassigned' and set unit to available
        if self.unit:
            self.unit.available = True
            self.unit.save()

        self.user.user_type = "unassigned"
        self.user.save()

        super().delete(*args, **kwargs)


class BillItems(models.Model):
    id = models.CharField(
        primary_key=True, max_length=7, default=generate_id, editable=False
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title


class UserInvoice(models.Model):
    id = models.CharField(
        primary_key=True, max_length=7, default=generate_id, editable=False
    )
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="invoices")
    bill_items = models.ManyToManyField(BillItems, related_name="invoices")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    recurring = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_total_amount(self):
        """Recalculate the total amount based on bill items."""
        self.total_amount = (
            self.bill_items.aggregate(total=models.Sum("amount"))["total"] or 0.00
        )

    def save(self, *args, **kwargs):
        self.calculate_total_amount()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.id} for User {self.user}"

    class Meta:
        ordering = ["-created_at"]
