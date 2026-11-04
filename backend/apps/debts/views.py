from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.customers.models import Customer

from .models import Debt
from .serializers import DebtWriteSerializer, DebtReadSerializer
from .selectors.debt_queries import get_customer_debts
from .services.debt_service import create_debt, update_debt


class CustomerDebtListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_customer(self, request, customer_id):
        return get_object_or_404(
            Customer,
            id=customer_id,
            shop=request.user.shop,
        )

    def get(self, request, customer_id):
        customer = self.get_customer(request, customer_id)

        debts = get_customer_debts(customer)

        debt_status = request.query_params.get(
            "status",
            "ACTIVE",
        ).upper()

        if debt_status not in ["ACTIVE", "CLEARED", "ALL"]:
            raise ValidationError({
                "status": "Choose ACTIVE, CLEARED or ALL."
            })

        serialized_debts = DebtReadSerializer(
            debts,
            many=True,
        ).data

        if debt_status != "ALL":
            serialized_debts = [
                debt
                for debt in serialized_debts
                if debt["status"] == debt_status
            ]

        return Response(
            serialized_debts,
            status=status.HTTP_200_OK,
        )

    def post(self, request, customer_id):
        customer = self.get_customer(request, customer_id)

        serializer = DebtWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        debt = create_debt(
            customer=customer,
            created_by=request.user,
            created_at=data.get("created_at"),
            items=data["items"],
            note=data.get("note", ""),
        )

        debt = get_customer_debts(customer).get(id=debt.id)

        return Response(
            DebtReadSerializer(debt).data,
            status=status.HTTP_201_CREATED,
        )


class DebtDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, debt_id):
        return get_object_or_404(
            Debt.objects.filter(
                customer__shop=request.user.shop,
            ).select_related(
                "customer",
                "created_by",
            ).prefetch_related(
                "items",
                "allocations__payment",
            ),
            id=debt_id,
        )

    def get(self, request, debt_id):
        debt = self.get_object(request, debt_id)

        return Response(
            DebtReadSerializer(debt).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, debt_id):
        debt = self.get_object(request, debt_id)

        serializer = DebtWriteSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        updated_debt = update_debt(
            debt=debt,
            data=dict(serializer.validated_data),
        )

        updated_debt.refresh_from_db()

        updated_debt = self.get_object(request, debt_id)

        return Response(
            DebtReadSerializer(updated_debt).data,
            status=status.HTTP_200_OK,
        )