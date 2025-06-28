from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.db.models import F
from django.db import transaction
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class PaymentService(models.Model):
    class ServiceName(models.TextChoices):
        SHOP_SUBSCRIPTION = 'shop_subscription', 'Shop Subscription'
        BRAND_CREATION = 'brand_creation', 'Brand Creation'

    name = models.CharField(max_length=50, choices=ServiceName.choices, unique=True)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.get_name_display()

class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    class PaymentType(models.TextChoices):
        PRODUCT = 'product', 'Product Activation'
        ESTATE = 'estate', 'Estate Activation'
        SUBSCRIPTION = 'subscription', 'Shop Subscription'
        BRAND = 'brand', 'Brand Creation'
        DEPOSIT = 'deposit', 'Wallet Deposit'

    service = models.ForeignKey(
        PaymentService,
        on_delete=models.CASCADE,
        related_name='payments',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        null=True,
        blank=True
    )
    date_added = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    external_id = models.CharField(max_length=100, blank=True, null=True)
    provider = models.CharField(max_length=50, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        indexes = [
            models.Index(fields=['user', 'date_added']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['payment_type']),
            models.Index(fields=['transaction_id']),
        ]

    def clean(self):
        if self.payment_type == self.PaymentType.PRODUCT and \
           (not self.content_type or self.content_type.model != 'product'):
            raise ValidationError("Product payment must reference a Product.")
        if self.payment_type == self.PaymentType.ESTATE and \
           (not self.content_type or self.content_type.model != 'property'):
            raise ValidationError("Estate payment must reference a Property.")
        if self.payment_type == self.PaymentType.SUBSCRIPTION and \
           (not self.content_type or self.content_type.model != 'subscription'):
            raise ValidationError("Subscription payment must reference a Subscription.")
        if self.payment_type == self.PaymentType.BRAND and \
           (not self.content_type or self.content_type.model != 'brand'):
            raise ValidationError("Brand payment must reference a Brand.")
        if self.payment_type == self.PaymentType.DEPOSIT and \
           (self.content_type or self.object_id or self.service):
            raise ValidationError("Deposit payment should not reference a content object or service.")
        if self.service and self.payment_type:
            if self.service.name == PaymentService.ServiceName.SHOP_SUBSCRIPTION and \
               self.payment_type != self.PaymentType.SUBSCRIPTION:
                raise ValidationError("Shop Subscription service must have Subscription payment type.")
            if self.service.name == PaymentService.ServiceName.BRAND_CREATION and \
               self.payment_type != self.PaymentType.BRAND:
                raise ValidationError("Brand Creation service must have Brand payment type.")
        if self.payment_type in [self.PaymentType.PRODUCT, self.PaymentType.ESTATE] and self.service:
            raise ValidationError("Product and Estate payments should not have a service.")
        if self.payment_type == self.PaymentType.PRODUCT:
            if self.content_object:
                product_price = Decimal(self.content_object.price)
                if product_price >= Decimal('500000.00'):
                    expected_amount = Decimal('500.00')
                elif product_price < Decimal('10000.00'):
                    expected_amount = Decimal('100.00')
                else:
                    expected_amount = (product_price * Decimal('0.001')).quantize(Decimal('0.01'))
                if self.amount != expected_amount:
                    raise ValidationError(f"Invalid amount for product payment. Expected {expected_amount}, got {self.amount}.")
        elif self.payment_type == self.PaymentType.ESTATE:
            if self.content_object:
                expected_amount = (Decimal(self.content_object.price) * Decimal('0.01')).quantize(Decimal('0.01'))
                if self.amount != expected_amount:
                    raise ValidationError(f"Invalid amount for estate payment. Expected {expected_amount}, got {self.amount}.")
        elif self.payment_type in [self.PaymentType.SUBSCRIPTION, self.PaymentType.BRAND]:
            if self.service and self.amount != self.service.price:
                raise ValidationError(f"Invalid amount for {self.service.name}. Expected {self.service.price}, got {self.amount}.")
        elif self.payment_type == self.PaymentType.DEPOSIT:
            if self.amount < Decimal('100.00'):
                raise ValidationError("Deposit amount must be at least 100 TZS.")

    def process_payment(self):
        """Deduct payment amount from user's wallet."""
        try:
            wallet = self.user.wallet
            with transaction.atomic():
                wallet.deduct_balance(
                    amount=self.amount,
                    payment=self,
                    description=f"Payment for {self.payment_type}"
                )
                self.status = self.PaymentStatus.COMPLETED
                if self.payment_type != self.PaymentType.DEPOSIT:
                    self.transaction_id = None
                    self.external_id = None
                    self.provider = None
                    self.account_number = None
                self.save()
                logger.info(f"Payment {self.id} processed for user {self.user.username}, amount: {self.amount} TZS")
        except Wallet.DoesNotExist:
            self.status = self.PaymentStatus.FAILED
            self.save()
            logger.error(f"Payment {self.id} failed: No wallet for user {self.user.username}")
            raise ValidationError("User does not have a wallet.")
        except ValidationError as e:
            self.status = self.PaymentStatus.FAILED
            self.save()
            logger.error(f"Payment {self.id} failed: {str(e)}")
            raise e

    def __str__(self):
        return f"{self.user.username} - {self.payment_type or self.service.name} - {self.amount} TZS"

class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username}'s Wallet - Balance: {self.balance} TZS"

    def has_sufficient_balance(self, amount):
        return self.balance >= amount

    def deduct_balance(self, amount, payment=None, description=""):
        if amount <= 0:
            raise ValidationError("Amount must be positive.")
        if not self.has_sufficient_balance(amount):
            raise ValidationError("Insufficient wallet balance. Please fund your wallet.")
        
        with transaction.atomic():
            self.balance = F('balance') - amount
            self.save()
            self.refresh_from_db()

            WalletTransaction.objects.create(
                wallet=self,
                amount=-amount,
                transaction_type=WalletTransaction.TransactionType.DEBIT,
                payment=payment,
                description=description or f"Payment for {payment.payment_type if payment else 'unknown'}"
            )

    def add_funds(self, amount, transaction_id=None, external_id=None, provider=None, account_number=None, description="ZenoPay deposit"):
        if amount <= 0:
            raise ValidationError("Amount must be positive.")
        
        with transaction.atomic():
            self.balance = F('balance') + amount
            self.save()
            self.refresh_from_db()

            WalletTransaction.objects.create(
                wallet=self,
                amount=amount,
                transaction_type=WalletTransaction.TransactionType.CREDIT,
                transaction_id=transaction_id,
                external_id=external_id,
                provider=provider,
                account_number=account_number,
                description=description
            )

class WalletTransaction(models.Model):
    class TransactionType(models.TextChoices):
        CREDIT = 'credit', 'Credit'
        DEBIT = 'debit', 'Debit'

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions'
    )
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    external_id = models.CharField(max_length=100, blank=True, null=True)
    provider = models.CharField(max_length=50, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['transaction_id']),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} TZS - {self.created_at}"