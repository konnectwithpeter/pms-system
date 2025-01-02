from rest_framework import serializers
from base.models import MaintenanceRequest
from management.models import Tenant, UserInvoice


from management.serializers import *


from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.serializers import ModelSerializer


class TenantProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    unit = UnitSerializer()
    invoices = SerializerMethodField()
    water_meter = SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "user",
            "unit",
            "lease_start_date",
            "total_due",
            "total_paid",
            "lease_end_date",
            "invoices",
            "water_meter",
        ]

    def get_invoices(self, obj):
        user_invoices = UserInvoice.objects.filter(user=obj.user)
        return UserInvoiceSerializer(user_invoices, many=True).data

    def get_water_meter(self, obj):
        # Get the water meter associated with the tenant's unit
        try:
            water_meter = WaterMeter.objects.get(unit=obj.unit)
            return WaterMeterSerializer(water_meter).data
        except WaterMeter.DoesNotExist:
            return None  # Return None if no water meter is found


class MaintenanceSerializer(ModelSerializer):
    unit = UnitSerializer()

    class Meta:
        model = MaintenanceRequest
        fields = [
            "id",
            "category",
            "description",
            "status",
            "severity",
            "submitted_at",
            "completed_at",
            "image1",
            "image2",
            "image3",
            "video",
            "budget",
            "unit",
        ]
        
    
