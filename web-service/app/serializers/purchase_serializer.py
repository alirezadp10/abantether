from rest_framework import serializers
from app.models import CryptoCurrency


class PurchaseSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=10, required=True, allow_blank=False)
    count = serializers.IntegerField(min_value=1, required=True)

    def validate_name(self, value):
        if not CryptoCurrency.objects.filter(symbol=value.upper()).exists():
            raise serializers.ValidationError("This symbol name does not exist")
        return value
