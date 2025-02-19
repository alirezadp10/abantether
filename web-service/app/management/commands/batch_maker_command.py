from django.core.management.base import BaseCommand
from collections import defaultdict
from django.db import transaction
from django.conf import settings
from app.models import Order, ExchangeTransaction, Exchanger, OrderExchangeTransaction
from app.redis_client import RedisClient
from rq import Queue
from app.tasks import settle


class Command(BaseCommand):
    help = "This command will make a batch of orders."

    def __init__(self):
        super().__init__()
        self.redis_client = RedisClient()
        self.min_batch_amount = getattr(settings, "MIN_BATCH_AMOUNT", 10)  # مقدار دیفالت ۱۰ در نظر گرفته می‌شود

    def handle(self, *args, **options):
        orders = Order.objects.select_related('crypto_currency').filter(status="pending")

        orders_based_symbol = defaultdict(list)
        for order in orders:
            orders_based_symbol[order.crypto_currency.symbol].append(order)

        for symbol, orders in orders_based_symbol.items():
            sum_amount = sum(order.amount * order.count for order in orders)
            order_ids = [order.id for order in orders]

            if sum_amount >= self.min_batch_amount:
                exchange_transaction = self.create_exchange_transaction(orders, order_ids, sum_amount)
                queue = Queue(connection=self.redis_client.client, name=symbol)
                queue.enqueue(settle, exchange_transaction.id, symbol)

    def create_exchange_transaction(self, orders, order_ids, amount):
        with transaction.atomic():
            Order.objects.filter(id__in=order_ids).update(status="processing")

            exchanger = Exchanger.objects.first()
            if not exchanger:
                raise ValueError("No exchanger found")

            exchange_transaction = ExchangeTransaction.objects.create(exchanger=exchanger, amount=amount)

            order_exchange_transactions = [
                OrderExchangeTransaction(order=order, exchange_transaction=exchange_transaction) for order in orders
            ]
            OrderExchangeTransaction.objects.bulk_create(order_exchange_transactions)

        return exchange_transaction
