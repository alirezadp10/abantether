from django.test import TestCase
from unittest.mock import patch, MagicMock, ANY
from django.conf import settings
from django.core.management import call_command
from app.models import Order, ExchangeTransaction, Exchanger, OrderExchangeTransaction, CryptoCurrency, User, \
    Transaction
from app.management.commands.batch_maker_command import Command
from app.redis_client import RedisClient
from app.tasks import settle


class BatchOrdersTest(TestCase):
    def setUp(self):
        self.command = Command()
        self.user = User.objects.create(username="testuser")
        self.crypto_currency = CryptoCurrency.objects.create(symbol="BTC", name="Bitcoin", price=50000)
        self.tether = CryptoCurrency.objects.create(symbol="TETHER", name="Tether", price=1000)
        self.ethereum = CryptoCurrency.objects.create(symbol="ETH", name="Ethereum", price=3000)
        self.exchanger = Exchanger.objects.create(name="Test Exchanger", api_url="https://api.test.com")
        self.redis_client_mock = MagicMock()
        self.command.redis_client = self.redis_client_mock
        self.transaction = Transaction.objects.create(user=self.user, amount=100, type="credit")
        settings.MIN_BATCH_AMOUNT = 10

    def test_successfully_creating_exchange_transaction(self):
        order1 = Order.objects.create(transaction=self.transaction, user=self.user,
                                      crypto_currency=self.crypto_currency, amount=5, count=1,
                                      status='pending')
        order2 = Order.objects.create(transaction=self.transaction, user=self.user,
                                      crypto_currency=self.crypto_currency, amount=6, count=1,
                                      status='pending')
        orders = [order1, order2]

        exchange_transaction = self.command.create_exchange_transaction(orders, [order1.id, order2.id], 11)

        self.assertEqual(ExchangeTransaction.objects.count(), 1)
        self.assertEqual(exchange_transaction.amount, 11)
        self.assertEqual(OrderExchangeTransaction.objects.count(), 2)
        self.assertEqual(Order.objects.get(id=order1.id).status, 'processing')
        self.assertEqual(Order.objects.get(id=order2.id).status, 'processing')

    @patch('app.redis_client.RedisClient')
    @patch('rq.Queue.enqueue')
    def test_successful_batch_processing_and_enqueueing(self, enqueue_mock, redis_client_mock: RedisClient):
        redis_client_instance = MagicMock()
        redis_client_mock.return_value = redis_client_instance

        enqueue_mock.return_value = None

        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=5,
                             count=2,
                             status='pending')
        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=3,
                             count=2,
                             status='pending')

        call_command('batch_maker_command')

        enqueue_mock.assert_called_once_with(settle, ANY, ANY)

    def test_raises_error_when_no_exchanger_found(self):
        self.exchanger.delete()
        order = Order.objects.create(transaction=self.transaction,
                                     user=self.user,
                                     crypto_currency=self.crypto_currency,
                                     amount=5,
                                     count=2,
                                     status='pending')

        with self.assertRaises(ValueError) as context:
            self.command.create_exchange_transaction([order], [order.id], 10)
        self.assertEqual(str(context.exception), "No exchanger found")

    def test_no_exchange_transaction_when_orders_below_min_batch_amount(self):
        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=3,
                             count=1,
                             status='pending')
        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=4,
                             count=1,
                             status='pending')
        call_command('batch_maker_command')

        self.assertEqual(ExchangeTransaction.objects.count(), 0)

    def test_creating_exchange_transaction_when_orders_above_min_batch_amount(self):
        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=6,
                             count=1,
                             status='pending')
        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=7,
                             count=1,
                             status='pending')

        call_command('batch_maker_command')

        self.assertEqual(ExchangeTransaction.objects.count(), 1)

    def test_batch_processing_for_multiple_orders_with_same_symbol(self):
        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=3,
                             count=1,
                             status='pending')
        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=4,
                             count=1,
                             status='pending')
        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=5,
                             count=1,
                             status='pending')

        call_command('batch_maker_command')

        self.assertEqual(ExchangeTransaction.objects.count(), 1)

    def test_batch_processing_with_partial_orders_in_processing_status(self):
        order1 = Order.objects.create(transaction=self.transaction,
                                      user=self.user,
                                      crypto_currency=self.crypto_currency,
                                      amount=5, count=1,
                                      status='pending')
        order2 = Order.objects.create(transaction=self.transaction,
                                      user=self.user,
                                      crypto_currency=self.crypto_currency,
                                      amount=6, count=1,
                                      status='processing')
        orders = [order1, order2]

        self.command.create_exchange_transaction(orders, [order1.id, order2.id], 11)

        self.assertEqual(ExchangeTransaction.objects.count(), 1)
        self.assertEqual(Order.objects.get(id=order1.id).status, 'processing')
        self.assertEqual(Order.objects.get(id=order2.id).status, 'processing')

    def test_batch_processing_with_mixed_order_amounts(self):
        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=3,
                             count=1,
                             status='pending')
        Order.objects.create(transaction=self.transaction,
                             user=self.user,
                             crypto_currency=self.crypto_currency,
                             amount=8,
                             count=1,
                             status='pending')

        call_command('batch_maker_command')

        self.assertEqual(ExchangeTransaction.objects.count(), 1)

    @patch('rq.Queue.enqueue')
    def test_orders_with_different_symbols_in_different_queues(self, enqueue_mock):
        Order.objects.create(transaction=self.transaction, user=self.user,
                             crypto_currency=self.tether, amount=5000, count=1, status='pending')
        Order.objects.create(transaction=self.transaction, user=self.user,
                             crypto_currency=self.ethereum, amount=6000, count=1, status='pending')

        call_command('batch_maker_command')

        enqueue_mock.assert_any_call(settle, 1, 'TETHER')
        enqueue_mock.assert_any_call(settle, 2, 'ETH')

        self.assertEqual(enqueue_mock.call_count, 2)
