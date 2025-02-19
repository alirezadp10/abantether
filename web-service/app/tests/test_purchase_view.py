from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from app.models import CryptoCurrency, UserWallet, Transaction, Order


class PurchaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_authenticate(user=self.user)

        self.crypto = CryptoCurrency.objects.create(symbol="BTC", price=100)
        self.wallet = UserWallet.objects.create(user=self.user, balance=1000, locked_balance=0)

    def test_successful_purchase(self):
        response = self.client.post("/api/purchase/", {"name": "BTC", "count": 5})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Your order has been registered")

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.locked_balance, 500)

    def test_crypto_not_found(self):
        response = self.client.post("/api/purchase/", {"name": "ETH", "count": 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["name"][0], "This symbol name does not exist")

    def test_wallet_not_found(self):
        self.wallet.delete()
        response = self.client.post("/api/purchase/", {"name": "BTC", "count": 5})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "User wallet not found")

    def test_insufficient_balance(self):
        response = self.client.post("/api/purchase/", {"name": "BTC", "count": 20})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Insufficient balance")

    def test_atomicity_on_failure(self):
        initial_transaction_count = Transaction.objects.count()
        initial_order_count = Order.objects.count()

        response = self.client.post("/api/purchase/", {"name": "BTC", "count": 20})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.wallet.refresh_from_db()

        self.assertEqual(self.wallet.locked_balance, 0)
        self.assertEqual(Transaction.objects.count(), initial_transaction_count)
        self.assertEqual(Order.objects.count(), initial_order_count)

    def test_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post("/api/purchase/", {"name": "BTC", "count": 5})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_request_missing_name(self):
        response = self.client.post("/api/purchase/", {"count": 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_invalid_request_missing_count(self):
        response = self.client.post("/api/purchase/", {"name": "BTC"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("count", response.data)

    def test_negative_count(self):
        response = self.client.post("/api/purchase/", {"name": "BTC", "count": -5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_zero_count(self):
        response = self.client.post("/api/purchase/", {"name": "BTC", "count": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transaction_does_not_create_when_insufficient_balance(self):
        initial_trx_count = Transaction.objects.count()
        initial_order_count = Order.objects.count()

        response = self.client.post("/api/purchase/", {"name": "BTC", "count": 15})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Transaction.objects.count(), initial_trx_count)
        self.assertEqual(Order.objects.count(), initial_order_count)
