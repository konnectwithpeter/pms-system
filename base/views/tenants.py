from rest_framework import viewsets
import os, requests

from re import search, sub
from base.tasks import (
    send_email_task,
    send_password_reset_email,
)  # Import your email sending task
import json

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail
from django.db.models.functions import Now
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.http import HttpResponsePermanentRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import get_template, render_to_string
from django.utils.encoding import DjangoUnicodeDecodeError, smart_bytes, smart_str
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.decorators import (
    api_view,
    action,
    parser_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.files.storage import default_storage
from django.shortcuts import render, get_object_or_404
from datetime import datetime
from django.views import View
from django.core.files.storage import default_storage
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView


from base.models import *
from base.serializers import *

EMAIL_HOST_USER = "Rowg Dev <info@rowg.co.ke>"


class TenantInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get tenant profile
        try:
            tenant_profile = TenantProfile.objects.get(user=request.user)
        except TenantProfile.DoesNotExist:
            return Response({"error": "Tenant profile not found"}, status=404)

        # Serialize tenant profile
        tenant_profile_serializer = TenantProfileSerializer(tenant_profile)

        # Get related invoices
        invoices = RentInvoice.objects.filter(recipient=request.user)
        invoice_serializer = RentInvoiceSerializer(invoices, many=True)

        # Get notifications for the tenant
        notifications = Notification.objects.filter(recipient=request.user)
        notification_serializer = NotificationSerializer(notifications, many=True)

        # Get maintenance requests
        maintenance_requests = MaintenanceRequest.objects.filter(tenant=request.user)
        maintenance_serializer = MaintenanceRequestSerializer(
            maintenance_requests, many=True
        )

        # Return all data in a single response
        data = {
            "tenant_profile": tenant_profile_serializer.data,
            "invoices": invoice_serializer.data,
            "notifications": notification_serializer.data,
            "maintenance_requests": maintenance_serializer.data,
        }

        return Response(data, status=200)


class TenantProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            tenant_profile = TenantProfile.objects.get(user=request.user)
        except TenantProfile.DoesNotExist:
            return Response(
                {"error": "Tenant profile not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TenantProfileSerializer(tenant_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VacateNoticeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = VacateNoticeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(
                serializer.errors
            )  # Print the error message to understand what's wrong
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# List and create maintenance requests
@api_view(["GET", "POST", "PATCH"])
def maintenance_request_view(request):
    if request.method == "GET":
        # Get all maintenance requests for the logged-in tenant
        tenant = request.user
        requests = MaintenanceRequest.objects.filter(tenant=tenant)
        serializer = MaintenanceRequestSerializer(requests, many=True)
        return Response(serializer.data)

    if request.method == "POST":
        # Handle new maintenance request creation
        data = request.data
        tenant = request.user
        property_id = data.get("property_id")

        # Ensure property belongs to the tenant
        try:
            property = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            return Response(
                {"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Prepare the maintenance request data
        request_data = {
            "type": data.get("maintenance_type"),
            "description": data.get("description"),
            "severity": data.get("severity"),
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
        serializer = MaintenanceRequestSerializer(data=request_data)
        if serializer.is_valid():
            # Save the instance with tenant and property
            serializer.save(tenant=tenant, property=property)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "PATCH":
        data = request.data
        print(request.data)
        tenant = User.objects.get(id=data["tenant"])
        maintenance_request = get_object_or_404(
            MaintenanceRequest, property=data["property"], tenant=tenant
        )
        print(maintenance_request)
        return Response(
            {"message": "Status updated successfully"}, status=status.HTTP_200_OK
        )
