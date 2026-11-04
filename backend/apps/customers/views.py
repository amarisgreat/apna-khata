from django.db.models import Q

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Customer
from .serializers import CustomerSerializer
from .selectors.customer_queries import get_shop_customers
from .services.customer_service import (
    create_customer,
    update_customer,
    change_customer_status,
)


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        return get_shop_customers(self.request.user.shop)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        if self.action == "list":

            # ------------------------------------------
            # Customer status filter
            # Default: ACTIVE
            # ------------------------------------------
            customer_status = self.request.query_params.get("status")

            if customer_status:
                customer_status = customer_status.upper()

                if customer_status not in Customer.Status.values:
                    raise ValidationError({
                        "status": "Choose ACTIVE or INACTIVE."
                    })

                queryset = queryset.filter(status=customer_status)

            else:
                queryset = queryset.filter(
                    status=Customer.Status.ACTIVE
                )

            # ------------------------------------------
            # Search by customer name or phone
            # ------------------------------------------
            search = self.request.query_params.get("search")

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search)
                    | Q(phone__icontains=search)
                )

            # ------------------------------------------
            # Filter by tag
            # ------------------------------------------
            tag = self.request.query_params.get("tag")

            if tag:
                queryset = queryset.filter(
                    tags__name__iexact=tag
                ).distinct()

            # ------------------------------------------
            # Filter by balance
            # ------------------------------------------
            balance_filter = self.request.query_params.get("balance")

            if balance_filter:
                balance_filter = balance_filter.lower()

                if balance_filter == "outstanding":
                    queryset = queryset.filter(
                        outstanding_balance__gt=0
                    )

                elif balance_filter == "overdue":
                    queryset = queryset.filter(
                        has_overdue_debt=True
                    )

                elif balance_filter == "cleared":
                    queryset = queryset.filter(
                        total_debt__gt=0,
                        outstanding_balance=0,
                    )

                else:
                    raise ValidationError({
                        "balance": (
                            "Choose outstanding, overdue or cleared."
                        )
                    })

            # ------------------------------------------
            # Customer sorting
            # ------------------------------------------
            sort = self.request.query_params.get("sort", "name")

            if sort == "name":
                queryset = queryset.order_by("name", "id")

            elif sort == "balance":
                queryset = queryset.order_by(
                    "-outstanding_balance",
                    "name",
                    "id",
                )

            elif sort == "last_activity":
                queryset = queryset.order_by(
                    "-last_activity",
                    "name",
                    "id",
                )

            else:
                raise ValidationError({
                    "sort": (
                        "Choose name, balance or last_activity."
                    )
                })

        return queryset

    # ==============================================
    # CREATE CUSTOMER
    # ==============================================
    def perform_create(self, serializer):
        self.created_customer = create_customer(
            shop=self.request.user.shop,
            data=dict(serializer.validated_data),
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response(
            self.get_serializer(self.created_customer).data,
            status=status.HTTP_201_CREATED,
        )

    # ==============================================
    # UPDATE CUSTOMER
    # ==============================================
    def perform_update(self, serializer):
        self.updated_customer = update_customer(
            customer=self.get_object(),
            data=dict(serializer.validated_data),
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        return Response(
            self.get_serializer(self.updated_customer).data,
            status=status.HTTP_200_OK,
        )

    # ==============================================
    # CHANGE CUSTOMER STATUS
    # ==============================================
    @action(detail=True, methods=["patch"])
    def status(self, request, pk=None):
        customer = self.get_object()

        new_status = request.data.get("status", "").upper()

        if new_status not in Customer.Status.values:
            raise ValidationError({
                "status": "Choose ACTIVE or INACTIVE."
            })

        change_customer_status(
            customer=customer,
            status=new_status,
        )

        return Response(
            {
                "message": "Customer status updated.",
                "status": new_status,
            },
            status=status.HTTP_200_OK,
        )