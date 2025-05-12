import logging
from django.contrib.contenttypes.models import ContentType
from .models import Payment, PaymentService
from shops.models import Subscription
from marketplace.models import Product

logger = logging.getLogger(__name__)

def process_payment_callback(transaction_id, external_id, status_value):
    try:
        payment = Payment.objects.get(external_id=external_id, transaction_id=transaction_id)
        logger.debug(f"Processing callback for transaction_id {transaction_id}, status {status_value}")
        
        if status_value.lower() == 'success':
            payment.status = Payment.PaymentStatus.COMPLETED
            if payment.payment_type == Payment.PaymentType.PRODUCT:
                product = payment.content_object
                if isinstance(product, Product):
                    product.is_active = True
                    product.save()
                    logger.info(f"Product {product.id} activated for payment {payment.id}")
            elif payment.payment_type == Payment.PaymentType.SUBSCRIPTION and payment.service:
                subscription = payment.content_object
                if isinstance(subscription, Subscription):
                    subscription.extend_subscription()
                    logger.info(f"Subscription extended for payment {payment.id}")
            else:
                logger.warning(f"Unsupported payment type {payment.payment_type} or missing service for payment {payment.id}")
        else:
            payment.status = Payment.PaymentStatus.FAILED
            logger.debug(f"Payment {payment.id} marked as failed")
        
        payment.save()
        logger.info(f"Payment {payment.id} updated to {payment.status}")
        return {"status": "success", "detail": f"Payment {payment.id} processed"}
    
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for transaction_id {transaction_id}, external_id {external_id}")
        return {"status": "error", "detail": f"Payment not found"}
    except Exception as e:
        logger.error(f"Error processing payment callback: {str(e)}")
        return {"status": "error", "detail": str(e)}