from django.db import models


class OrderExchangeTransaction(models.Model):
    exchange_transaction = models.ForeignKey('ExchangeTransaction', on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app.order_exchange_transaction'

    def __str__(self):
        return f"{self.exchange_transaction} - {self.order}"
