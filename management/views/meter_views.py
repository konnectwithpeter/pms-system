from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from management.models import *
from management.serializers import *
from rest_framework.decorators import api_view, permission_classes
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_DOWN


class MeterListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        meter_readings = WaterMeter.objects.all()
        serializer = WaterMeterSerializer(meter_readings, many=True)
        return Response(serializer.data)
    
@api_view(["POST"])
@permission_classes([IsAdminUser])
def meter_view(request):
    if request.method == "POST":
        
        try:
            # Retrieve the data from the request
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
            unit_instance = Unit.objects.get(
                id=request.data['row[unit][id]']
            )

            # Fetch the water meter reading instance for this property
            water_meter_reading = WaterMeter.objects.filter(
                unit=unit_instance
            ).first()
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
        except Unit.DoesNotExist:
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