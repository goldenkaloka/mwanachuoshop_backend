from datetime import datetime, timedelta, timezone
from django.conf import settings

from marketplace.utils.azampay import AzamPayService
from shops.models import ShopSubscription
from users.models import ProductPayment, SubscriptionPayment


class PaymentProcessor:
    @staticmethod
    def process_subscription_payment(shop, plan, payment_method='azampay'):
        """Process subscription payment for a shop"""
        # Create subscription first (inactive)
        start_date = timezone.now()
        end_date = start_date + timedelta(days=plan.duration_days)
        
        subscription = ShopSubscription.objects.create(
            shop=shop,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            is_active=False,
            is_trial=plan.is_trial
        )
        
        # Create payment record
        transaction_id = f"SUB-{shop.id}-{datetime.now().timestamp()}"
        payment = SubscriptionPayment.objects.create(
            shop=shop,
            plan=plan,
            subscription=subscription,
            amount=plan.price,
            payment_method=payment_method,
            transaction_id=transaction_id
        )
        
        # Initiate payment based on method
        if payment_method == 'azampay':
            phone = shop.owner.profile.phone_number
            callback_url = f"{settings.BASE_URL}/api/payments/azampay-callback/"
            
            try:
                response = AzamPayService.initiate_payment(
                    amount=plan.price,
                    phone=phone,
                    reference=transaction_id,
                    callback_url=callback_url
                )
                
                payment.metadata = {
                    'initiation_response': response,
                    'azampay_reference': response.get('referenceId')
                }
                payment.save()
                return payment, response
            except Exception as e:
                payment.status = 'failed'
                payment.metadata = {'error': str(e)}
                payment.save()
                return payment, None

    @staticmethod
    def process_product_payment(user, product, payment_method='azampay'):
        """Process payment for individual product listing"""
        # Determine price (could be from product or fixed amount)
        amount = settings.PRODUCT_LISTING_FEE  # Or product.price if you charge based on product
        
        transaction_id = f"PROD-{user.id}-{datetime.now().timestamp()}"
        payment = ProductPayment.objects.create(
            user=user,
            product=product,
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id
        )
        
        if payment_method == 'azampay':
            phone = user.profile.phone_number
            callback_url = f"{settings.BASE_URL}/api/payments/azampay-product-callback/"
            
            try:
                response = AzamPayService.initiate_payment(
                    amount=amount,
                    phone=phone,
                    reference=transaction_id,
                    callback_url=callback_url
                )
                
                payment.metadata = {
                    'initiation_response': response,
                    'azampay_reference': response.get('referenceId')
                }
                payment.save()
                return payment, response
            except Exception as e:
                payment.status = 'failed'
                payment.metadata = {'error': str(e)}
                payment.save()
                return payment, None