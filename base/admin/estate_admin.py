from unfold.admin import ModelAdmin
from django.contrib import admin
from base.models import *
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html


# Water Price Admin
class WaterPriceAdmin(ModelAdmin):
    list_display = ("price_per_unit", "effective_date")
    search_fields = ("price_per_unit",)
    ordering = ("-effective_date",)


admin.site.register(WaterPrice, WaterPriceAdmin)


@admin.register(WaterMeterReading)
class WaterMeterReadingAdmin(ModelAdmin):
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


@admin.register(Property)
class PropertyAdmin(ModelAdmin):

    list_filter = ("estate", "block")
    list_display = (
        "estate",
        "block",
        "unit",
        "rent_price",
        "available",
        "landlord",
    )

    readonly_fields = ("created_at",  "view_image")

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "landlord",
                    "estate",
                    "block",
                    "unit",
                    "description",
                    "rent_price",
                    "available",
                    "image1",  # Make the image field editable
                    "view_image",  # To display the image as a card
                )
            },
        ),
       
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                   
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
                obj.image.url,
            )
        return "No image available"

    view_image.short_description = "Property Image"

    def estate_grouped(self, obj):
        return obj.estate

    estate_grouped.admin_order_field = (
        "estate"  # Allows sorting by estate in the admin panel
    )
    estate_grouped.short_description = "estate"


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(ModelAdmin):
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
        images = [obj.image1]
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
