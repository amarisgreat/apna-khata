from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.customers.models import Customer

from .models import Payment
from .serializers import (
    PaymentWriteSerializer,
    PaymentReadSerializer,
)
from .services.payment_service import (
    create_payment,
    update_payment,
)


class CustomerPaymentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_customer(self, request, customer_id):
        return get_object_or_404(
            Customer,
            id=customer_id,
            shop=request.user.shop,
        )

    def get(self, request, customer_id):
        customer = self.get_customer(request, customer_id)

        payments = (
            Payment.objects
            .filter(customer=customer)
            .select_related(
                "customer",
                "created_by",
            )
            .prefetch_related(
                "allocations__debt",
            )
            .order_by("-paid_at", "-id")
        )

        serializer = PaymentReadSerializer(
            payments,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, customer_id):
        customer = self.get_customer(request, customer_id)

        serializer = PaymentWriteSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        payment = create_payment(
            customer=customer,
            created_by=request.user,
            amount=data["amount"],
            paid_at=data.get("paid_at"),
            note=data.get("note", ""),
        )

        payment = (
            Payment.objects
            .select_related(
                "customer",
                "created_by",
            )
            .prefetch_related(
                "allocations__debt",
            )
            .get(id=payment.id)
        )

        return Response(
            PaymentReadSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, payment_id):
        return get_object_or_404(
            Payment.objects
            .select_related(
                "customer",
                "created_by",
            )
            .prefetch_related(
                "allocations__debt",
            ),
            id=payment_id,
            customer__shop=request.user.shop,
        )

    def get(self, request, payment_id):
        payment = self.get_object(
            request,
            payment_id,
        )

        return Response(
            PaymentReadSerializer(payment).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, payment_id):
        payment = self.get_object(
            request,
            payment_id,
        )

        serializer = PaymentWriteSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        updated_payment = update_payment(
            payment=payment,
            data=dict(serializer.validated_data),
        )

        updated_payment = (
            Payment.objects
            .select_related(
                "customer",
                "created_by",
            )
            .prefetch_related(
                "allocations__debt",
            )
            .get(id=updated_payment.id)
        )

        return Response(
            PaymentReadSerializer(updated_payment).data,
            status=status.HTTP_200_OK,
        )