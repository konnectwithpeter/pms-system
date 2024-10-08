from django.urls import include, path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView

from base.views.users import *
from base.views.transactions import *
from base.views.tenants import *
from base.views.landlord import *
from base.views.admin_views import *

router = routers.DefaultRouter()


urlpatterns = [
    path("token/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "request-reset-email/",
        RequestPasswordResetEmail.as_view(),
        name="request-reset-email",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        PasswordTokenCheckAPI.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "password-reset-complete",
        SetNewPasswordAPIView.as_view(),
        name="password-reset-complete",
    ),
    path("tenant-info/", TenantInfoView.as_view(), name="tenant-info"),
    path(
        "tenant-profile/",
        TenantProfileDetailView.as_view(),
        name="tenant-profile-detail",
    ),
    path(
        "vacate-notices/", VacateNoticeCreateView.as_view(), name="vacate-notice-create"
    ),
    path("initiate-payment/", index, name="initiate_payment"),
    path("properties/", property_list_create, name="listed-properties"),
    path("maintenance-requests/", maintenance_request_view, name="maintenance-request"),
    path(
        "notifications/",
        NotificationViewSet.as_view({"get": "list"}),
        name="notifications",
    ),
    path(
        "notifications-edit/",
        mark_notification_as_read,
        name="mark-notification-as-read",
    ),
    path("landlord/", landlord_dashboard, name="landlord-dashboard"),
    path("admin/properties/", AdminPropertyView.as_view(), name="admin-properties"),
    ##################
    # Admin dashboard##
    ##################
    path("admin/estates/", EstateListView.as_view(), name="estate-list"),
    path(
        "admin/maintenance-requests/",
        MaintenanceRequestListView.as_view(),
        name="maintenance-requests",
    ),
    path(
        "admin/meter-readings/",
        MeterReadingListView.as_view(),
        name="meter-readings",
    ),
    path("admin/tenants/", TenantProfileView.as_view(), name="tenant-list"),
    path('admin/create-tenant/', create_tenant, name='tenant-create'),
    path('admin/create-estate/',create_property , name='create-estate'),
]
