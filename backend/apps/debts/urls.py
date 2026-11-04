from django.urls import path

from .views import (
    CustomerDebtListCreateView,
    DebtDetailView,
)

urlpatterns = [
    path(
        "customers/<int:customer_id>/debts/",
        CustomerDebtListCreateView.as_view(),
        name="customer-debt-list-create",
    ),
    path(
        "debts/<int:debt_id>/",
        DebtDetailView.as_view(),
        name="debt-detail",
    ),
]