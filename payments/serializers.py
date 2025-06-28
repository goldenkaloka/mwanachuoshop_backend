import re
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import PaymentService, Payment, Wallet

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
        if payment_type == Payment.PaymentType.DEPOSIT and (service or data.get('content_type') or data.get('object_id')):
            raise serializers.ValidationError(
                "Deposit payment should not have a service or content object."
            )
        return data

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

class WalletDepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=100.00)
    mobile_number = serializers.CharField(max_length=13)  # Increased to handle +2557XXXXXXXX
    provider = serializers.ChoiceField(
        choices=['Mpesa', 'Tigo', 'Airtel', 'Halopesa'],
        default='Mpesa'
    )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value

    def validate_mobile_number(self, value):
        # Normalize mobile number
        value = value.strip()
        if value.startswith('0'):
            value = '+255' + value[1:]
        elif not value.startswith('+255'):
            if re.match(r'^7[0-9]{8}$|^6[0-9]{8}$', value):
                value = '+255' + value
            else:
                raise serializers.ValidationError(
                    "Invalid mobile number format. Use +2557XXXXXXXX, 07XXXXXXXX, or 7XXXXXXXX."
                )
        if not re.match(r'^\+255[67][0-9]{8}$', value):
            raise serializers.ValidationError(
                "Invalid mobile number format. Must be +255 followed by 6 or 7 and 8 digits."
            )
        if len(value) > 13:
            raise serializers.ValidationError("Mobile number is too long.")
        return value

    def validate_provider(self, value):
        # Make provider case-insensitive
        valid_choices = [choice.lower() for choice in ['Mpesa', 'Tigo', 'Airtel', 'Halopesa']]
        if value.lower() in valid_choices:
            # Return the title-case version for consistency
            return next(choice for choice in ['Mpesa', 'Tigo', 'Airtel', 'Halopesa'] if choice.lower() == value.lower())
        raise serializers.ValidationError(f"Invalid provider. Choose from {', '.join(valid_choices)}.")