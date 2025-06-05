import logging
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from .models import Payment
from shops.models import Shop, Subscription
from marketplace.models import Product
from estates.models import Property

logger = logging.getLogger(__name__)

@transaction.atomic
def process_payment_callback(transaction_id, external_id, status_value):
    """Process ZenoPay callback to update payment status and related objects."""
    try:
        payment = Payment.objects.select_for_update().get(
            external_id=external_id,
            transaction_id=transaction_id
        )
        logger.debug(f"Processing callback for transaction_id {transaction_id}, external_id {external_id}, status {status_value}")

        status_map = {
            'SUCCESS': Payment.PaymentStatus.COMPLETED,
            'FAILED': Payment.PaymentStatus.FAILED,
            'CANCELLED': Payment.PaymentStatus.FAILED,
            'PENDING': Payment.PaymentStatus.PENDING
        }
        new_status = status_map.get(status_value.upper(), Payment.PaymentStatus.FAILED)
        
        if payment.status == Payment.PaymentStatus.COMPLETED:
            logger.warning(f"Payment {payment.id} already completed, skipping update.")
            return

        payment.status = new_status
        payment.save()

        if new_status == Payment.PaymentStatus.COMPLETED:
            if payment.payment_type == Payment.PaymentType.PRODUCT:
                product = payment.content_object
                if isinstance(product, Product):
                    product.is_active = True
                    product.save()
                    logger.info(f"Product {product.id} activated for payment {payment.id}")
            elif payment.payment_type == Payment.PaymentType.ESTATE:
                property_instance = payment.content_object
                if isinstance(property_instance, Property):
                    property_instance.is_available = True
                    property_instance.save()
                    logger.info(f"Property {property_instance.id} set to is_available=True for payment {payment.id}")
            elif payment.payment_type == Payment.PaymentType.SUBSCRIPTION:
                subscription = payment.content_object
                if isinstance(subscription, Subscription):
                    subscription.extend_subscription(months=1)
                    logger.info(f"Subscription {subscription.id} extended for payment {payment.id}")
            elif payment.payment_type == Payment.PaymentType.BRAND:
                logger.info(f"Brand payment {payment.id} processed (no specific action defined)")
            else:
                logger.warning(f"Unsupported payment type {payment.payment_type} for payment {payment.id}")

        elif new_status == Payment.PaymentStatus.FAILED:
            if payment.payment_type == Payment.PaymentType.PRODUCT:
                product = payment.content_object
                if isinstance(product, Product):
                    product.is_active = False
                    product.save()
                    logger.info(f"Product {product.id} set to is_active=False for failed payment {payment.id}")
            elif payment.payment_type == Payment.PaymentType.ESTATE:
                property_instance = payment.content_object
                if isinstance(property_instance, Property):
                    property_instance.is_available = False
                    property_instance.save()
                    logger.info(f"Property {property_instance.id} set to is_available=False for failed payment {payment.id}")
            elif payment.payment_type == Payment.PaymentType.SUBSCRIPTION:
                subscription = payment.content_object
                if isinstance(subscription, Subscription):
                    subscription.status = Subscription.Status.EXPIRED
                    subscription.shop.is_active = False
                    subscription.shop.save(update_fields=['is_active'])
                    subscription.save()
                    products_updated = Product.objects.filter(
                        shop=subscription.shop,
                        is_active=True
                    ).update(is_active=False)
                    logger.info(f"Deactivated {products_updated} products and shop {subscription.shop.id} due to failed payment {payment.id}")
            elif payment.payment_type == Payment.PaymentType.BRAND:
                logger.info(f"Brand payment {payment.id} marked as failed (no specific action defined)")
            else:
                logger.warning(f"Unsupported payment type {payment.payment_type} for failed payment {payment.id}")

        logger.info(f"Payment {payment.id} updated to status {payment.status}")

    except Payment.DoesNotExist:
        logger.error(f"Payment not found for transaction_id {transaction_id}, external_id {external_id}")
    except Exception as e:
        logger.error(f"Error processing payment callback for transaction_id {transaction_id}: {str(e)}", exc_info=True)