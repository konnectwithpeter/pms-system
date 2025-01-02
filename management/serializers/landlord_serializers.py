from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from management.models import *
from .users_serializers import UserSerializer
from .properties_serializers import BlockSerializer
from .invoice_serializers import UserInvoiceSerializer

class PropertySerializer(ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'unit_number', 'block', 'rent_price', 'available', 'water_meter_present']


class LandlordUnitSerializer(ModelSerializer):
    block = BlockSerializer(read_only=True)
    class Meta:
        model = Unit
        fields = '__all__'
        
        
        
class LandlordProfileSerializer(ModelSerializer):
    owner = UserSerializer(read_only=True) 
    units = SerializerMethodField()
    invoices = SerializerMethodField()

    class Meta:
        model = LandlordProfile
        fields = ['id', 'owner', 'total_paid', 'amount_due', 'units', 'invoices']

    def get_units(self, obj):
        # Retrieve all units owned by the landlord
        units = Unit.objects.filter(owner=obj.owner)
        return LandlordUnitSerializer(units, many=True).data
    
    def get_invoices(self, obj):
        user_invoices = UserInvoice.objects.filter(user=obj.owner)
        return UserInvoiceSerializer(user_invoices, many=True).data