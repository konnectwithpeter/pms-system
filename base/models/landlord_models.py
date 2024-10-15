from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError


class LandlordProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"user_type": "landlord"},
    )
    properties = models.ManyToManyField("Property", related_name="landlord_profiles")
    pending_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_billed = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, default=0
    )  # New field for total billed
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Landlord Profile: {self.user.first_name} {self.user.last_name}"

    def clean(self):
        # Ensure that the user is a landlord and does not already have a landlord profile
        if self.user.user_type != "landlord":
            raise ValidationError("User must be of type 'landlord'.")

    def update_pending_bill(self):
        """Update the pending bill based on total billed and total paid."""
        print(self.total_billed, self.total_paid)
        self.pending_bill = self.total_billed - self.total_paid

    def save(self, *args, **kwargs):
        self.clean()  # Call the clean method to validate
        # Calculate pending bill
        self.update_pending_bill()

        # Call the original save method
        super().save(*args, **kwargs)


# Signal to create a LandlordProfile if it doesn't exist when saving the user
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_landlord_profile(sender, instance, created, **kwargs):
    if instance.user_type == "landlord":
        LandlordProfile.objects.get_or_create(
            user=instance
        )  # Ensures the profile is created if it doesn't exist


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_landlord_profile(sender, instance, **kwargs):
    if instance.user_type == "landlord":
        # Check if the landlord profile exists before saving
        if hasattr(instance, "landlordprofile"):
            instance.landlordprofile.save()



class SpecialInvoice(models.Model):
    landlord = models.ForeignKey('LandlordProfile', on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="invoices/special/", blank=True, null=True)
    

    def __str__(self):
        return f"Invoice {self.id} - {self.email}"


@receiver(post_save, sender=SpecialInvoice)
def process_invoice(sender, instance, created, **kwargs):
    # Check if the transaction is created and if it's successful
    from .base_user import User
    if created:
        owner =instance.landlord
        to_add = instance.price
        owner.total_billed = owner.total_billed + int(to_add)
        owner.save()
        print("Generating Invoice")
        
