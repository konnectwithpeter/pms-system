from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from base.models import *
from base.serializers import *
from rest_framework.decorators import api_view, permission_classes
import string, random
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage


class EstateListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Group properties by estate
        # Group properties by estate
        estates = Property.objects.values_list("estate", flat=True).distinct()
        estate_groups = []

        for idx, estate in enumerate(estates, start=1):
            # Filter properties by estate and group by blocks
            estate_properties = Property.objects.filter(estate=estate)
            blocks = {}
            landlord = (
                estate_properties.first().landlord
            )  # Assuming all properties in an estate have the same landlord

            for property in estate_properties:
                block_name = property.block
                if block_name not in blocks:
                    blocks[block_name] = []
                blocks[block_name].append(property)

            # Prepare the data structure expected by the serializer
            estate_data = {
                "id": idx,
                "name": estate,
                "blocks": [
                    {"block": block_name, "units": blocks[block_name]}
                    for block_name in blocks
                ],
                "landlord": landlord,
            }
            estate_groups.append(estate_data)

        # Serialize the data
        estate_serializer = EstateSerializer(estate_groups, many=True)
        return Response(estate_serializer.data)


class MaintenanceRequestListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        maintenance_requests = MaintenanceRequest.objects.all()
        serializer = MaintenanceRequestSerializer(maintenance_requests, many=True)
        return Response(serializer.data)


class MeterReadingListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        meter_readings = WaterMeterReading.objects.all()
        serializer = WaterMeterReadingsSerializer(meter_readings, many=True)
        return Response(serializer.data)


class TenantProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        tenant_profiles = TenantProfile.objects.all()
        serializer = TenantProfileSerializer(tenant_profiles, many=True)
        return Response(serializer.data)


# Function to generate a random password
def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for i in range(length))


# Function to generate a random password
def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for i in range(length))


@api_view(["POST"])
@permission_classes([AllowAny])  # Allow any user to access (adjust if needed)
def create_tenant(request):
    data = request.data

    # Extract estate, block, and unit from request
    estate_name = data.get("estate")
    block_name = data.get("block")
    unit_name = data.get("unit")

    # Fetch the property using estate, block, and unit
    try:
        property_obj = Property.objects.get(
            estate=estate_name, block=block_name, unit=unit_name, available=True
        )
    except Property.DoesNotExist:
        return Response(
            {"error": "Property not found or not available"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if user with the same email already exists
    try:
        user, created = User.objects.get_or_create(
            email=data["email"],
            defaults={
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "email": data["email"],
                "phone": data["phone"],
                "password": generate_random_password(),  # Set a temporary password
                "user_type": "tenant",
            },
        )
        if not created:
            # If user already exists, return an error or handle accordingly
            return Response(
                {"error": "User with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except IntegrityError as e:
        return Response(
            {"error": "Failed to create user due to: " + str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create the tenant profile
    tenant_profile = TenantProfile.objects.create(
        user=user,
        property=property_obj,
    )
    tenant_profile.save()

    # Optionally, create a meter reading record if the tenant is paying the water bill
    if data.get("pay_water_bill"):
        WaterMeterReading.objects.create(
            property=property_obj,
            previous_reading=0,  # Assuming no previous reading, adjust if necessary
            current_reading=data["meter_reading"],
        )

    # Mark the property as unavailable now
    property_obj.available = False
    property_obj.save()

    # Return a response with tenant details
    return Response(
        {
            "message": "Tenant created successfully",
            "tenant_email": user.email,
            "tenant_password": (
                "Temporary password created" if created else "User already exists"
            ),
        },
        status=status.HTTP_201_CREATED,
    )


import json


@api_view(["POST"])
@permission_classes([AllowAny])
def create_property(request):
    if request.method == "POST":
        # Parse the estateDetails from the request
        estate_details = json.loads(request.data.get("estateDetails"))

        estate_name = estate_details["estateName"]
        block_name = estate_details["blockName"]
        unit_name = estate_details["unitName"]
        rent_amount = estate_details["rentAmount"]
        owner_name = estate_details.get("ownerName", None)  # May be empty
        owner_email = estate_details.get("ownerEmail", None)  # May be empty
        owner_phone = estate_details.get("ownerPhone", None)  # May be
        allow_water_reading = estate_details["allowWaterReading"]

        check_property = Property.objects.filter(
            block=block_name, unit=unit_name
        ).exists()
        # Ensure uniqueness constraint: no duplicate unit in the same estate/block
        if check_property:
            return JsonResponse(
                {
                    "error": "A unit with the same name already exists in this block of the estate."
                },
                status=400,
            )

        estate = Property.objects.filter(estate=estate_name).first()
        if estate:
            # Check if the estate exists

            # The estate exists, find its tenants (assuming tenants are related to the estate)

            if estate.landlord:
                unit = Property.objects.create(
                    estate=estate,
                    block=block_name,
                    unit=unit_name,
                    rent_price=rent_amount,
                    water_meter_present=allow_water_reading,
                    landlord=estate.landlord,  # Associate the unit with the tenant
                )
                return Response(
                    {"message": "Unit allocated to existing tenant.", "unit": unit.id},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"message": "No tenants found for this estate."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        else:

            # Check if user with the same email already exists
            check_landlord = User.objects.filter(email=owner_email)
            print(check_landlord)
            if check_landlord.exists():
                landlord = check_landlord.first()
            else:
                name_parts = owner_name.split()
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                landlord = User.objects.create(
                    email=owner_email,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": owner_email,
                        "phone": owner_phone,
                        "password": generate_random_password(),  # Set a temporary password
                        "user_type": "landlord",
                    },
                )

            # Create a new estate and the associated unit

            unit = Property.objects.create(
                estate=estate_name,
                block=block_name,
                unit=unit_name,
                rent_price=rent_amount,
                water_meter_present=allow_water_reading,
                landlord=landlord,
            )

            return Response(
                {"message": "New estate and landlord created.", "unit": unit.id},
                status=status.HTTP_201_CREATED,
            )

    return Response(
        {"message": "Invalid request method."}, status=status.HTTP_400_BAD_REQUEST
    )
