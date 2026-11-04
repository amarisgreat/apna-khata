from django.urls import path

from .views import (
    CustomerPaymentListCreateView,
    PaymentDetailView,
)

urlpatterns = [
    path(
        "customers/<int:customer_id>/payments/",
        CustomerPaymentListCreateView.as_view(),
        name="customer-payment-list-create",
    ),
    path(
        "payments/<int:payment_id>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),
]