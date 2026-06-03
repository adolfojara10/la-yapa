"""Auth endpoint serializers."""

from __future__ import annotations

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


def _tokens_for_user(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class _UserPayloadMixin:
    """Shared 'user' block embedded in register/login/social responses."""

    def user_payload(self, user: User) -> dict:
        from apps.users.api.serializers import MeSerializer  # local import = avoid cycle

        return MeSerializer(user, context=self.context).data  # type: ignore[attr-defined]


class RegisterSerializer(serializers.Serializer, _UserPayloadMixin):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=[
            (User.Role.CONSUMER, "consumer"),
            (User.Role.BUSINESS_OWNER, "business_owner"),
        ],
        default=User.Role.CONSUMER,
    )
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=80)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=80)

    def validate_email(self, value: str) -> str:
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data: dict) -> dict:
        from .services.registration import register_email_user

        result = register_email_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data["role"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return {"user": self.user_payload(result.user), "tokens": _tokens_for_user(result.user)}


class LoginSerializer(serializers.Serializer, _UserPayloadMixin):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        email = attrs["email"].strip().lower()
        request = self.context.get("request")
        user = authenticate(request=request, username=email, password=attrs["password"])
        if user is None:
            raise serializers.ValidationError(
                {"detail": "Invalid credentials."}, code="invalid_credentials"
            )
        if not user.is_active:
            raise serializers.ValidationError({"detail": "Account is disabled."}, code="inactive")
        attrs["user"] = user
        return attrs

    def to_response(self) -> dict:
        user = self.validated_data["user"]
        return {"user": self.user_payload(user), "tokens": _tokens_for_user(user)}


class GoogleAuthSerializer(serializers.Serializer, _UserPayloadMixin):
    id_token = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        from .services.google import GoogleAuthError, verify_id_token

        try:
            profile = verify_id_token(attrs["id_token"])
        except GoogleAuthError as exc:
            raise serializers.ValidationError(
                {"id_token": str(exc)}, code="invalid_id_token"
            ) from exc
        attrs["profile"] = profile
        return attrs

    def to_response(self) -> dict:
        from allauth.socialaccount.models import SocialAccount

        from .services.registration import get_or_create_social_user

        profile = self.validated_data["profile"]
        result = get_or_create_social_user(
            email=profile.email,
            first_name=profile.first_name,
            last_name=profile.last_name,
            email_verified=True,
        )
        SocialAccount.objects.get_or_create(
            provider="google",
            uid=profile.sub,
            defaults={"user": result.user, "extra_data": {"email": profile.email}},
        )
        return {"user": self.user_payload(result.user), "tokens": _tokens_for_user(result.user)}


class AppleAuthSerializer(serializers.Serializer, _UserPayloadMixin):
    identity_token = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=80)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=80)

    def validate(self, attrs: dict) -> dict:
        from .services.apple import AppleAuthError, verify_identity_token

        try:
            profile = verify_identity_token(attrs["identity_token"])
        except AppleAuthError as exc:
            raise serializers.ValidationError(
                {"identity_token": str(exc)}, code="invalid_identity_token"
            ) from exc
        attrs["profile"] = profile
        return attrs

    def to_response(self) -> dict:
        from allauth.socialaccount.models import SocialAccount

        from .services.registration import get_or_create_social_user

        profile = self.validated_data["profile"]
        # On repeat Apple sign-ins, `email` may be empty in the token — look up
        # by SocialAccount.uid first; only fall back to creating a new user
        # when we genuinely have an email.
        existing = SocialAccount.objects.filter(provider="apple", uid=profile.sub).first()
        if existing is not None:
            user = existing.user
        else:
            if not profile.email:
                raise serializers.ValidationError(
                    {"identity_token": "Apple did not return an email and no prior account exists."}
                )
            result = get_or_create_social_user(
                email=profile.email,
                first_name=self.validated_data.get("first_name", ""),
                last_name=self.validated_data.get("last_name", ""),
                email_verified=profile.email_verified,
            )
            user = result.user
            SocialAccount.objects.create(
                provider="apple",
                uid=profile.sub,
                user=user,
                extra_data={"email": profile.email},
            )
        return {"user": self.user_payload(user), "tokens": _tokens_for_user(user)}


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs: dict) -> dict:
        from .services import email_otp

        email = attrs["email"].strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Don't leak account existence; return the generic "invalid" reason.
            raise serializers.ValidationError({"code": "invalid"}, code="invalid_code") from None
        result = email_otp.verify(user, attrs["code"])
        if not result.ok:
            raise serializers.ValidationError({"code": result.reason}, code=result.reason)
        attrs["user"] = user
        return attrs


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs: dict) -> dict:
        # Silent on lookup — same anti-enumeration stance as forgot-password.
        attrs["email"] = attrs["email"].strip().lower()
        return attrs

    def maybe_send(self) -> None:
        from .services import email_otp

        try:
            user = User.objects.get(email__iexact=self.validated_data["email"])
        except User.DoesNotExist:
            return
        if user.is_email_verified:
            return
        email_otp.issue_and_send(user)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self, **kwargs) -> None:
        from .services.password_reset import request_reset

        request_reset(self.validated_data["email"])


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def save(self, **kwargs) -> User:
        from .services.password_reset import ResetError, perform_reset

        try:
            user = perform_reset(
                raw_token=self.validated_data["token"],
                new_password=self.validated_data["new_password"],
            )
        except ResetError as exc:
            raise serializers.ValidationError(
                {"token" if exc.reason == "invalid_token" else "new_password": exc.reason},
                code=exc.reason,
            ) from exc
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def save(self, **kwargs) -> None:
        from rest_framework_simplejwt.exceptions import TokenError
        from rest_framework_simplejwt.tokens import RefreshToken as RT

        try:
            RT(self.validated_data["refresh"]).blacklist()
        except TokenError:
            # Idempotent: already-blacklisted / expired tokens are a no-op.
            return
