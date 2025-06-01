# payments/tasks.py
import logging
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from .models import Payment, PaymentService
from shops.models import Subscription
from marketplace.models import Product
from estates.models import Property

logger = logging.getLogger(__name__)

@transaction.atomic
def process_payment_callback(transaction_id, external_id, status_value):
    try:
        payment = Payment.objects.select_for_update().get(external_id=external_id, transaction_id=transaction_id)
        logger.debug(f"Processing callback for transaction_id {transaction_id}, external_id {external_id}, status {status_value}")
        
        if status_value.lower() == 'success':
            payment.status = Payment.PaymentStatus.COMPLETED
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
                    subscription.extend_subscription()  # Reactivates associated products
                    logger.info(f"Subscription {subscription.id} extended for payment {payment.id}")
            elif payment.payment_type == Payment.PaymentType.BRAND:
                # Handle BRAND payment if needed (e.g., activate brand)
                logger.info(f"Brand payment {payment.id} processed (no specific action defined)")
            else:
                logger.warning(f"Unsupported payment type {payment.payment_type} for payment {payment.id}")
        else:
            payment.status = Payment.PaymentStatus.FAILED
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
                    subscription.save()
                    # Deactivate associated products
                    products_updated = Product.objects.filter(
                        shop=subscription.shop,
                        is_active=True
                    ).update(is_active=False)
                    logger.info(f"Deactivated {products_updated} products for shop {subscription.shop.id} due to failed payment {payment.id}")
            elif payment.payment_type == Payment.PaymentType.BRAND:
                logger.info(f"Brand payment {payment.id} marked as failed (no specific action defined)")
            else:
                logger.warning(f"Unsupported payment type {payment.payment_type} for failed payment {payment.id}")
            logger.debug(f"Payment {payment.id} marked as failed")
        
        payment.save()
        logger.info(f"Payment {payment.id} updated to {payment.status}")
        return {"status": "success", "detail": f"Payment {payment.id} processed"}
    
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for transaction_id {transaction_id}, external_id {external_id}")
        return {"status": "error", "detail": f"Payment not found"}
    except Exception as e:
        logger.error(f"Error processing payment callback: {str(e)}", exc_info=True)
        return {"status": "error", "detail": str(e)}