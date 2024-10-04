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


@api_view(["GET", "POST"])
@parser_classes([MultiPartParser, FormParser])  # To handle file uploads
def property_list_create(request):
    if request.method == "GET":
        # Return a list of all properties
        properties = Property.objects.all()
        serializer = PropertySerializer(properties, many=True)
        return Response(serializer.data)

    if request.method == "POST":
        # Ensure that the user is authenticated and is a landlord
        if not request.user.is_authenticated or request.user.user_type != "landlord":
            return Response(
                {"error": "Only landlords can create properties"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Use request.data directly, no need to copy
        property_data = {
            "title": request.data.get("title"),
            "rent_price": request.data.get("rent_amount"),
            "address": request.data.get("location"),
            "description": request.data.get("description"),
            "bedrooms": request.data.get("bedrooms"),
            "bathrooms": request.data.get("bathrooms"),
            "parking": request.data.get("parking"),
        }

        image_fields = ["image1", "image2", "image3"]
        for idx, field_name in enumerate(image_fields):
            image_key = f"image_{idx + 1}"
            if image_key in request.FILES:
                uploaded_file = request.FILES[image_key]

                # Ensure proper handling of temporary files
                if isinstance(uploaded_file, TemporaryUploadedFile):
                    uploaded_file.seek(0)
                elif isinstance(uploaded_file, InMemoryUploadedFile):
                    uploaded_file.open()

                property_data[field_name] = uploaded_file

        # Create a property instance with the landlord manually set
        serializer = PropertySerializer(data=property_data)

        if serializer.is_valid():
            # Save the property instance without committing it to the database yet
            property_instance = serializer.save(landlord=request.user)

            # Handle additional files (optional)
            if "files[]" in request.FILES:
                files = request.FILES.getlist("files[]")
                for file in files:
                    pass
                    # PropertyFile.objects.create(property=property_instance, file=file)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# View to update request status
@api_view(["PATCH"])
def update_maintenance_status(request, pk):
    maintenance_request = get_object_or_404(
        MaintenanceRequest, pk=pk, tenant=request.user
    )

    new_status = request.data.get("status")
    if new_status not in dict(MaintenanceRequest.STATUS_CHOICES):
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    maintenance_request.status = new_status

    if new_status == "Completed":
        maintenance_request.completed_at = datetime.now()

    maintenance_request.save()

    return Response(
        {"message": "Status updated successfully"}, status=status.HTTP_200_OK
    )


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter notifications for the authenticated user (recipient)
        return Notification.objects.filter(recipient=self.request.user)

    # Allow landlord and admin users to create/send notifications
    def create(self, request, *args, **kwargs):
        # Ensure only landlords or admins can send notifications
        if request.user.user_type not in ["landlord", "admin"]:
            return Response(
                {"detail": "You do not have permission to send notifications."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # The sender is the logged-in user
        sender = request.user

        # Extract the data to create the notification
        title = request.data.get("title")
        message = request.data.get("message")
        notification_type = request.data.get(
            "notification_type", "Info"
        )  # Default to Info if not provided
        recipient_id = request.data.get(
            "recipient"
        )  # Expect recipient's user ID from frontend

        try:
            recipient = User.objects.get(id=recipient_id)  # Ensure recipient exists
        except User.DoesNotExist:
            return Response(
                {"detail": "Recipient not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Create the notification
        notification = Notification.objects.create(
            title=title,
            message=message,
            notification_type=notification_type,
            sender=sender,
            recipient=recipient,
        )

        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request):
    notification_id = request.data["notification"]
    try:
        # Ensure the notification exists and belongs to the current user
        notification = Notification.objects.get(
            id=notification_id, recipient=request.user
        )
    except Notification.DoesNotExist:
        return Response(
            {"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND
        )

    # Mark the notification as read (assuming you have a 'status' or 'read' field)
    notification.read = (
        True  # or `notification.read = True` if you have a boolean field
    )

    notification.save()

    return Response(
        {"detail": "Notification marked as read."}, status=status.HTTP_200_OK
    )


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["email"] = user.email
        token["user_type"] = user.user_type

        # Debugging: Check profile_picture value
        if user.profile_picture:
            try:
                profile_picture_url = default_storage.url(user.profile_picture.name)
                token["profile_picture"] = profile_picture_url
            except Exception as e:
                print(f"Error getting profile picture URL: {e}")
                token["profile_picture"] = None
        else:
            token["profile_picture"] = None

        # Attach TenantProfile details if user is a tenant and has a TenantProfile

        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # Save the user instance

        email = user.email

        recipient_list = [email]

        # Prepare context for email with only necessary fields
        context = {
            "username": user.first_name,
            "email": user.email,
            # Add other fields as necessary
        }

        # Determine user type and set email parameters
        if user.user_type == "tenant":
            template_name = "base/tenant_welcome.html"  # Use the template name, not the rendered HTML
        elif user.user_type == "landlord":
            template_name = "base/landlord_welcome.html"
        else:
            # Handle other user types or errors
            return Response(
                {"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Send email after successful registration
        send_email_task.delay(recipient_list, template_name, context)

        return Response(status=status.HTTP_201_CREATED)


class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        email = request.data.get("email", "")

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)

            redirect_url = request.data.get("redirect_url", "")
            reset_url = redirect_url + "uidb64=" + str(uidb64) + "/token=" + str(token)

            html_message = render_to_string(
                "base/user_reset_password.html", {"reset_url": reset_url}
            )
            recipient_list = [email]
            send_password_reset_email.delay(recipient_list, html_message)

        return Response(
            {"success": "We have sent you a link to reset your password"},
            status=status.HTTP_200_OK,
        )


class CustomRedirect(HttpResponsePermanentRedirect):

    allowed_schemes = [os.environ.get("APP_SCHEME"), "http", "https"]


class PasswordTokenCheckAPI(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):

        redirect_url = request.GET.get("redirect_url")

        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                if len(redirect_url) > 3:
                    return CustomRedirect(redirect_url + "?token_valid=False")
                else:
                    return CustomRedirect(
                        os.environ.get("FRONTEND_URL", "") + "?token_valid=False"
                    )

            if redirect_url and len(redirect_url) > 3:
                return CustomRedirect(
                    redirect_url
                    + "?token_valid=True&message=Credentials Valid&uidb64="
                    + uidb64
                    + "&token="
                    + token
                )
            else:
                return CustomRedirect(
                    os.environ.get("FRONTEND_URL", "") + "?token_valid=False"
                )

        except DjangoUnicodeDecodeError as identifier:
            try:
                if not PasswordResetTokenGenerator().check_token(user):
                    return CustomRedirect(redirect_url + "?token_valid=False")

            except UnboundLocalError as e:
                return Response(
                    {"error": "Token is not valid, please request a new one"},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [AllowAny]

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"success": True, "message": "Password reset success"},
            status=status.HTTP_200_OK,
        )
