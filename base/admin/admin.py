from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib import admin
from base.models import *
from django.utils.translation import gettext_lazy as _

# Register the TransactionAdmin with the Transaction model



admin.site.register(MaintenanceRequest)

#admin.site.register(VacateNotice, ModelAdmin)

# Optionally, if you want to customize the admin display of each model,
# you can create custom ModelAdmins for each model, similar to the UserAdmin above.
