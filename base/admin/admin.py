from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.contrib import admin
from base.models import *
from django.utils.translation import gettext_lazy as _


class UserAdmin(BaseUserAdmin, ModelAdmin):

    # Specify fields to display in the user list view
    list_display = (
        "email",
        "first_name",
        "last_name",
        "user_type",
        "is_active",
        "is_staff",
    )
    list_filter = ("user_type", "is_active", "is_staff")

    # Enable search by email, first name, and last name
    search_fields = ("email", "first_name", "last_name")

    # Define the form layout using fieldsets
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal Info"),
            {"fields": ("first_name", "last_name", "phone", "profile_picture")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("User Type"), {"fields": ("user_type",)}),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    # Fieldsets for the form used when creating a new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "user_type",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    ordering = ("email",)

    # Enable filter horizontal for groups and user permissions
    filter_horizontal = ("groups", "user_permissions")


# Register the custom User admin
admin.site.register(User, UserAdmin)


# Register the TransactionAdmin with the Transaction model

admin.site.register(Transaction)
admin.site.register(WaterBillInvoice)
admin.site.register(RentInvoice)


class VacateNoticeAdmin(ModelAdmin):
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
