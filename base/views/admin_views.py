from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
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
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
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
    permission_classes = [IsAdminUser]

    def get(self, request):
        maintenance_requests = MaintenanceRequest.objects.all()
        serializer = MaintenanceRequestSerializer(maintenance_requests, many=True)
        return Response(serializer.data)


class MeterReadingListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        meter_readings = WaterMeterReading.objects.all()
        serializer = WaterMeterReadingsSerializer(meter_readings, many=True)
        return Response(serializer.data)


class VacateListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        vacating = VacateNotice.objects.all()
        serializer = VacateNoticeSerializer(vacating, many=True)
        return Response(serializer.data)


class RecentAdminActivitiesView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Fetch the 10 most recent log entries (admin actions)
        recent_activities = LogEntry.objects.select_related("user").order_by(
            "-action_time"
        )[:6]

        # Serialize the log entries
        serializer = AdminActivitySerializer(recent_activities, many=True)

        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAdminUser])  # Allow any user to access (adjust if needed)
def update_maintenance(request):
    if request.method == "POST":
        a = MaintenanceRequest.objects.filter(id=request.data["id"]).first()
        a.status = request.data["action"]
        a.save()
        return Response(
            {"error": "Updated successfully"},
            status=status.HTTP_200_OK,
        )


class TenantProfileView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        tenant_profiles = TenantProfile.objects.all()
        serializer = TenantProfileSerializer(tenant_profiles, many=True)
        return Response(serializer.data)



# Function to generate a random password
def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for i in range(length))


@api_view(["POST"])
@permission_classes([IsAdminUser])  # Allow any user to access (adjust if needed)
def create_tenant(request):
    data = request.data

    # Extract estate, block, and unit from request
    estate_name = data.get("estate")
    block_name = data.get("block")
    unit_name = data.get("unit")

    # Fetch the property using estate, block, and unit
    try:
        property_obj = Property.objects.filter(
            estate=estate_name, block=block_name, unit=unit_name, available=True
        ).first()
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
            previous_reading=data[
                "meter_reading"
            ],  # Assuming no previous reading, adjust if necessary
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

#############################
##Water Meter Reading View###
#############################

from decimal import Decimal, ROUND_DOWN


@api_view(["POST"])
@permission_classes([IsAdminUser])
def meter_reading_view(request):
    if request.method == "POST":

        try:
            # Retrieve the data from the request
            reading_data = request.data.get("reading")
            new_reading = request.data.get("newReading")

            try:
                # Ensure the input is treated as a string and convert to Decimal
                new_reading_decimal = Decimal(str(new_reading)).quantize(
                    Decimal("0.00"), rounding=ROUND_DOWN
                )
                print(new_reading_decimal)
            except ValueError as e:
                return Response(
                    {"error": f"Invalid reading value: {new_reading}. Error: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch the corresponding property based on estate, block, and unit
            property_instance = Property.objects.get(
                estate=request.data["reading[estate]"],
                block=request.data["reading[block]"],
                unit=request.data["reading[unit]"],
            )

            # Fetch the water meter reading instance for this property
            water_meter_reading = WaterMeterReading.objects.filter(
                property=property_instance
            ).first()
            print("here", property_instance)
            if water_meter_reading:

                # Update the current reading
                water_meter_reading.current_reading = new_reading_decimal

                # Call the save method which includes validation, previous reading update,
                # and all other business logic (water bill calculation, invoice generation)
                water_meter_reading.save()
                return Response(
                    {"message": "Meter reading updated successfully."},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"error": "No water meter reading found for this unit."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Property.DoesNotExist:
            return Response(
                {"error": "Property not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {"error": e.message_dict}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_property(request):
    if request.method == "POST":
        estate_details = json.loads(request.data.get("estateDetails"))

        estate_name = estate_details["estateName"]
        block_name = estate_details["blockName"]
        unit_name = estate_details["unitName"]
        rent_amount = estate_details["rentAmount"]
        owner_name = estate_details.get("ownerName", None)
        owner_email = estate_details.get("ownerEmail", None)
        owner_phone = estate_details.get("ownerPhone", None)
        allow_water_reading = estate_details["allowWaterReading"]

        # Check if the unit already exists within the same estate and block
        check_property = Property.objects.filter(
            estate=estate_name, block=block_name, unit=unit_name
        ).exists()

        if check_property:
            return JsonResponse(
                {
                    "error": "A unit with the same name already exists in this block of the estate."
                },
                status=400,
            )

        # Check if the estate exists
        estate_exists = Property.objects.filter(estate=estate_name).exists()

        if estate_exists:
            # Estate exists, handle multiple landlords
            # Retrieve or create the landlord
            landlord = User.objects.filter(email=owner_email).first()
            if not landlord:
                name_parts = owner_name.split()
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                landlord = User.objects.create(
                    email=owner_email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=owner_phone,
                    password=generate_random_password(),
                    user_type="landlord",
                )

            # Create the unit in the existing estate, associating it with the landlord
            unit = Property.objects.create(
                estate=estate_name,
                block=block_name,
                unit=unit_name,
                rent_price=rent_amount,
                water_meter_present=allow_water_reading,
                landlord=landlord,
            )

            return Response(
                {"message": "New unit added to the estate.", "unit": unit.id},
                status=status.HTTP_201_CREATED,
            )

        else:
            # If the estate does not exist, create a new estate along with the unit
            landlord = User.objects.filter(email=owner_email).first()
            if not landlord:
                name_parts = owner_name.split()
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                landlord = User.objects.create(
                    email=owner_email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=owner_phone,
                    password=generate_random_password(),
                    user_type="landlord",
                )

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


from django.shortcuts import get_object_or_404
from rest_framework.parsers import JSONParser


@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_transaction(request):
    if request.method == "POST":
        email = request.data.get("email")
        amount = request.data.get("amount")
        transaction_id = request.data.get("transaction_id")

        # Validate the required fields
        if not email or not amount or not transaction_id:
            return Response(
                {
                    "error": "All fields (email, amount, transaction_id, timestamp) are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the user based on the email
        user = get_object_or_404(User, email=email)

        # Create the new transaction
        transaction = Transaction.objects.create(
            payee=user,
            amount=amount,
            transaction_id=transaction_id,
        )

        # Serialize the new transaction and return the response
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
