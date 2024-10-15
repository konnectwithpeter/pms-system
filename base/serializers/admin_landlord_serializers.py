from rest_framework import serializers
from base.models import *
from .serializers import UserSerializer
from .admin_estate_serializers import TransactionSerializer


class LandlordPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ["id", "estate", "block", "unit", "rent_price", "available"]


class ServiceFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFeeInvoice
        fields = "__all__"


class SpecialInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialInvoice
        fields = "__all__"


class LandlordProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Will show the string representation of the user
    properties = LandlordPropertySerializer(
        many=True
    )  # Serialize the related properties
    service_invoices = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()
    special_invoices = serializers.SerializerMethodField()

    class Meta:
        model = LandlordProfile
        fields = [
            "user",
            "properties",
            "pending_bill",
            "total_billed",
            "total_paid",
            "service_invoices",
            "transactions",
            "special_invoices",
        ]

    def get_service_invoices(self, obj):
        service_invoice = ServiceFeeSerializer(
            ServiceFeeInvoice.objects.filter(landlord=obj), many=True
        ).data
        return service_invoice

    def get_special_invoices(self, obj):
        service_invoice = SpecialInvoiceSerializer(
            SpecialInvoice.objects.filter(landlord=obj), many=True
        ).data
        return service_invoice

    def get_transactions(self, obj):
        transactions = TransactionSerializer(
            Transaction.objects.filter(payee=obj.user), many=True
        ).data
        return transactions
