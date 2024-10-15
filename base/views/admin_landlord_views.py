from rest_framework.decorators import api_view, permission_classes

from rest_framework.permissions import IsAdminUser
from rest_framework import status
from base.models import *
from base.serializers import *
from base.serializers import LandlordProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response


class LandlordProfileView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        landlords = LandlordProfile.objects.all()
        serializer = LandlordProfileSerializer(landlords, many=True)
        return Response(serializer.data)


class CreateInvoiceView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = SpecialInvoiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAdminUser])  # Allow any user to access (adjust if needed)
def create_special_invoice(request):
    if request.method == "POST":
        get_user = User.objects.get(email=request.data["email"])
        get_landlord = LandlordProfile.objects.get(user=get_user)

        invoice = SpecialInvoice.objects.create(
            landlord=get_landlord,
            description=request.data["description"],
            price=request.data["price"],
        )
        invoice.save()
        return Response(status=status.HTTP_201_CREATED)
