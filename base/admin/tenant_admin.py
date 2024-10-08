from unfold.admin import ModelAdmin
from django.contrib import admin
from base.models import *
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils.safestring import mark_safe



# Register the TenantProfileAdmin with the TenantProfile model
admin.site.register(TenantProfile)
