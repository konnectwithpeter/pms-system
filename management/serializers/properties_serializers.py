from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework import serializers
from management.models import *
from .users_serializers import UserSerializer
from .users_serializers import TenantSerializer


class ApartmentSerializer(ModelSerializer):
    class Meta:
        model = Apartment
        fields = ["id", "name", "location"]


class BlockSerializer(ModelSerializer):
    apartment = ApartmentSerializer(read_only=True)

    class Meta:
        model = Block
        fields = ["id", "apartment", "block_name"]


class UnitSerializer(ModelSerializer):
    block = BlockSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    apartment = ApartmentSerializer(read_only=True)
    tenant = TenantSerializer(read_only=True)
    owner_name = SerializerMethodField()

    class Meta:
        model = Unit
        fields = [
            "id",
            "block",
            "unit_number",
            "owner",
            "description",
            "rent_price",
            "available",
            "water_meter_present",
            "apartment",
            "tenant",
            "owner_name",
        ]

    def get_owner_name(self, obj):
        # Check if the owner exists
        if obj.owner:
            first_name = obj.owner.first_name or ""
            last_name = obj.owner.last_name or ""
            email = obj.owner.email or ""
            return (
                f"{first_name} {last_name} - {email}".strip()
            )  # Combine names and handle None gracefully
        return None


class WaterMeterSerializer(ModelSerializer):
    unit = UnitSerializer(read_only=True)

    class Meta:
        model = WaterMeter
        fields = [
            "unit",
            "previous_reading",
            "current_reading",
            "reading_date",
        ]
