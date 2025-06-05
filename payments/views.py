import json
import re
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import uuid
import logging
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django_q.tasks import async_task
from .models import PaymentService, Payment
from .serializers import PaymentServiceSerializer, PaymentSerializer
from .tasks import process_payment_callback
from shops.models import Shop, Subscription, UserOffer
from marketplace.models import Product
from estates.models import Property

logger = logging.getLogger(__name__)

class PaymentServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentService.objects.all()
    serializer_class = PaymentServiceSerializer
    permission_classes = [IsAuthenticated]

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_product_payment(request):
    """Initiate a payment for product activation (0.1% of product price, minimum 1000 TZS)."""
    product_id = request.data.get('product_id')
    if not product_id:
        logger.error("Product ID not provided.")
        return Response({"error": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    product = get_object_or_404(Product, id=product_id, owner=request.user)
    shop = getattr(request.user, 'shop', None)
    offer = getattr(request.user, 'offer', None)

    if product.is_active:
        logger.info(f"Product {product_id} already active for user {request.user.username}.")
        return Response({"detail": "Product already active."}, status=status.HTTP_400_BAD_REQUEST)

    existing_payment = Payment.objects.filter(
        user=request.user,
        content_type=ContentType.objects.get_for_model(Product),
        object_id=product.id,
        payment_type=Payment.PaymentType.PRODUCT,
        status=Payment.PaymentStatus.PENDING
    ).first()
    if existing_payment:
        logger.info(f"Existing pending payment found for product {product_id}: transaction_id {existing_payment.transaction_id}")
        return Response({
            "transaction_id": existing_payment.transaction_id,
            "amount": str(existing_payment.amount),
            "message": "Payment already initiated. Please complete the transaction or wait for processing."
        }, status=status.HTTP_200_OK)

    if shop and shop.is_subscription_active():
        logger.info(f"User {request.user.username} has active shop subscription.")
        with transaction.atomic():
            product.is_active = True
            product.save()
        return Response({
            "detail": "Product activated via shop subscription."
        }, status=status.HTTP_200_OK)

    if offer and offer.consume_free_product():
        logger.info(f"User {request.user.username} used free product offer.")
        with transaction.atomic():
            product.is_active = True
            product.save()
        return Response({
            "detail": "Product activated using free offer.",
            "free_products_remaining": offer.free_products_remaining
        }, status=status.HTTP_200_OK)

    try:
        mobile_number = request.data.get('mobile_number')
        provider = request.data.get('provider', 'Mpesa')

        if not mobile_number:
            logger.error("Mobile number not provided.")
            return Response({"error": "Mobile number is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize phone number to +255 format
        if mobile_number.startswith('0'):
            mobile_number = '+255' + mobile_number[1:]
        if not re.match(r'^\+255[67]\d{8}$', mobile_number):
            logger.error(f"Invalid mobile number format: {mobile_number}")
            return Response({"error": "Invalid mobile number format. Use +2557XXXXXXXX or 07XXXXXXXX."}, 
                           status=status.HTTP_400_BAD_REQUEST)

        provider_map = {
            'mpesa': 'Mpesa',
            'tigo': 'Tigo',
            'airtel': 'Airtel',
            'halopesa': 'Halopesa',
        }
        normalized_provider = provider_map.get(provider.lower(), provider)
        if normalized_provider not in ['Mpesa', 'Tigo', 'Airtel', 'Halopesa']:
            logger.error(f"Invalid provider: {provider}")
            return Response({"error": f"Invalid provider: {provider}. Must be one of Mpesa, Tigo, Airtel, Halopesa."}, 
                           status=status.HTTP_400_BAD_REQUEST)

        payment_amount = max(
            Decimal('1000.00'),
            (product.price * Decimal('0.001')).quantize(Decimal('0.01'))
        )
        external_id = str(uuid.uuid4())
        logger.info(f"Initiating product payment for user {request.user.username}, product {product_id}, external_id {external_id}, amount {payment_amount} TZS")

        # ZenoPay REST API call
        payload = {
            'create_order': 1,
            'buyer_email': request.user.email or 'no-email@example.com',
            'buyer_name': request.user.username,
            'buyer_phone': mobile_number,
            'amount': float(payment_amount),
            'account_id': settings.ZENOPAY_ACCOUNT_ID,
            'api_key': settings.ZENOPAY_API_KEY,
            'secret_key': settings.ZENOPAY_SECRET_KEY,
            'webhook_url': settings.ZENOPAY_WEBHOOK_URL,
            'metadata': json.dumps({
                'product_id': product_id,
                'external_id': external_id,
                'provider': normalized_provider
            })
        }

        try:
            response = requests.post(settings.ZENOPAY_API_BASE_URL, json=payload)
            response.raise_for_status()
            response_data = response.json()
            logger.debug(f"ZenoPay API response: {response_data}")
        except requests.RequestException as e:
            logger.error(f"ZenoPay API request failed: {str(e)}")
            return Response({"error": f"Payment service unavailable: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError:
            logger.error(f"Invalid JSON response from ZenoPay: {response.text}")
            return Response({"error": "Invalid response from payment service."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if response_data.get('status') == 'success':
            transaction_id = response_data.get('order_id')
            with transaction.atomic():
                payment = Payment.objects.create(
                    user=request.user,
                    amount=payment_amount,
                    status=Payment.PaymentStatus.PENDING,
                    transaction_id=transaction_id,
                    external_id=external_id,
                    provider=normalized_provider,
                    account_number=mobile_number,
                    content_type=ContentType.objects.get_for_model(Product),
                    object_id=product.id,
                    payment_type=Payment.PaymentType.PRODUCT,
                    service=None
                )
                logger.info(f"Payment created: transaction_id {payment.transaction_id}, status {payment.status}")

            return Response({
                "transaction_id": payment.transaction_id,
                "amount": str(payment_amount),
                "message": "Payment initiated. Please complete the transaction via your mobile device and confirm activation."
            }, status=status.HTTP_201_CREATED)
        else:
            error_message = response_data.get('message', 'Payment initiation failed.')
            logger.error(f"ZenoPay payment failed: {error_message}")
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Payment initiation error for product {product_id}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_estate_payment(request):
    """Initiate a payment for property activation (0.1% of property price, minimum 1000 TZS)."""
    property_id = request.data.get('property_id')
    if not property_id:
        logger.error("Property ID not provided.")
        return Response({"error": "Property ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    property_instance = get_object_or_404(Property, id=property_id, owner=request.user)

    if property_instance.is_available:
        logger.info(f"Property {property_id} already available for user {request.user.username}.")
        return Response({"detail": "Property already activated."}, status=status.HTTP_400_BAD_REQUEST)

    existing_payment = Payment.objects.filter(
        user=request.user,
        content_type=ContentType.objects.get_for_model(Property),
        object_id=property_instance.id,
        payment_type=Payment.PaymentType.ESTATE,
        status=Payment.PaymentStatus.PENDING
    ).first()
    if existing_payment:
        logger.info(f"Existing pending payment found for property {property_id}: transaction_id {existing_payment.transaction_id}")
        return Response({
            "transaction_id": existing_payment.transaction_id,
            "amount": str(existing_payment.amount),
            "message": "Payment already initiated. Please complete the transaction or wait for processing."
        }, status=status.HTTP_200_OK)

    try:
        mobile_number = request.data.get('mobile_number')
        provider = request.data.get('provider', 'Mpesa')

        if not mobile_number:
            logger.error("Mobile number not provided.")
            return Response({"error": "Mobile number is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize phone number to +255 format
        if mobile_number.startswith('0'):
            mobile_number = '+255' + mobile_number[1:]
        if not re.match(r'^\+255[67]\d{8}$', mobile_number):
            logger.error(f"Invalid mobile number: {mobile_number}")
            return Response({"error": "Invalid mobile number format. Use +2557XXXXXXXX or 07XXXXXXXX."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        provider_map = {
            'mpesa': 'Mpesa',
            'tigo': 'Tigo',
            'airtel': 'Airtel',
            'halopesa': 'Halopesa',
        }
        normalized_provider = provider_map.get(provider.lower(), provider)
        if normalized_provider not in ['Mpesa', 'Tigo', 'Airtel', 'Halopesa']:
            logger.error(f"Invalid provider: {provider}")
            return Response({"error": f"Invalid provider: {provider}. Must be one of Mpesa, Tigo, Airtel, Halopesa."}, 
                           status=status.HTTP_400_BAD_REQUEST)

        payment_amount = max(
            Decimal('1000.00'),
            (property_instance.price * Decimal('0.001')).quantize(Decimal('0.01'))
        )
        external_id = str(uuid.uuid4())
        logger.info(f"Initiating estate payment for user {request.user.username}, property {property_id}, external_id {external_id}, amount {payment_amount} TZS")

        # ZenoPay REST API call
        payload = {
            'create_order': 1,
            'buyer_email': request.user.email or 'no-email@example.com',
            'buyer_name': request.user.username,
            'buyer_phone': mobile_number,
            'amount': float(payment_amount),
            'account_id': settings.ZENOPAY_ACCOUNT_ID,
            'api_key': settings.ZENOPAY_API_KEY,
            'secret_key': settings.ZENOPAY_SECRET_KEY,
            'webhook_url': settings.ZENOPAY_WEBHOOK_URL,
            'metadata': json.dumps({
                'property_id': property_id,
                'external_id': external_id,
                'provider': normalized_provider
            })
        }

        try:
            response = requests.post(settings.ZENOPAY_API_BASE_URL, json=payload)
            response.raise_for_status()
            response_data = response.json()
            logger.debug(f"ZenoPay API response: {response_data}")
        except requests.RequestException as e:
            logger.error(f"ZenoPay API request failed: {str(e)}")
            return Response({"error": f"Payment service unavailable: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError:
            logger.error(f"Invalid JSON response from ZenoPay: {response.text}")
            return Response({"error": "Invalid response from payment service."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if response_data.get('status') == 'success':
            transaction_id = response_data.get('order_id')
            with transaction.atomic():
                payment = Payment.objects.create(
                    user=request.user,
                    amount=payment_amount,
                    status=Payment.PaymentStatus.PENDING,
                    transaction_id=transaction_id,
                    external_id=external_id,
                    provider=normalized_provider,
                    account_number=mobile_number,
                    content_type=ContentType.objects.get_for_model(Property),
                    object_id=property_instance.id,
                    payment_type=Payment.PaymentType.ESTATE,
                    service=None
                )
                logger.info(f"Payment created: transaction_id {payment.transaction_id}, status {payment.status}")

            return Response({
                "transaction_id": payment.transaction_id,
                "amount": str(payment_amount),
                "message": "Payment initiated. Please complete the transaction and confirm activation via confirm-property-creation."
            }, status=status.HTTP_201_CREATED)
        else:
            error_message = response_data.get('message', 'Payment initiation failed.')
            logger.error(f"ZenoPay payment failed: {error_message}")
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Payment initiation error for property {property_id}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_shop_subscription_payment(request):
    """Initiate a payment for a 1-month shop subscription."""
    shop_id = request.data.get('shop_id')
    if not shop_id:
        logger.error("Shop ID not provided.")
        return Response({"error": "Shop ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    shop = get_object_or_404(Shop, id=shop_id, user=request.user)
    subscription = getattr(shop, 'subscription', None)

    if not subscription:
        logger.error(f"No subscription found for shop {shop_id}")
        return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        payment_service = PaymentService.objects.get(name=PaymentService.ServiceName.SHOP_SUBSCRIPTION)
        mobile_number = request.data.get('mobile_number')
        provider = request.data.get('provider', 'Mpesa')
        payment_amount = payment_service.price  # Fixed amount for 1 month

        if not mobile_number:
            logger.error("Mobile number not provided.")
            return Response({"error": "Mobile number is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize phone number to +255 format
        if mobile_number.startswith('0'):
            mobile_number = '+255' + mobile_number[1:]
        if not re.match(r'^\+255[67]\d{8}$', mobile_number):
            logger.error(f"Invalid mobile number format: {mobile_number}")
            return Response({"error": "Invalid mobile number format. Use +2557XXXXXXXX or 07XXXXXXXX."}, 
                           status=status.HTTP_400_BAD_REQUEST)

        provider_map = {
            'mpesa': 'Mpesa',
            'tigo': 'Tigo',
            'airtel': 'Airtel',
            'halopesa': 'Halopesa',
        }
        normalized_provider = provider_map.get(provider.lower(), provider)
        if normalized_provider not in ['Mpesa', 'Tigo', 'Airtel', 'Halopesa']:
            logger.error(f"Invalid provider: {provider}")
            return Response({"error": f"Invalid provider: {provider}. Must be one of Mpesa, Tigo, Airtel, Halopesa."}, 
                           status=status.HTTP_400_BAD_REQUEST)

        existing_payment = Payment.objects.filter(
            user=request.user,
            content_type=ContentType.objects.get_for_model(Subscription),
            object_id=subscription.id,
            payment_type=Payment.PaymentType.SUBSCRIPTION,
            status=Payment.PaymentStatus.PENDING
        ).first()
        if existing_payment:
            logger.info(f"Existing pending payment found for subscription {subscription.id}: transaction_id {existing_payment.transaction_id}")
            return Response({
                "transaction_id": existing_payment.transaction_id,
                "amount": str(existing_payment.amount),
                "message": "Payment already initiated. Please complete the transaction or wait for processing."
            }, status=status.HTTP_200_OK)

        external_id = str(uuid.uuid4())
        logger.info(f"Initiating shop subscription payment for user {request.user.username}, service {payment_service.name}, shop_id {shop_id}, external_id {external_id}, amount {payment_amount} TZS")

        # ZenoPay REST API call
        payload = {
            'create_order': 1,
            'buyer_email': request.user.email or 'no-email@example.com',
            'buyer_name': request.user.username,
            'buyer_phone': mobile_number,
            'amount': float(payment_amount),
            'account_id': settings.ZENOPAY_ACCOUNT_ID,
            'api_key': settings.ZENOPAY_API_KEY,
            'secret_key': settings.ZENOPAY_SECRET_KEY,
            'webhook_url': settings.ZENOPAY_WEBHOOK_URL,
            'metadata': json.dumps({
                'shop_id': shop_id,
                'subscription_id': str(subscription.id),
                'external_id': external_id,
                'provider': normalized_provider
            })
        }

        try:
            response = requests.post(settings.ZENOPAY_API_BASE_URL, json=payload)
            response.raise_for_status()
            response_data = response.json()
            logger.debug(f"ZenoPay API response: {response_data}")
        except requests.RequestException as e:
            logger.error(f"ZenoPay API request failed: {str(e)}")
            return Response({"error": f"Payment service unavailable: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError:
            logger.error(f"Invalid JSON response from ZenoPay: {response.text}")
            return Response({"error": "Invalid response from payment service."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if response_data.get('status') == 'success':
            transaction_id = response_data.get('order_id')
            with transaction.atomic():
                payment = Payment.objects.create(
                    user=request.user,
                    service=payment_service,
                    amount=payment_amount,
                    status=Payment.PaymentStatus.PENDING,
                    transaction_id=transaction_id,
                    external_id=external_id,
                    provider=normalized_provider,
                    account_number=mobile_number,
                    content_type=ContentType.objects.get_for_model(Subscription),
                    object_id=subscription.id,
                    payment_type=Payment.PaymentType.SUBSCRIPTION
                )
                logger.info(f"Payment created: transaction_id {payment.transaction_id}, status {payment.status}")

            return Response({
                "transaction_id": payment.transaction_id,
                "amount": str(payment_amount),
                "message": "Payment initiated. Please complete the transaction via your mobile device."
            }, status=status.HTTP_201_CREATED)
        else:
            error_message = response_data.get('message', 'Payment initiation failed.')
            logger.error(f"ZenoPay payment failed: {error_message}")
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

    except PaymentService.DoesNotExist:
        logger.error("Shop subscription service not found")
        return Response({"error": "Shop subscription service not available."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Payment initiation error for shop {shop_id} subscription: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def zenopay_callback(request):
    """Handle ZenoPay payment callback."""
    logger.debug(f"Callback received from IP: {request.META.get('REMOTE_ADDR')}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Raw callback data: {request.body}")

    try:
        data = json.loads(request.body) if request.body else {}
        logger.debug(f"Parsed callback payload: {data}")

        # Map ZenoPay webhook fields (prioritize order_id and payment_status)
        transaction_id = data.get('order_id') or data.get('transactionId') or data.get('reference')
        external_id = data.get('reference') or data.get('externalId') or data.get('utilityRef')
        status_value = data.get('payment_status') or data.get('status') or data.get('transactionStatus')

        if not all([transaction_id, external_id, status_value]):
            logger.error(f"Missing required fields: transaction_id={transaction_id}, external_id={external_id}, status={status_value}")
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(settings, 'ZENOPAY_ALLOWED_IPS') and settings.ZENOPAY_ALLOWED_IPS:
            if request.META.get('REMOTE_ADDR') not in settings.ZENOPAY_ALLOWED_IPS:
                logger.error(f"Unauthorized callback from IP: {request.META.get('REMOTE_ADDR')}")
                return Response({"error": "Unauthorized callback source"}, status=status.HTTP_403_FORBIDDEN)

        task_id = async_task(
            'payments.tasks.process_payment_callback',
            transaction_id,
            external_id,
            status_value,
            task_name=f'process_payment_{transaction_id}',
            group='payment_callbacks'
        )
        logger.info(f"Enqueued task {task_id} for transaction_id {transaction_id}")

        return Response({
            "status": "success",
            "detail": f"Payment callback enqueued for processing (task_id: {task_id})"
        }, status=status.HTTP_200_OK)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        return Response({"error": "Invalid JSON format in request body"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Callback processing error: {str(e)}")
        return Response({"error": "Callback processing failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def zenopay_callback_compatible(request):
    return zenopay_callback(request)