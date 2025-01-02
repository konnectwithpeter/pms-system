# views.py

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from management.models import Apartment, Block, Unit
from management.serializers import ApartmentSerializer, BlockSerializer, UnitSerializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from management.models import User
from base.models import MaintenanceRequest
from base.serializers import MaintenanceSerializer
from datetime import datetime


class ApartmentViewSet(ModelViewSet):
    queryset = Apartment.objects.all().order_by("name")
    serializer_class = ApartmentSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        # You can customize the queryset if necessary
        return Apartment.objects.all()


@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_apartment(request):
    serializer = ApartmentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlockViewSet(ModelViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        apartment_id = self.request.query_params.get("apartment_id", None)
        if apartment_id:
            # Ensure the queryset is ordered here as well
            return Block.objects.filter(apartment_id=apartment_id).order_by(
                "block_name"
            )  # Specify ordering
        return Block.objects.all().order_by("block_name")

    def perform_create(self, serializer):
        # You can customize the save method here if needed
        serializer.save()


@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_block(request):
    block_name = request.data.get("name")
    apartment_id = request.data.get("apartment_id")

    # Check if apartment exists
    try:
        apartment = Apartment.objects.get(id=apartment_id)
    except Apartment.DoesNotExist:
        return Response(
            {"error": "Apartment not found."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Check for duplicate block name in the specified apartment
    if Block.objects.filter(block_name=block_name, apartment=apartment).exists():
        return Response(
            {
                "error": "A block with this name already exists in the specified apartment."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create the Block manually if no duplicates are found
    block = Block.objects.create(block_name=block_name, apartment=apartment)

    # Return success response with the created block data
    return Response(
        {"error": "A block with this name already exists in the specified apartment."},
        status=status.HTTP_201_CREATED,
    )


class UnitViewSet(ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        block_id = self.request.query_params.get("block_id", None)
        if block_id:
            return Unit.objects.filter(block_id=block_id)
        return Unit.objects.all()


@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_unit(request):
    # Extracting data from the request
    unit_name = request.data.get("unit_name")
    description = request.data.get("description")
    rent_price = request.data.get("rent_price")
    owner_id = request.data.get("owner_id")
    block_id = request.data.get("block")
    apartment_id = request.data.get("apartment")

    # Validate that all necessary fields are provided
    if (
        not unit_name
        or not rent_price
        or not owner_id
        or not block_id
        or not apartment_id
    ):
        return Response(
            {"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Fetch the block using the block_name and apartment_name
        apartment = Apartment.objects.get(id=apartment_id)
        block = Block.objects.get(apartment=apartment, id=block_id)
    except Apartment.DoesNotExist:
        return Response(
            {"error": "Apartment not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Block.DoesNotExist:
        return Response({"error": "Block not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if a unit with the same name already exists in the block
    if Unit.objects.filter(block=block, unit_number=unit_name).exists():
        return Response(
            {"error": "A unit with this name already exists in this block."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        # Check the user type
        owner = User.objects.get(email=owner_id)

        if owner.user_type == "unassigned":
            # Update the user type to "landlord"
            owner.user_type = "landlord"
            owner.save()

    except User.DoesNotExist:
        return Response(
            {"error": "Owner user not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Prepare the data to save the new unit
    try:
        Unit.objects.create(
            unit_number=unit_name,
            description=description,
            rent_price=rent_price,
            block=block,
            owner=owner,
        )
        return Response(
            
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET", "POST", "PATCH"])
@permission_classes([IsAdminUser])
def maintenance_request_view(request):
    if request.method == "GET":
        #Get all maintenance requests for the logged-in tenant
        requests = MaintenanceRequest.objects.all()
        serializer = MaintenanceSerializer(requests, many=True)
        return Response(serializer.data)
    

    if request.method == "PATCH":
        data = request.data
        
        try:
            # Fetch the maintenance request object
            m_request = MaintenanceRequest.objects.get(id=data["request"])
        except MaintenanceRequest.DoesNotExist:
            return Response(
                {"error": "Maintenance request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if 'budget' exists in the request data
        if 'budget' in data:
            if data['budget'] != 0:
                m_request.status = "In Progress"
                m_request.budget = data['budget']
            else:
                m_request.status = "Completed"
                m_request.completed_at = datetime.now()
        else:
            # If 'budget' is not provided, set status to 'Completed'
            m_request.status = "Completed"

        # Save the changes
        m_request.save()
        print(data.get('budget'), m_request)

        return Response(
            {"message": "Status updated successfully"},
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Invalid request method"},
        status=status.HTTP_405_METHOD_NOT_ALLOWED,
    )