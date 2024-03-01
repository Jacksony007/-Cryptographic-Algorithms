from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterAccountView, AccountLoginView, AccountLogoutView

urlpatterns = [
    path("register/", RegisterAccountView.as_view(), name="register-account"),
    path("login/", AccountLoginView.as_view(), name="login-account"),
    path("token/generate_access/", TokenRefreshView.as_view(), name="generate-access-token"),
    path("logout/", AccountLogoutView.as_view(), name="logout-account"),
]