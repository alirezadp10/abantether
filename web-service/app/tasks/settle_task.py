from rq import Queue
from app.models import ExchangeTransaction, ExchangerRequestLog, Order, Transaction, UserWallet
from app.redis_client import RedisClient
import requests
import time
from collections import defaultdict
from django.db import transaction as db_transaction
from decimal import Decimal


def update_user_wallets_and_orders(orders, status):
    """Updates user wallets and order statuses"""
    user_ids = orders.values_list('user_id', flat=True).distinct()

    user_wallets = UserWallet.objects.select_for_update().filter(user_id__in=user_ids)

    total_sum_of_users = defaultdict(Decimal)
    for order in orders:
        total_sum_of_users[order.user_id] += order.amount * order.count

    for user_wallet in user_wallets:
        user_wallet.locked_balance -= total_sum_of_users[user_wallet.user_id]
        if status == 'Completed':
            user_wallet.balance -= total_sum_of_users[user_wallet.user_id]
        user_wallet.save()

    orders.update(status=status)


def create_reverse_transactions(orders):
    """Creates reverse transactions in case of failure"""
    transactions = Transaction.objects.filter(id__in=orders.values_list('transaction_id', flat=True))
    reverse_transactions_data = [
        Transaction(
            user=transaction.user,
            type="Credit",
            amount=transaction.amount
        )
        for transaction in transactions
    ]
    Transaction.objects.bulk_create(reverse_transactions_data)


def settle(exchange_transaction_id: int, currency: str):
    exchange_transaction = ExchangeTransaction.objects.get(id=exchange_transaction_id)
    exchange_transaction.try_count += 1
    exchange_transaction.save()

    request_data = {
        'amount': exchange_transaction.amount,
        'currency': currency,
    }

    exchanger_request_log = ExchangerRequestLog.objects.create(
        request=str(request_data),
        exchange_transaction=exchange_transaction
    )

    try:
        response = requests.post(exchange_transaction.exchanger.api_url, json=request_data, timeout=60)

        exchanger_request_log.response = str(response)
        exchanger_request_log.save()

        if response.status_code == 200:
            with db_transaction.atomic():
                orders = Order.objects.filter(exchange_transaction=exchange_transaction)
                update_user_wallets_and_orders(orders, status="Completed")

                exchange_transaction.status = "Completed"
                exchange_transaction.save()

        else:
            raise Exception("Exchanger request failed")

    except Exception as e:
        if exchange_transaction.try_count < 3:
            time.sleep(60)
            queue = Queue(connection=RedisClient().client)
            queue.enqueue(settle, exchange_transaction, currency)
        else:
            with db_transaction.atomic():
                orders = Order.objects.filter(exchange_transaction=exchange_transaction)
                update_user_wallets_and_orders(orders, status="Failed")

                create_reverse_transactions(orders)

                exchange_transaction.status = "Failed"
                exchange_transaction.save()
                # OR we can change the exchanger and send transaction with them
