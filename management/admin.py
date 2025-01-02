from django.contrib import admin
from management.models import *

# Register your models here.
admin.site.register(Apartment)
admin.site.register(Block)
admin.site.register(Unit)
admin.site.register(Tenant)
admin.site.register(WaterUnitPrice)
admin.site.register(BillItems)
admin.site.register(UserInvoice)
admin.site.register(WaterMeter)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    # Define fields to display in the admin list view
    list_display = (
        "email",
        "first_name",
        "last_name",
        "user_type",
        "is_active",
        "is_staff",
    )
    list_filter = ("user_type", "is_active", "is_staff")  # Filters for the right sidebar

    # Fieldsets for user detail/edit view
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Information", {"fields": ("first_name", "last_name", "phone", "profile_picture")}),
        ("Permissions", {"fields": ("user_type", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login",)}),
    )

    # Fieldsets for the add user form
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "phone",
                    "profile_picture",
                    "user_type",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    # Set email as the identifier in the admin search
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("email",)  # Default ordering in the admin list view
    filter_horizontal = ("groups", "user_permissions")  # Permissions selector widget

# Register the custom User model with the admin site
admin.site.register(User, UserAdmin)


