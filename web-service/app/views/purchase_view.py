from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from app.redis_client import RedisClient
from app.serializers import PurchaseSerializer
from app.models import UserWallet, Order, CryptoCurrency, Transaction
from django.db import transaction


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def purchase(request):
    serializer = PurchaseSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    count = serializer.validated_data.get('count')
    name = serializer.validated_data.get('name').upper()

    try:
        with transaction.atomic():
            crypto_currency = CryptoCurrency.objects.get(symbol=name)

            total_amount = crypto_currency.price * count

            user_wallet = UserWallet.objects.select_for_update().get(user_id=request.user.id)

            if user_wallet.balance < total_amount + user_wallet.locked_balance:
                raise ValueError("Insufficient balance")

            user_wallet.locked_balance += total_amount
            user_wallet.save()

            trx = Transaction.objects.create(
                user=request.user,
                type=dict(Transaction.TRANSACTION_TYPES).get("debit"),
                amount=total_amount
            )

            Order.objects.create(
                user=request.user,
                crypto_currency=crypto_currency,
                transaction=trx,
                count=count,
                amount=crypto_currency.price
            )

        return Response({"message": "Your order has been registered"}, status=status.HTTP_201_CREATED)

    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except CryptoCurrency.DoesNotExist:
        return Response({"error": "CryptoCurrency not found"}, status=status.HTTP_404_NOT_FOUND)
    except UserWallet.DoesNotExist:
        return Response({"error": "User wallet not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
