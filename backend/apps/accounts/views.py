from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken

from .serializers import RegisterSerializer


class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        user = result["user"]
        shop = result["shop"]

        token = AccessToken.for_user(user)
        token["shop_id"] = shop.id

        return Response({
            "message": "Registration successful",
            "access": str(token),
            "user": {
                "id": user.id,
                "name": user.name,
                "phone": user.phone
            },
            "shop": {
                "id": shop.id,
                "name": shop.name
            }
        }, status=status.HTTP_201_CREATED)

    from django.contrib.auth import authenticate


class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        phone = request.data.get("phone")
        password = request.data.get("password")

        if not phone or not password:
            return Response(
                {"message": "Phone and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            request,
            phone=phone,
            password=password
        )

        if user is None:
            return Response(
                {"message": "Invalid phone or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token = AccessToken.for_user(user)
        token["shop_id"] = user.shop.id

        return Response({
            "message": "Login successful",
            "access": str(token),
            "user": {
                "id": user.id,
                "name": user.name,
                "phone": user.phone
            },
            "shop": {
                "id": user.shop.id,
                "name": user.shop.name
            }
        })