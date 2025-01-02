from django.urls import include, path
from rest_framework import routers
from management.views import *

router = routers.DefaultRouter()


urlpatterns = [
    path("users/", CreateUserView.as_view(), name="create_user"),
    path("apartments/", ApartmentViewSet.as_view({"get": "list"}), name="create_user"),
    path("create-apartment/", create_apartment, name="create_apartment"),
    path("blocks/", BlockViewSet.as_view({"get": "list"}), name="create_user"),
    path("create-block/", create_block, name="create_block"),
    path("units/", UnitViewSet.as_view({"get": "list"}), name="create_user"),
    path("create-unit/", create_unit, name="create_unit"),
    path("assign-tenant/", assign_tenant, name="asign_tenant"),
    path("meter-readings/", MeterListView.as_view(), name="meter-readings"),
    path("update-reading/", meter_view, name="update-reading"),
    path("tenant-records/", AllTenantView.as_view({"get": "list"}), name="all_tenants"),
    path(
        "tenant-records/<int:pk>/",
        AllTenantView.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="tenant-detail",
    ),
    path("invoices/", UserInvoiceView.as_view(), name="create_invoice"),
    path("invoices/<str:pk>/", UserInvoiceView.as_view(), name="edit_invoice"),
    path(
        "landlord-profiles/",
        LandlordProfileViewSet.as_view({"get": "list"}),
        name="landlord",
    ),
    path(
        "landlord-profiles/<int:pk>/",
        LandlordProfileViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="landlord-detail",
    ),
    path("maintenance-requests/", maintenance_request_view, name="maintenance-request"),
]
