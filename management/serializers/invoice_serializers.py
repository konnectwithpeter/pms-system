from management.models import *
from rest_framework.serializers import ModelSerializer

class BillItemsSerializer(ModelSerializer):
    class Meta:
        model = BillItems
        fields = "__all__"

class UserInvoiceSerializer(ModelSerializer):
    bill_items = BillItemsSerializer(many=True)

    class Meta:
        model = UserInvoice
        fields = "__all__"

    def create(self, validated_data):
        bill_items_data = validated_data.pop('bill_items')
        invoice = UserInvoice.objects.create(**validated_data)

        for item_data in bill_items_data:
            bill_item = BillItems.objects.create(**item_data)
            invoice.bill_items.add(bill_item)

        invoice.save()
        return invoice

    def update(self, instance, validated_data):
        bill_items_data = validated_data.pop('bill_items', None)

        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update related bill items if provided
        if bill_items_data is not None:
            instance.bill_items.clear()
            for item_data in bill_items_data:
                bill_item, created = BillItems.objects.get_or_create(
                    id=item_data.get('id'),
                    defaults=item_data
                )
                instance.bill_items.add(bill_item)

        instance.save()
        return instance

