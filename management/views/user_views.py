from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from management.models import *
from management.serializers import *
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action


class CreateUserView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User created successfully!", "user": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            # Collect and structure error messages for the response
            errors = {field: error[0] for field, error in serializer.errors.items()}
            return Response(
                {"message": "User creation failed.", "errors": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # GET method to retrieve users with user_type 'unassigned' or 'landlord'
    def get(self, request):
        user_type = request.query_params.get("user_type")

        if user_type:
            # Allow filtering for both 'unassigned' and 'landlord' if specified
            user_types = user_type.split(",")
            users = User.objects.filter(user_type__in=user_types)
        else:
            # Default to all users if no user_type filter is provided
            users = User.objects.all()

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def assign_tenant(request):
    # Extract data from request
    email = request.data.get("user_email")
    unit_id = request.data.get("unit_id")

    # Validate inputs
    if not email or not unit_id:
        return Response(
            {"error": "Both unit_id and user_email are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if the unit exists and is available
    unit = Unit.objects.filter(id=unit_id).first()
    if not unit or not unit.available:
        return Response(
            {"error": "Unit is not available or does not exist"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check if the user exists and is unassigned
    tenant_user = User.objects.filter(email=email).first()
    if not tenant_user:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    if tenant_user.user_type != "unassigned":
        return Response(
            {"error": "User is already assigned to a role"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Optionally, create a meter reading record if the tenant is paying the water bill
        if request.data.get("pay_water_bill") == "true":
            meter_reading_record = WaterMeter.objects.filter(unit=unit).exists()
            print(request.data.get("pay_water_bill"))
            if request.data.get("pay_water_bill") and meter_reading_record == False:
                WaterMeter.objects.create(
                    unit=unit,
                    previous_reading=request.data.get(
                        "meter_reading"
                    ),  # Assuming no previous reading, adjust if necessary
                    current_reading=request.data.get("meter_reading"),
                )
        # Use a transaction to handle partial failure
        # with transaction.atomic():

        # Create Tenant object and link to unit
        Tenant.objects.create(user=tenant_user, unit=unit)

        # Update unit availability
        unit.available = False
        unit.save()

        return Response(
            {"message": "Tenant assigned successfully"}, status=status.HTTP_201_CREATED
        )

    except Exception as e:
        # Rollback user_type if tenant assignment fails
        tenant_user.user_type = "unassigned"
        tenant_user.save()
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AllTenantView(ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["get"])
    def get(self, request, *args, **kwargs):
        try:
            tenant_profile = self.get_object()
            # This will automatically include the units because of the serializer's nested structure
            serializer = self.get_serializer(tenant_profile)
            return Response(serializer.data)
        except Tenant.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


class LandlordProfileViewSet(ModelViewSet):
    queryset = LandlordProfile.objects.all()
    serializer_class = LandlordProfileSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["get"])
    def get_profile_with_units(self, request, pk=None):
        try:
            landlord_profile = self.get_object()
            # This will automatically include the units because of the serializer's nested structure
            serializer = self.get_serializer(landlord_profile)
            return Response(serializer.data)
        except LandlordProfile.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
