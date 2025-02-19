from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from app.models import UserWallet
from app.serializers import SignupSerializer
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(["POST"])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        UserWallet.objects.create(user=user)

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "User created successfully",
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)