from django.test import TestCase
from unittest.mock import patch, MagicMock
from app.tasks import settle
import requests
from django.contrib.auth.models import User
from app.models import (
    Order, OrderExchangeTransaction, ExchangeTransaction, Exchanger, ExchangerRequestLog, UserWallet,
    Transaction, CryptoCurrency
)


class SettleTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="testuser"
        )
        self.exchanger = Exchanger.objects.create(
            name="Test Exchanger", api_url="https://api.test.com"
        )
        self.crypto_currency = CryptoCurrency.objects.create(
            symbol="BTC", name="Bitcoin", price=50000
        )
        self.wallet = UserWallet.objects.create(
            user=self.user, balance=1000, locked_balance=500
        )
        self.transaction = Transaction.objects.create(
            user=self.user, amount=200, type="Debit"
        )
        self.order = Order.objects.create(
            transaction=self.transaction, user=self.user, crypto_currency=self.crypto_currency,
            amount=50, count=4, status="Pending"
        )
        self.exchange_transaction = ExchangeTransaction.objects.create(
            exchanger=self.exchanger, amount=500, status="Pending"
        )
        self.order_exchange_transaction = OrderExchangeTransaction.objects.create(
            exchange_transaction=self.exchange_transaction, order=self.order
        )

    @patch('requests.post')
    def test_settle_successful(self, mock_post):
        # Mocking successful response from the exchange API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call the settle task
        settle(self.exchange_transaction.id, self.crypto_currency.symbol)

        # Check that the exchange transaction status is updated to 'Completed'
        self.exchange_transaction.refresh_from_db()
        self.assertEqual(self.exchange_transaction.status, "Completed")

        # Check that the wallet balance was updated
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 800)
        self.assertEqual(self.wallet.locked_balance, 300)

        # Check that the order status is updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Completed")

    @patch('requests.post')
    def test_settle_failure_retries(self, mock_post):
        # Mocking a failed response from the exchange API
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Simulating a retry mechanism
        settle(self.exchange_transaction.id, self.crypto_currency.symbol)

        # Ensure the try_count is incremented
        self.exchange_transaction.refresh_from_db()
        self.assertEqual(self.exchange_transaction.try_count, 1)

    @patch('requests.post')
    def test_settle_failed_after_retries(self, mock_post):
        # Mocking a failed response after 3 attempts
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Simulating a failure after 3 attempts
        for _ in range(3):
            settle(self.exchange_transaction.id, self.crypto_currency.symbol)

        # Ensure the exchange transaction status is updated to 'Failed'
        self.exchange_transaction.refresh_from_db()
        self.assertEqual(self.exchange_transaction.status, "Failed")

        # Check that the order status is updated to 'Failed'
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Failed")

        # Check that reverse transactions are created
        self.assertEqual(Transaction.objects.filter(user=self.user, type="Credit").count(), 1)

    @patch('requests.post')
    def test_settle_failure_non_500(self, mock_post):
        # Mocking a failed response with a non-500 status code (e.g. 403)
        mock_response = MagicMock()
        mock_response.status_code = 403  # Forbidden
        mock_post.return_value = mock_response

        settle(self.exchange_transaction.id, self.crypto_currency.symbol)

        # Check that the transaction status is still 'Pending' and not 'Completed' or 'Failed'
        self.exchange_transaction.refresh_from_db()
        self.assertEqual(self.exchange_transaction.status, "Pending")

    @patch('requests.post')
    def test_settle_success_after_retries(self, mock_post):
        # Mocking failed responses for first two attempts, then success on third
        mock_response = MagicMock()
        mock_response.status_code = 500  # First two attempts fail
        mock_post.return_value = mock_response

        # Simulating the third attempt success
        mock_response.status_code = 200  # Success on third attempt

        # Call the settle task
        settle(self.exchange_transaction.id, self.crypto_currency.symbol)

        # Check that the exchange transaction status is updated to 'Completed'
        self.exchange_transaction.refresh_from_db()
        self.assertEqual(self.exchange_transaction.status, "Completed")

    @patch('requests.post')
    def test_reverse_transactions_on_failure(self, mock_post):
        # Mocking a failed response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Simulating failure after 3 attempts
        for _ in range(3):
            settle(self.exchange_transaction.id, self.crypto_currency.symbol)

        # Check that reverse transactions are created
        self.assertEqual(Transaction.objects.filter(user=self.user, type="Credit").count(), 1)

        # Ensure that the exchange transaction status is updated to 'Failed'
        self.exchange_transaction.refresh_from_db()
        self.assertEqual(self.exchange_transaction.status, "Failed")

        # Ensure the order status is updated to 'Failed'
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Failed")

    @patch('requests.post')
    def test_settle_success_multiple_orders(self, mock_post):
        # Mocking successful response from the exchange API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Create orders for multiple users
        user1 = User.objects.create(username="user1")
        user2 = User.objects.create(username="user2")
        wallet1 = UserWallet.objects.create(user=user1, balance=1000, locked_balance=260)
        wallet2 = UserWallet.objects.create(user=user2, balance=4000, locked_balance=1500)

        exchange_transaction = ExchangeTransaction.objects.create(
            exchanger=self.exchanger, amount=1760, status="Pending"
        )

        order1 = Order.objects.create(
            transaction=Transaction.objects.create(user=self.user, amount=100, type="Debit"),
            user=user1, crypto_currency=self.crypto_currency, amount=50, count=2, status="Pending",
        )
        order2 = Order.objects.create(
            transaction=Transaction.objects.create(user=self.user, amount=160, type="Debit"),
            user=user1, crypto_currency=self.crypto_currency, amount=80, count=2, status="Pending",
        )
        order3 = Order.objects.create(
            transaction=Transaction.objects.create(user=self.user, amount=300, type="Debit"),
            user=user2, crypto_currency=self.crypto_currency, amount=100, count=3, status="Pending",
        )
        order4 = Order.objects.create(
            transaction=Transaction.objects.create(user=self.user, amount=500, type="Debit"),
            user=user2, crypto_currency=self.crypto_currency, amount=100, count=5, status="Pending",
        )
        order5 = Order.objects.create(
            transaction=Transaction.objects.create(user=self.user, amount=700, type="Debit"),
            user=user2, crypto_currency=self.crypto_currency, amount=100, count=7, status="Pending",
        )

        OrderExchangeTransaction.objects.create(exchange_transaction=exchange_transaction, order=order1)
        OrderExchangeTransaction.objects.create(exchange_transaction=exchange_transaction, order=order2)
        OrderExchangeTransaction.objects.create(exchange_transaction=exchange_transaction, order=order3)
        OrderExchangeTransaction.objects.create(exchange_transaction=exchange_transaction, order=order4)
        OrderExchangeTransaction.objects.create(exchange_transaction=exchange_transaction, order=order5)

        # Call the settle task
        settle(exchange_transaction.id, self.crypto_currency.symbol)

        # Ensure exchange transaction status is 'Completed'
        exchange_transaction.refresh_from_db()
        self.assertEqual(exchange_transaction.status, "Completed")

        # Ensure wallet balances and locked balances are updated
        wallet1.refresh_from_db()
        self.assertEqual(wallet1.balance, 740)
        self.assertEqual(wallet1.locked_balance, 0)

        wallet2.refresh_from_db()
        self.assertEqual(wallet2.balance, 2500)
        self.assertEqual(wallet2.locked_balance, 0)

        # Ensure order statuses are updated
        order1.refresh_from_db()
        self.assertEqual(order1.status, "Completed")

        order2.refresh_from_db()
        self.assertEqual(order2.status, "Completed")

        order3.refresh_from_db()
        self.assertEqual(order2.status, "Completed")

        order4.refresh_from_db()
        self.assertEqual(order2.status, "Completed")

        order5.refresh_from_db()
        self.assertEqual(order2.status, "Completed")

    @patch('requests.post')
    def test_settle_failed_after_retries_with_reverse_transactions(self, mock_post):
        # Mocking a failed response with status code 500 for all 3 attempts
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Create orders for multiple users
        user1 = User.objects.create(username="user1")
        user2 = User.objects.create(username="user2")
        wallet1 = UserWallet.objects.create(user=user1, balance=1000, locked_balance=260)
        wallet2 = UserWallet.objects.create(user=user2, balance=4000, locked_balance=1500)

        exchange_transaction = ExchangeTransaction.objects.create(
            exchanger=self.exchanger, amount=1760, status="Pending"
        )

        order1 = Order.objects.create(
            transaction=Transaction.objects.create(user=user1, amount=100, type="Debit"),
            user=user1, crypto_currency=self.crypto_currency, amount=50, count=2, status="Pending",
        )
        order2 = Order.objects.create(
            transaction=Transaction.objects.create(user=user1, amount=160, type="Debit"),
            user=user1, crypto_currency=self.crypto_currency, amount=80, count=2, status="Pending",
        )
        order3 = Order.objects.create(
            transaction=Transaction.objects.create(user=user2, amount=300, type="Debit"),
            user=user2, crypto_currency=self.crypto_currency, amount=100, count=3, status="Pending",
        )
        order4 = Order.objects.create(
            transaction=Transaction.objects.create(user=user2, amount=500, type="Debit"),
            user=user2, crypto_currency=self.crypto_currency, amount=100, count=5, status="Pending",
        )
        order5 = Order.objects.create(
            transaction=Transaction.objects.create(user=user2, amount=700, type="Debit"),
            user=user2, crypto_currency=self.crypto_currency, amount=100, count=7, status="Pending",
        )

        OrderExchangeTransaction.objects.create(exchange_transaction=exchange_transaction, order=order1)
        OrderExchangeTransaction.objects.create(exchange_transaction=exchange_transaction, order=order2)
        OrderExchangeTransaction.objects.create(exchange_transaction=exchange_transaction, order=order3)
        OrderExchangeTransaction.objects.create(exchange_transaction=exchange_transaction, order=order4)
        OrderExchangeTransaction.objects.create(exchange_transaction=exchange_transaction, order=order5)

        # Call the settle task 3 times, simulating retries
        for _ in range(3):
            settle(exchange_transaction.id, self.crypto_currency.symbol)

        # Ensure exchange transaction status is 'Failed'
        exchange_transaction.refresh_from_db()
        self.assertEqual(exchange_transaction.status, "Failed")

        # Ensure wallet locked balances are updated
        wallet1.refresh_from_db()
        self.assertEqual(wallet1.locked_balance, 0)
        self.assertEqual(wallet1.balance, 1000)

        wallet2.refresh_from_db()
        self.assertEqual(wallet2.locked_balance, 0)
        self.assertEqual(wallet2.balance, 4000)

        # Ensure reverse transactions are created
        reverse_transactions_user1 = Transaction.objects.filter(user=user1, type="Credit")
        reverse_transactions_user2 = Transaction.objects.filter(user=user2, type="Credit")

        self.assertEqual(Transaction.objects.filter(user=user1, type="Credit").count(), 2)
        self.assertEqual(Transaction.objects.filter(user=user2, type="Credit").count(), 3)

        self.assertEqual(sum(tx.amount for tx in reverse_transactions_user1), 260)
        self.assertEqual(sum(tx.amount for tx in reverse_transactions_user2), 1500)

        # Ensure order statuses are updated to 'Failed'
        order1.refresh_from_db()
        self.assertEqual(order1.status, "Failed")

        order2.refresh_from_db()
        self.assertEqual(order2.status, "Failed")

        order3.refresh_from_db()
        self.assertEqual(order3.status, "Failed")

        order4.refresh_from_db()
        self.assertEqual(order4.status, "Failed")

        order5.refresh_from_db()
        self.assertEqual(order5.status, "Failed")
