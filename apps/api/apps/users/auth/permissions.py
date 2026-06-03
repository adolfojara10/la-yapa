"""Role-based DRF permissions.

These are deliberately separate from `IsAuthenticated` so views can compose
them: `permission_classes = [IsAuthenticated, ConsumerOnly]` reads cleanly
in code review even though the role check implies authentication.

Downstream apps (bags, orders, businesses, sales, ads) import these to gate
their endpoints; keeping them in one place avoids a sprinkle of bespoke
`request.user.role == "consumer"` checks across the codebase.
"""

from __future__ import annotations

from rest_framework import permissions

from apps.users.models import User


class _RolePermission(permissions.BasePermission):
    role: str = ""
    message = "Your account role is not allowed to access this resource."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "role", None) == self.role)


class ConsumerOnly(_RolePermission):
    role = User.Role.CONSUMER


class BusinessOwnerOnly(_RolePermission):
    role = User.Role.BUSINESS_OWNER


class AdminOnly(_RolePermission):
    role = User.Role.ADMIN


class SalesRepOnly(_RolePermission):
    role = User.Role.SALES_REP


class IsEmailVerified(permissions.BasePermission):
    """Gate that mirrors the mobile routing guard: lets unverified users in
    only enough to call `/auth/verify-email/*` and read their own profile.
    Apply at the viewset level for anything that mutates user-facing data."""

    message = "Email not verified."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "is_email_verified", False))
