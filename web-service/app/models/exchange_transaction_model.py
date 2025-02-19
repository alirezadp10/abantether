from django.db import models


class ExchangeTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    exchanger = models.ForeignKey('Exchanger', on_delete=models.RESTRICT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    order = models.ManyToManyField('Order', through='OrderExchangeTransaction', related_name='orders')
    try_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app.exchange_transaction'

    def __str__(self):
        return f"{self.exchanger} - {self.amount} - {self.status}"
