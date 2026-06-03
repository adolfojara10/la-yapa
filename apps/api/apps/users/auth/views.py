"""Auth views — thin layer over serializers + services."""

from __future__ import annotations

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from . import serializers


class RegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.RegisterSerializer

    @method_decorator(ratelimit(key="ip", rate="20/h", block=True))
    def post(self, request):
        ser = self.serializer_class(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        payload = ser.save()
        return Response(payload, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.LoginSerializer

    @method_decorator(ratelimit(key="ip", rate="30/m", block=True))
    def post(self, request):
        ser = self.serializer_class(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        return Response(ser.to_response(), status=status.HTTP_200_OK)


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.GoogleAuthSerializer

    @method_decorator(ratelimit(key="ip", rate="30/m", block=True))
    def post(self, request):
        ser = self.serializer_class(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        return Response(ser.to_response(), status=status.HTTP_200_OK)


class AppleAuthView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.AppleAuthSerializer

    @method_decorator(ratelimit(key="ip", rate="30/m", block=True))
    def post(self, request):
        ser = self.serializer_class(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        return Response(ser.to_response(), status=status.HTTP_200_OK)


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.VerifyEmailSerializer

    @method_decorator(ratelimit(key="ip", rate="10/h", block=True))
    def post(self, request):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        return Response({"verified": True}, status=status.HTTP_200_OK)


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ResendVerificationSerializer

    # 1/min per IP+email keeps abuse low while letting legit users retry.
    @method_decorator(
        ratelimit(key="post:email", rate="1/m", block=True),
    )
    @method_decorator(
        ratelimit(key="ip", rate="20/h", block=True),
    )
    def post(self, request):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.maybe_send()
        # Always 202 — clients can't infer whether an email was actually sent.
        return Response({"ok": True}, status=status.HTTP_202_ACCEPTED)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ForgotPasswordSerializer

    @method_decorator(ratelimit(key="post:email", rate="3/h", block=True))
    @method_decorator(ratelimit(key="ip", rate="20/h", block=True))
    def post(self, request):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"ok": True}, status=status.HTTP_202_ACCEPTED)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ResetPasswordSerializer

    @method_decorator(ratelimit(key="ip", rate="20/h", block=True))
    def post(self, request):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"ok": True}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Blacklist the supplied refresh token. Access token is short-lived
    enough that we don't bother blacklisting it as well.

    AllowAny so a client that's already lost its access token (e.g. forced
    logout after a 401) can still revoke its refresh on the way out.
    """

    permission_classes = [AllowAny]
    serializer_class = serializers.LogoutSerializer

    def post(self, request):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(status=status.HTTP_205_RESET_CONTENT)
