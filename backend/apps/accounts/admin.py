from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    ordering = ("-date_joined",)

    list_display = (
        "name",
        "phone",
        "is_active",
        "is_staff",
        "date_joined",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "name",
        "phone",
    )

    fieldsets = (
        (None, {
            "fields": ("phone", "password")
        }),

        ("Personal Information", {
            "fields": ("name",)
        }),

        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "phone",
                "name",
                "password1",
                "password2",
            ),
        }),
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
    )