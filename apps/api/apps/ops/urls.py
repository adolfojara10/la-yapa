from django.urls import path

from . import views

app_name = "ops"

urlpatterns = [
    path("session", views.AdminSessionView.as_view(), name="session"),
    path("businesses", views.BusinessListView.as_view(), name="business-list"),
    path("businesses/<int:pk>", views.BusinessDetailView.as_view(), name="business-detail"),
    path(
        "businesses/<int:pk>/approve", views.ApproveBusinessView.as_view(), name="business-approve"
    ),
    path("businesses/<int:pk>/reject", views.RejectBusinessView.as_view(), name="business-reject"),
    path(
        "businesses/<int:pk>/request-more-info",
        views.RequestMoreInfoBusinessView.as_view(),
        name="business-request-more-info",
    ),
    path(
        "sales/business-accounts",
        views.CreateDraftBusinessAccountView.as_view(),
        name="sales-business-account-create",
    ),
    path(
        "sales/business-accounts/<int:pk>/send-setup-link",
        views.SendBusinessSetupLinkView.as_view(),
        name="sales-business-account-send-setup-link",
    ),
]
