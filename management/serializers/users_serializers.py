from rest_framework.serializers import ModelSerializer,SerializerMethodField
from rest_framework import serializers
from management.models import *
from rest_framework.validators import UniqueValidator
from .invoice_serializers import UserInvoiceSerializer



class UserSerializer(ModelSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message="This email is already in use."
            )
        ]
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone",
            "profile_picture",
            "is_active",
            "user_type",
        ]

    def create(self, validated_data):
        validated_data["user_type"] = "unassigned"
        return super().create(validated_data)


class TenantApartment(ModelSerializer):
    class Meta:
        model = Apartment
        fields = ["id", "name", "location"]


class TenantBlock(ModelSerializer):
    apartment = TenantApartment(read_only=True)

    class Meta:
        model = Block
        fields = ["id", "apartment", "block_name"]


class TenantUnit(ModelSerializer):
    block = TenantBlock(read_only=True)
    owner = UserSerializer(read_only=True)
    apartment = TenantApartment(read_only=True)

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
        ]


class TenantSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)
    invoices = SerializerMethodField()
    meter_reading = serializers.SerializerMethodField()
    unit = TenantUnit()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "user",
            "lease_start_date",
            "lease_end_date",
            "total_due",
            "total_paid",
            "invoices",
            "meter_reading",
            "unit",
        ]
    def get_invoices(self, obj):
        """
        Fetch invoices related to the tenant's user.
        Filters invoices where `user` matches the tenant's user.
        """
        user_invoices = UserInvoice.objects.filter(user=obj.user)
        return UserInvoiceSerializer(user_invoices, many=True).data
    
    
    def get_meter_reading(self, obj):
        # Get the related unit and its water meter
        unit = getattr(obj, "unit", None)  # Ensure the Tenant has a related Unit
        if not unit:
            return None  # No unit linked to this tenant

        water_meter = getattr(unit, "watermeter", None)  # Access the OneToOneField
        if not water_meter:
            return None  # No water meter linked to this unit

        # Return serialized water meter details
        return {
            "previous_reading": water_meter.previous_reading,
            "current_reading": water_meter.current_reading,
            "reading_date": water_meter.reading_date,
        }


# class TenantSerializer(ModelSerializer):
#     user = UserSerializer(read_only=True)
#     invoices = TenantInvoiceSerializer(many=True, read_only=True)
#     meter_reading = serializers.SerializerMethodField()
#     unit = UnitRecordSerializer(read_only=True)

#     class Meta:
#         model = Tenant
#         fields = [
#             "id",
#             "user",
#             "lease_start_date",
#             "lease_end_date",
#             "total_due",
#             "total_paid",
#             "invoices",
#             "meter_reading",
#             "unit",
#         ]

#     def get_meter_reading(self, obj):
#         # Get the related unit and its water meter
#         unit = getattr(obj, "unit", None)  # Ensure the Tenant has a related Unit
#         if not unit:
#             return None  # No unit linked to this tenant

#         water_meter = getattr(unit, "watermeter", None)  # Access the OneToOneField
#         if not water_meter:
#             return None  # No water meter linked to this unit

#         # Return serialized water meter details
#         return {
#             "previous_reading": water_meter.previous_reading,
#             "current_reading": water_meter.current_reading,
#             "reading_date": water_meter.reading_date,
#         }
