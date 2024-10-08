from rest_framework import serializers
from base.models import (
    User,
    Property,
    TenantProfile,
    MaintenanceRequest,
    RentInvoice,
    VacateNotice,
    Notification,Transaction
)
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.serializers import ModelSerializer
from django.contrib.admin.models import LogEntry


class RegisterUserSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "user_type",
            "profile_picture",
        ]

    # extra_kwargs = {'password':{'write_only':True}}

    def validate(self, attrs):
        email = attrs.get("email", None)
        first_name = attrs.get("first_name", None)
        last_name = attrs.get("last_name", None)
        user_type = attrs.get("user_type", None)

        if not first_name.isalnum():
            raise serializers.ValidationError("The username must be alphanumeric")
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ResetPasswordEmailRequestSerializer(ModelSerializer):
    email = serializers.EmailField(min_length=2)

    class Meta:
        model = User
        fields = ["email"]

    def validate(self, attrs):

        email = attrs["data"].get("email", "")

        return super().validate(attrs)


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        fields = ["email"]


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ["password", "token", "uidb64"]

    def validate(self, attrs):
        try:
            password = attrs.get("password")
            token = attrs.get("token")
            uidb64 = attrs.get("uidb64")

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("The reset link is invalid", 401)

            user.set_password(password)
            user.save()

            return user
        except Exception as e:
            raise AuthenticationFailed("The reset link is invalid", 401)
        return super().validate(attrs)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone",
            "profile_picture",
            "user_type",
        ]


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = "__all__"


class TenantProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    property = PropertySerializer()

    class Meta:
        model = TenantProfile
        fields = [
            "user",
            "property",
            "water_bill",
            "arrears",
            "pending_bill",
            "total_billed",
            "total_paid",
            "rent_status",
            "move_in_date",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "phone_number",
            "amount",
            "transaction_status",
            "transaction_id",
            "timestamp",
        ]


class RentInvoiceSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True)

    class Meta:
        model = RentInvoice
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    sender = UserSerializer()

    class Meta:
        model = Notification
        fields = ["title", "message", "date", "read", "notification_type", "sender"]


class VacateNoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacateNotice
        fields = ["vacate_date", "reason"]

    def validate(self, data):
        print("Validation data:", data)
        return data


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRequest
        fields = [
            "type",
            "description",
            "status",
            "severity",
            "submitted_at",
            "completed_at",
            "image1",
            "image2",
            "image3",
            "video",
            "budget",
        ]


class PropertyAdminSerializer(serializers.ModelSerializer):
    landlord = serializers.SerializerMethodField()
    tenants = TenantProfileSerializer(many=True, read_only=True)
    invoices = RentInvoiceSerializer(many=True, read_only=True)
    maintenances = MaintenanceRequestSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "unit",
            "block",
            "image1",
            "location",
            "landlord",
            "tenants",
            "invoices",
            "maintenances",
        ]

    def get_landlord(self, obj):
        if obj.landlord:
            return {
                "id": obj.landlord.id,
                "email": obj.landlord.email,
                "first_name": obj.landlord.first_name,
                "last_name": obj.landlord.last_name,
                "phone": obj.landlord.phone,
                "profile_picture": (
                    obj.landlord.profile_picture.url
                    if obj.landlord.profile_picture
                    else None
                ),
            }
        return None
