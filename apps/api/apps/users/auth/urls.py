"""URLs for /api/v1/auth/*."""

from django.urls import path

from . import views

app_name = "auth"

urlpatterns = [
    path("register", views.RegisterView.as_view(), name="register"),
    path("login", views.LoginView.as_view(), name="login"),
    path("refresh", views.RefreshView.as_view(), name="refresh"),
    path("google", views.GoogleAuthView.as_view(), name="google"),
    path("apple", views.AppleAuthView.as_view(), name="apple"),
    path("verify-email", views.VerifyEmailView.as_view(), name="verify-email"),
    path(
        "verify-email/resend",
        views.ResendVerificationView.as_view(),
        name="verify-email-resend",
    ),
    path("forgot-password", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password", views.ResetPasswordView.as_view(), name="reset-password"),
    path("logout", views.LogoutView.as_view(), name="logout"),
]
