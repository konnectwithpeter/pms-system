from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, Permission
from .models import *
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from django.utils.html import format_html


from django_celery_results.models import TaskResult, GroupResult
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    SolarSchedule,
    PeriodicTask,
)

# Unregister django_celery_beat models
admin.site.unregister(ClockedSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(PeriodicTask)

# Unregister django_celery_results models
admin.site.unregister(TaskResult)
admin.site.unregister(GroupResult)

admin.site.unregister(Group)

from django.contrib import admin
from .models import (
    User,
    WaterPrice,
    Property,
    WaterMeterReading,
    TenantProfile,
    Transaction,
)
from django.utils.html import format_html

from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse

from unfold.admin import ModelAdmin
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.html import format_html





from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from django.utils.translation import gettext_lazy as _

class UserAdmin(BaseUserAdmin):
    # Specify fields to display in the user list view
    list_display = ("email", "first_name", "last_name", "user_type", "is_active", "is_staff")
    list_filter = ("user_type", "is_active", "is_staff")

    # Enable search by email, first name, and last name
    search_fields = ("email", "first_name", "last_name")

    # Define the form layout using fieldsets
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal Info"), {"fields": ("first_name", "last_name", "phone", "profile_picture")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("User Type"), {"fields": ("user_type",)}),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    # Fieldsets for the form used when creating a new user
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "user_type", "password1", "password2"),
        }),
    )

    ordering = ("email",)

    # Enable filter horizontal for groups and user permissions
    filter_horizontal = ("groups", "user_permissions")


# Register the custom User admin
admin.site.register(User, UserAdmin)



# Water Price Admin
class WaterPriceAdmin(admin.ModelAdmin):
    list_display = ("price_per_unit", "effective_date")
    search_fields = ("price_per_unit",)
    ordering = ("-effective_date",)


admin.site.register(WaterPrice, WaterPriceAdmin)

from django.contrib import admin
from django.utils.html import format_html
from .models import Property

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "landlord",
        "location",
        "block",
        "house",
        "rent_price",
        "available",
        "created_at",
    )

    readonly_fields = ("created_at", "updated_at", "view_image")

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "landlord",
                    "location",
                    "block",
                    "house",
                    "description",
                    "rent_price",
                    "available",
                    "image1",  # Make the image field editable
                    "view_image",  # To display the image as a card
                )
            },
        ),
        (
            "Facilities",
            {
                "fields": (
                    "bathrooms",
                    "bedrooms",
                    "parking",
                    "water_price",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def view_image(self, obj):
        """Display the uploaded property image as a card."""
        if obj.image1:
            return format_html(
                '<div style="width: 500px; height: 500px; overflow: hidden; border: 1px solid #ccc; border-radius: 5px; display: inline-block;">'
                '<img src="{}" style="width: 100%; height: auto;"/>'
                "</div>",
                obj.image1.url,
            )
        return "No image available"

    view_image.short_description = "Property Image"



@admin.register(WaterMeterReading)
class WaterMeterReadingAdmin(admin.ModelAdmin):
    list_display = (
        "property",
        "previous_reading",
        "current_reading",
        "reading_date",
      
    )

    readonly_fields = ("reading_date",)

    fieldsets = (
        (
            "Meter Reading Details",
            {
                "fields": (
                    "property",
                    "previous_reading",
                    "current_reading",
                    "reading_date",
                   
                )
            },
        ),
    )

    def units_used(self, obj):
        """Display the units of water used based on readings."""
        return obj.units_used()

    units_used.short_description = "Units Used"

    def water_bill(self, obj):
        """Display the calculated water bill."""
        return obj.water_bill()

    water_bill.short_description = "Water Bill"


class TenantProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "property",
        "move_in_date",
        "move_out_date",
        "rent_status",
        "total_monthly_bill",
        "total_billed",
        "total_paid",
    )
    list_filter = ("rent_status", "property")
    search_fields = ("user__email", "property__house", "property__block")
    ordering = ("-move_in_date",)

    # Specify fields that should be read-only in the admin form
    readonly_fields = ("move_in_date", "total_billed", "total_paid")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "property",
                    "move_in_date",
                    "move_out_date",
                )  # Include move_in_date here
            },
        ),
        (
            "Billing Information",
            {
                "fields": (
                    "total_monthly_bill",
                    "total_billed",
                    "total_paid",
                    "rent_status",
                ),
            },
        ),
       
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("user", "property")
        return queryset

    def total_billed(self, obj):
        return obj.calculate_total_billed()  # Replace with actual calculation logic

    def total_paid(self, obj):
        return obj.calculate_total_paid()  # Replace with actual logic


