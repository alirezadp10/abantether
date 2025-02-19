from django.db import models


class CryptoCurrency(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50, db_index=True)
    price = models.DecimalField(max_digits=18, decimal_places=8)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app.crypto_currency'

    def __str__(self):
        return f"{self.name} - {self.price} ({self.symbol})"
