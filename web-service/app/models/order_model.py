from django.db import models
from django.contrib.auth.models import User


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    crypto_currency = models.ForeignKey('CryptoCurrency', on_delete=models.RESTRICT)
    transaction = models.ForeignKey('Transaction', on_delete=models.RESTRICT)
    exchange_transaction = models.ManyToManyField('ExchangeTransaction', through='OrderExchangeTransaction', related_name='exchange_transactions')
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    count = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app.order'

    def __str__(self):
        return f"{self.user.username} - {self.crypto_currency.symbol} - {self.amount} - {self.status}"
