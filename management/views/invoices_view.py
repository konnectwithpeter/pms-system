from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from management.models import UserInvoice
from management.serializers import *
from rest_framework.permissions import IsAdminUser
from django.http import QueryDict
from management.tasks import email_invoice_task


class UserInvoiceView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Create a new invoice with bill items."""
        data = (
            request.data.dict() if isinstance(request.data, QueryDict) else request.data
        )

        # Reformat items
        items = []
        index = 0
        while f"items[{index}][name]" in data:
            items.append(
                {
                    "title": data[f"items[{index}][name]"],
                    "description": data[f"items[{index}][description]"],
                    "amount": data[f"items[{index}][price]"],
                }
            )
            index += 1
        user = User.objects.get(email=data["user"])

        formatted_data = {
            "user": user.id,
            "recurring": data.get("isRecurring", "false") == "true",
            "bill_items": items,
        }

        serializer = UserInvoiceSerializer(data=formatted_data)
        if serializer.is_valid():
            invoice = serializer.save()
            # Send the invoice email through Celery task
            email_invoice_task.apply_async(args=[invoice.id], countdown=3)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        """Edit an existing invoice and its bill items."""
        try:
            invoice = UserInvoice.objects.get(pk=pk)
        except UserInvoice.DoesNotExist:
            return Response(
                {"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserInvoiceSerializer(instance=invoice, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
