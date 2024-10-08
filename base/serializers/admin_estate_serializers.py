from rest_framework import serializers
from base.models import *
from .serializers import UserSerializer, PropertySerializer


class UnitSerializer(serializers.Serializer):
    name = serializers.CharField(source="unit")
    rent = serializers.IntegerField(source="rent_price")
    isVacant = serializers.BooleanField(source="available")
    


class BlockSerializer(serializers.Serializer):
    blockName = serializers.CharField(source="block")
    units = UnitSerializer(many=True)


class LandlordSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    email = serializers.EmailField()
    phone = serializers.CharField()

    def get_name(self, obj):
        # Combine first and last name
        return f"{obj.first_name} {obj.last_name}".strip()


class EstateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    blocks = BlockSerializer(many=True)
    landlord = LandlordSerializer()


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    tenantName = serializers.SerializerMethodField()
    phone = serializers.CharField(source="tenant.phone")
    estate = serializers.CharField(source="property.estate")
    block = serializers.CharField(source="property.block")
    unit = serializers.CharField(source="property.unit")
    images = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceRequest
        fields = [
            "id",
            "tenantName",
            "phone",
            "type",
            "severity",
            "status",
            "submitted_at",
            "details",
            "images",
            "estate",
            "block",
            "unit",
        ]

    def get_tenantName(self, obj):
        return f"{obj.tenant.first_name} {obj.tenant.last_name}"

    def get_details(self, obj):
        return {
            "estate": obj.property.estate,
            "block": obj.property.block,
            "unit": obj.property.unit,
            "description": obj.description,
            "images": self.get_images(obj),
            "video": obj.video.url if obj.video else None,
        }

    def get_images(self, obj):
        images = []
        if obj.image1:
            images.append(obj.image1.url)
        if obj.image2:
            images.append(obj.image2.url)
        if obj.image3:
            images.append(obj.image3.url)
        return images


##################
# tenant profiles#
##################
class WaterMeterReadingsSerializer(serializers.ModelSerializer):
    estate = serializers.CharField(source="property.estate", read_only=True)
    block = serializers.CharField(source="property.block", read_only=True)
    unit = serializers.CharField(source="property.unit", read_only=True)

    class Meta:
        model = WaterMeterReading
        fields = [
            "estate",
            "block",
            "unit",
            "previous_reading",
            "current_reading",
            "reading_date",
        ]


# Transaction Serializer
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


# Rent Invoice Serializer
class RentInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentInvoice
        fields = "__all__"


# Water Bill Invoice Serializer
class WaterBillInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterBillInvoice
        fields = "__all__"



# Water Meter Reading Serializer
class WaterMeterReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterMeterReading
        fields = "__all__"


# Tenant Profile Serializer
class TenantProfileSerializer(serializers.ModelSerializer):
    rent_invoices = serializers.SerializerMethodField()
    utility_invoices = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()
    meter_reading = serializers.SerializerMethodField()
    pendingBalance = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="pending_bill"
    )

    user = UserSerializer()
    property = PropertySerializer()

    class Meta:
        model = TenantProfile
        fields = [
            "user",
            "property",
            "rent_invoices",
            "transactions",
            "utility_invoices",
            "meter_reading",
            "pendingBalance",
        ]

    def get_rent_invoices(self, obj):
        rent_invoices = RentInvoiceSerializer(
            RentInvoice.objects.filter(tenant=obj), many=True
        ).data
        return rent_invoices

    def get_utility_invoices(self, obj):
        water_invoices = WaterBillInvoiceSerializer(
            WaterBillInvoice.objects.filter(tenant=obj), many=True
        ).data
        return water_invoices

    def get_transactions(self, obj):
        transactions = TransactionSerializer(
            Transaction.objects.filter(payee=obj.user), many=True
        ).data
        return transactions

    def get_meter_reading(self, obj):
        latest_reading = WaterMeterReading.objects.filter(property=obj.property).last()
        return WaterMeterReadingSerializer(latest_reading).data




