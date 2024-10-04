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
from base.models import *
from base.serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser



class AdminPropertyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        properties = Property.objects.all()
        serializer = PropertyAdminSerializer(properties, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def landlord_dashboard(request):
    landlord = request.user
    print(landlord)

    if landlord.user_type != "landlord":
        return Response(
            {"error": "Unauthorized access"}, status=status.HTTP_403_FORBIDDEN
        )

    # Fetch all properties for the landlord
    properties = Property.objects.filter(landlord=landlord)

    # Fetch all maintenance requests for properties owned by the landlord
    maintenance_requests = MaintenanceRequest.objects.filter(
        property__landlord=landlord
    )

    # Fetch all tenant profiles for properties owned by the landlord
    tenant_profiles = TenantProfile.objects.filter(property__landlord=landlord)

    # Prepare a dictionary to hold the combined data for each property
    property_data = []

    for property in properties:
        # Get all maintenance requests for this specific property
        property_maintenance_requests = maintenance_requests.filter(property=property)

        # Get the tenant profile associated with this specific property, if any
        tenant_profile = tenant_profiles.filter(property=property).first()

        # Bundle the data together
        property_dict = {
            "property": PropertySerializer(property, context={"request": request}).data,
            "maintenance_requests": MaintenanceRequestSerializer(
                property_maintenance_requests, many=True, context={"request": request}
            ).data,
            "tenant_profile": (
                TenantProfileSerializer(
                    tenant_profile, context={"request": request}
                ).data
                if tenant_profile
                else None
            ),
        }

        # Add the bundled data to the property data list
        property_data.append(property_dict)

    # Fetch unread notifications for the landlord
    notifications = Notification.objects.filter(recipient=landlord)

    # Serialize notifications
    notifications_serializer = NotificationSerializer(notifications, many=True)

    # Combine response data
    response_data = {
        "properties": property_data,
        "notifications": notifications_serializer.data,
    }

    return Response(response_data, status=status.HTTP_200_OK)
