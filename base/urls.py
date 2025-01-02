from django.urls import include, path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView

from base.views.users import *
from base.views.transactions import *
from base.views.tenants import *
from base.views.landlord import *


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
    #path("tenant-info/", TenantInfoView.as_view(), name="tenant-info"),
    path(
        "tenant-profile/",
        TenantProfileView.as_view(),
        name="tenant-profile-detail",
    ),
    path("maintenance-requests/", maintenance_request_view, name="maintenance-request"),

    # path(
    #     "vacate-notices/", VacateNoticeCreateView.as_view(), name="vacate-notice-create"
    # ),
    path("initiate-payment/", index, name="initiate_payment"),

]
