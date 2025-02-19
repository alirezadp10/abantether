from django.db import models


class ExchangerRequestLog(models.Model):
    request = models.TextField()
    response = models.TextField(null=True)
    exchange_transaction = models.ForeignKey('ExchangeTransaction', on_delete=models.RESTRICT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app.exchanger_request_log'

    def __str__(self):
        return self.response
