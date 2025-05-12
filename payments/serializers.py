from rest_framework import serializers
from .models import PaymentService, Payment
from django.contrib.contenttypes.models import ContentType

class PaymentServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentService
        fields = ['id', 'name', 'price', 'description']

class PaymentSerializer(serializers.ModelSerializer):
    service = PaymentServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=PaymentService.objects.all(),
        source='service',
        write_only=True,
        required=False,
        allow_null=True
    )
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all(),
        required=False,
        allow_null=True
    )
    object_id = serializers.IntegerField(required=False, allow_null=True)
    payment_type = serializers.ChoiceField(
        choices=Payment.PaymentType.choices,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Payment
        fields = [
            'id', 'service', 'service_id', 'payment_type', 'user', 'amount', 'status',
            'date_added', 'transaction_id', 'external_id', 'provider', 'account_number',
            'content_type', 'object_id'
        ]
        read_only_fields = ['user', 'status', 'date_added', 'transaction_id', 'external_id']

    def validate(self, data):
        payment_type = data.get('payment_type')
        service = data.get('service')
        if payment_type in [Payment.PaymentType.PRODUCT, Payment.PaymentType.ESTATE] and service:
            raise serializers.ValidationError(
                "Product and Estate payments should not have a service."
            )
        if payment_type in [Payment.PaymentType.SUBSCRIPTION, Payment.PaymentType.BRAND] and not service:
            raise serializers.ValidationError(
                f"{payment_type} payment requires a service."
            )
        return data