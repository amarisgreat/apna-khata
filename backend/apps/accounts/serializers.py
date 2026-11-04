import re

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.services.registration import register_shopkeeper


class RegisterSerializer(serializers.Serializer):

    name = serializers.CharField(max_length=150)

    shop_name = serializers.CharField(max_length=200)

    phone = serializers.CharField(max_length=10)

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    def validate_phone(self, value):
        if not re.fullmatch(r"[6-9]\d{9}", value):
            raise serializers.ValidationError(
                "Enter a valid 10-digit Indian mobile number."
            )

        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "This phone number is already registered."
            )

        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user, shop = register_shopkeeper(**validated_data)

        return {
            "user": user,
            "shop": shop
        }