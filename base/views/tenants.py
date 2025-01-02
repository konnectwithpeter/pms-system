from rest_framework import viewsets
import os, requests

from re import search, sub
from base.tasks import (
    send_email_task,
    send_password_reset_email,
)  # Import your email sending task
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import (
    api_view,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rest_framework.views import APIView


from base.models import *
from base.serializers import *
from management.models import *

EMAIL_HOST_USER = "Rowg Dev <info@rowg.co.ke>"


class TenantProfileView(APIView):
    """
    Retrieve the tenant profile of the currently authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get the tenant profile for the authenticated user
            tenant = Tenant.objects.get(user=request.user)

            serializer = TenantProfileSerializer(tenant)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Tenant.DoesNotExist:
            return Response(
                {"detail": "Tenant profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


# class VacateNoticeCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         serializer = VacateNoticeSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(tenant=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             print(
#                 serializer.errors
#             )  # Print the error message to understand what's wrong
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# List and create maintenance requests


@api_view(["GET", "POST", "PATCH"])
def maintenance_request_view(request):
    if request.method == "GET":
        # Get all maintenance requests for the logged-in tenant
        tenant = request.user
        requests = MaintenanceRequest.objects.filter(tenant=tenant)
        serializer = MaintenanceSerializer(requests, many=True)
        return Response(serializer.data)

    if request.method == "POST":

        # Handle new maintenance request creation
        data = request.data
        tenant = request.user
        unit_id = (
            data.get("property_id")[0]
            if isinstance(data.get("property_id"), list)
            else data.get("property_id")
        )

        # Ensure property belongs to the tenant
        try:
            property = Unit.objects.get(id=unit_id)
        except Unit.DoesNotExist:
            return Response(
                {"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Prepare the maintenance request data
        request_data = {
            "category": (
                data.get("maintenance_type")[0]
                if isinstance(data.get("maintenance_type"), list)
                else data.get("maintenance_type")
            ),
            "description": (
                data.get("description")[0]
                if isinstance(data.get("description"), list)
                else data.get("description")
            ),
            "severity": (
                data.get("severity")[0]
                if isinstance(data.get("severity"), list)
                else data.get("severity")
            ),
            "unit": {
                "id": property.id,
                "rent_price": property.rent_price,
                "unit_number": property.unit_number,
            },
        }

        # Include images if they were uploaded
        if "image_0" in request.FILES:
            request_data["image1"] = request.FILES["image_0"]

        if "image_1" in request.FILES:
            request_data["image2"] = request.FILES["image_1"]

        if "image_2" in request.FILES:
            request_data["image3"] = request.FILES["image_2"]

        # Optional video field
        if "video" in request.FILES:
            request_data["video"] = request.FILES["video"]
        # Serialize the data and create the maintenance request
        serializer = MaintenanceSerializer(data=request_data)

        if serializer.is_valid():
            print(property)
            # Save the instance with tenant and property
            serializer.save(tenant=tenant, unit=property)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
