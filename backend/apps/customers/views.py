from django.db.models import Q

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

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
        """
        Return customers belonging only to the authenticated user's shop.

        Do not apply the ACTIVE filter here because individual operations
        must also be able to retrieve inactive customers.
        """
        return get_shop_customers(
            self.request.user.shop
        )

    def filter_queryset(self, queryset):
        """
        Apply search, status and tag filters to customer listings.
        """

        queryset = super().filter_queryset(queryset)

        if self.action == "list":

            # Default: show only active customers.
            customer_status = self.request.query_params.get("status")

            if customer_status:
                customer_status = customer_status.upper()

                if customer_status not in Customer.Status.values:
                    raise ValidationError({
                        "status": "Choose ACTIVE or INACTIVE."
                    })

                queryset = queryset.filter(
                    status=customer_status
                )

            else:
                queryset = queryset.filter(
                    status=Customer.Status.ACTIVE
                )

            # Filter by customer tag.
            tag = self.request.query_params.get("tag")

            if tag:
                queryset = queryset.filter(
                    tags__name__iexact=tag
                ).distinct()

            # Search by customer name or phone.
            search = self.request.query_params.get("search")

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(phone__icontains=search)
                )

        return queryset

    def perform_create(self, serializer):
        """
        Create a customer under the authenticated user's shop.
        """

        self.created_customer = create_customer(
            shop=self.request.user.shop,
            data=dict(serializer.validated_data)
        )

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response(
            self.get_serializer(self.created_customer).data,
            status=status.HTTP_201_CREATED
        )

    def perform_update(self, serializer):
        """
        Update customer details through the service layer.
        """

        self.updated_customer = update_customer(
            customer=self.get_object(),
            data=dict(serializer.validated_data)
        )

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )

        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        return Response(
            self.get_serializer(self.updated_customer).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["patch"])
    def status(self, request, pk=None):
        """
        Activate or deactivate a customer.

        Inactive customers can still be retrieved and reactivated.
        """

        customer = self.get_object()

        new_status = request.data.get("status", "").upper()

        if new_status not in Customer.Status.values:
            raise ValidationError({
                "status": "Choose ACTIVE or INACTIVE."
            })

        change_customer_status(
            customer=customer,
            status=new_status
        )

        return Response({
            "message": "Customer status updated.",
            "status": customer.status
        }, status=status.HTTP_200_OK)
