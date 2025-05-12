from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class PaymentService(models.Model):
    class ServiceName(models.TextChoices):
        SHOP_SUBSCRIPTION = 'shop_subscription', 'Shop Subscription'
        BRAND_CREATION = 'brand_creation', 'Brand Creation'

    name = models.CharField(max_length=50, choices=ServiceName.choices, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
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
    amount = models.DecimalField(max_digits=10, decimal_places=2)
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
    
    # GenericForeignKey fields
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
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
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
        if self.service and self.payment_type:
            # Ensure service and payment_type align
            if self.service.name == PaymentService.ServiceName.SHOP_SUBSCRIPTION and \
               self.payment_type != self.PaymentType.SUBSCRIPTION:
                raise ValidationError("Shop Subscription service must have Subscription payment type.")
            if self.service.name == PaymentService.ServiceName.BRAND_CREATION and \
               self.payment_type != self.PaymentType.BRAND:
                raise ValidationError("Brand Creation service must have Brand payment type.")
        if self.payment_type in [self.PaymentType.PRODUCT, self.PaymentType.ESTATE] and self.service:
            raise ValidationError("Product and Estate payments should not have a service.")

    def __str__(self):
        return f"{self.user.username} - {self.payment_type or self.service.name} - {self.amount}"