from django.db import models


class Exchanger(models.Model):
    name = models.CharField(max_length=50, unique=True)
    api_url = models.URLField()
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app.exchanger'

    def __str__(self):
        return self.name
