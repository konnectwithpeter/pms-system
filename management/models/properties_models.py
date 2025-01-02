from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .base_user import User, LandlordProfile



class Apartment(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Block(models.Model):
    apartment = models.ForeignKey(
        Apartment, on_delete=models.CASCADE, related_name="blocks"
    )
    block_name = models.CharField(max_length=10)  # E.g., "3F"

    def __str__(self):
        return f"{self.block_name} - {self.apartment.name}"


class Unit(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="units")
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"user_type": "landlord"}, null=True, blank=True
    )
    unit_number = models.CharField(max_length=10)  # E.g., "F012"
    description = models.TextField(blank=True, null=True)
    rent_price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    water_meter_present = models.BooleanField(default=True)

    def __str__(self):
        return f"Unit {self.unit_number} - {self.block}"
    
    # Automatically create or update landlord profile when unit is created or updated
    @receiver(post_save, sender='management.Unit')
    def create_landlord_profile(sender, instance, created, **kwargs):
        if created and instance.owner:  # Check if the unit is newly created and has an owner
            owner = instance.owner

            if owner.user_type == "landlord":
                # Create a LandlordProfile if it doesn't already exist
                LandlordProfile.objects.get_or_create(
                    owner=owner,
                    defaults={'total_paid': 0, 'amount_due': 0}
                )