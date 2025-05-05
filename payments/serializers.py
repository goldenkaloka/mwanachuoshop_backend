from rest_framework import serializers
from .models import PaymentService, Payment

class PaymentServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentService
        fields = ['id', 'name', 'price', 'description']

class PaymentSerializer(serializers.ModelSerializer):
    service = PaymentServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=PaymentService.objects.all(), source='service', write_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'id', 'service', 'service_id', 'user', 'amount', 'status', 'date_added',
            'transaction_id', 'external_id', 'provider', 'account_number'
        ]
        read_only_fields = ['user', 'status', 'date_added', 'transaction_id', 'external_id']