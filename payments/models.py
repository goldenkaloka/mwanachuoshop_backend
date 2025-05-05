from django.conf import settings
from django.db import models

class PaymentService(models.Model):
    class ServiceName(models.TextChoices):
        PRODUCT_CREATION = 'product_creation', 'Product Creation'
        SHOP_SUBSCRIPTION = 'shop_subscription', 'Shop Subscription'
        ESTATE_CREATION = 'estate_creation', 'Estate Creation'
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

    service = models.ForeignKey(PaymentService, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    date_added = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    external_id = models.CharField(max_length=100, blank=True, null=True)
    provider = models.CharField(max_length=50, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    subscription = models.ForeignKey('shops.Subscription', on_delete=models.SET_NULL, blank=True, null=True, related_name='payments')

    class Meta:
        indexes = [models.Index(fields=['user', 'date_added'])]

    def __str__(self):
        return f"{self.user.username} - {self.service.name} - {self.amount}"