# Register the TenantProfileAdmin with the TenantProfile model
admin.site.register(TenantProfile, TenantProfileAdmin)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice', 'phone_number', 'amount', 'transaction_status', 'timestamp')
    list_filter = ('transaction_status', 'timestamp')
    search_fields = ('invoice__recipient__username', 'phone_number', 'transaction_status')
    ordering = ('-timestamp',)
    
    fieldsets = (
        (None, {
            'fields': ('invoice', 'phone_number', 'amount')
        }),
        ('Transaction Details', {
            'fields': ('transaction_status', 'transaction_id', 'timestamp'),
            'classes': ('collapse',)  # This makes this section collapsible
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # If an object is being edited
            return ('timestamp',)  # Make the timestamp read-only
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request):
        return True  # Allow adding new transactions

    def has_change_permission(self, request, obj=None):
        return True  # Allow changing transactions

    def has_delete_permission(self, request, obj=None):
        return True  # Allow deleting transactions

# Register the TransactionAdmin with the Transaction model
admin.site.register(Transaction, TransactionAdmin)


@admin.register(RentInvoice)
class RentInvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "recipient",
        "property",
        "monthly_rent",
        "water_bill",
        "total_amount",
        "billing_period_start",
        "billing_period_end",
        "paid",
        "view_file",
    )
    readonly_fields = (
        "created_at",
        "total_amount",
        "water_consumption",
        "billing_period_start",  # Make this readonly
        "view_file",
    )

    fieldsets = (
        (
            "Invoice Details",
            {
                "fields": (
                    "recipient",
                    "property",
                    "monthly_rent",
                    "total_amount",
                    "paid",
                )
            },
        ),
        (
            "Water Usage Details",
            {
                "fields": (
                    "previous_water_reading",
                    "current_water_reading",
                    "water_consumption",
                    "water_bill",
                    "price_per_unit",
                )
            },
        ),
        (
            "Billing Period",
            {
                "fields": (
                    "billing_period_start",  # Keep it here as readonly
                    "billing_period_end",
                )
            },
        ),
        (
            "Dates and Arrears",
            {
                "fields": (
                    "created_at",
                    "reading_date",
                    "arrears",
                )
            },
        ),
        (
            "File Upload",
            {"fields": ("view_file",)},  # Display the file in a readonly format
        ),
    )

    def view_file(self, obj):
        """Display the uploaded invoice file."""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">View Invoice File</a>', obj.file.url
            )
        return "No file available"

    view_file.short_description = "Invoice File"

    def water_consumption(self, obj):
        """Calculate water consumption based on readings."""
        return obj.current_water_reading - obj.previous_water_reading

    water_consumption.short_description = "Water Consumption (m³)"


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "tenant",
        "property",
        "type",
        "status",
        "severity",
        "submitted_at",
    )
    readonly_fields = ("submitted_at", "completed_at", "view_media")

    fieldsets = (
        (
            "Request Details",
            {
                "fields": (
                    "tenant",
                    "property",
                    "type",
                    "description",
                    "status",
                    "severity",
                )
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "submitted_at",
                    "completed_at",
                )
            },
        ),
        ("Budget", {"fields": ("budget",)}),
        ("Media", {"fields": ("view_media",)}),  # Media is in a separate fieldset
    )

    def view_media(self, obj):
        """
        Display images and video in the admin panel, all media uneditable.
        """
        media_html = ""

        # Handle Images
        images = [obj.image1, obj.image2, obj.image3]
        for image in images:
            if image:
                media_html += f"""
                <div style="display: inline-block; margin: 5px;">
                    <img src="{image.url}" alt="Image" style="width: 100%; height: auto; object-fit: cover; border-radius: 8px;">
                </div>
                """

        # Handle Video
        if obj.video:
            media_html += f"""
            <div style="margin-top: 15px;">
                <video width="500" height="500" controls style="border-radius: 8px;">
                    <source src="{obj.video.url}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
            """

        return format_html(media_html) if media_html else "No media available"

    view_media.short_description = "Maintenance Media"


admin.site.register(Notification)


class VacateNoticeAdmin(admin.ModelAdmin):
    list_display = ("tenant", "notice_date", "vacate_date", "reason")
    list_filter = ("vacate_date",)
    search_fields = ("tenant__username",)

    def changelist_view(self, request, extra_context=None):
        # Query for vacate notices
        vacate_notices = VacateNotice.objects.all()
        extra_context = extra_context or {}
        extra_context["vacate_notices"] = vacate_notices
        return super(VacateNoticeAdmin, self).changelist_view(
            request, extra_context=extra_context
        )


admin.site.register(VacateNotice, VacateNoticeAdmin)

# Optionally, if you want to customize the admin display of each model,
# you can create custom ModelAdmins for each model, similar to the UserAdmin above.
