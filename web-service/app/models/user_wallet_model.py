from django.db import models
from django.contrib.auth.models import User


class UserWallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    locked_balance = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app.user_wallet'

    def __str__(self):
        return f"{self.user.username}: {int(self.balance) - int(self.locked_balance)}"
