import json
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
    """Initiate a payment for product activation (0.1% of product price, minimum $1.00)."""
    product_id = request.data.get('product_id')
    if not product_id:
        logger.error("Product ID not provided.")
        return Response({"error": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    product = get_object_or_404(Product, id=product_id, owner=request.user)
    shop = Shop.objects.filter(user=request.user).first()
    offer = UserOffer.objects.filter(user=request.user).first()

    if product.is_active:
        return Response({"detail": "Product already active."}, status=status.HTTP_400_BAD_REQUEST)

    # Free activation paths
    if shop and shop.is_subscription_active():
        logger.info(f"User {request.user.username} has active shop subscription.")
        product.is_active = True
        product.save()
        return Response({
            "detail": "Product activated via shop subscription."
        }, status=status.HTTP_200_OK)

    if offer and offer.free_products_remaining > 0:
        logger.info(f"User {request.user.username} has free product offers.")
        offer.free_products_remaining -= 1
        offer.save()
        product.is_active = True
        product.save()
        return Response({
            "detail": "Product activated using free offer.",
            "free_products_remaining": offer.free_products_remaining
        }, status=status.HTTP_200_OK)

    # Paid activation: 0.1% of product price, minimum $1.00
    try:
        mobile_number = request.data.get('mobile_number')
        provider = request.data.get('provider', 'Mpesa')

        if not mobile_number:
            logger.error("Mobile number not provided.")
            return Response({"error": "Mobile number is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize provider (case-insensitive)
        provider_map = {
            'mpesa': 'Mpesa',
            'tigo': 'Tigo',
            'airtel': 'Airtel',
            'halopesa': 'Halopesa',
            'halotel': 'Halopesa',  # Map 'halotel' to 'Halopesa'
        }
        normalized_provider = provider_map.get(provider.lower(), provider)
        if normalized_provider not in ['Mpesa', 'Tigo', 'Airtel', 'Halopesa']:
            logger.error(f"Invalid provider: {provider}")
            return Response({"error": f"Invalid provider: {provider}. Must be one of Mpesa, Tigo, Airtel, Halopesa."}, 
                           status=status.HTTP_400_BAD_REQUEST)

        if not settings.AZAMPAY_CLIENT:
            logger.error("AzamPay client not initialized.")
            return Response({"error": "Payment service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Calculate payment amount: 0.1% of product price, minimum $1.00
        payment_amount = max(
            Decimal('1.00'),
            (product.price * Decimal('0.001')).quantize(Decimal('0.01'))
        )
        external_id = str(uuid.uuid4())
        logger.info(f"Initiating product payment for user {request.user.username}, external_id {external_id}, amount {payment_amount}")

        checkout_response = settings.AZAMPAY_CLIENT.mobile_checkout(
            amount=float(payment_amount),
            mobile=mobile_number,
            external_id=external_id,
            provider=normalized_provider
        )
        logger.debug(f"Checkout response: {checkout_response}")

        if not checkout_response.get('success', False):
            logger.error(f"Payment failed: {checkout_response.get('message', 'Unknown error')}")
            return Response(
                {"error": checkout_response.get('message', 'Payment initiation failed.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            amount=payment_amount,
            status=Payment.PaymentStatus.PENDING,
            transaction_id=checkout_response.get('transactionId'),
            external_id=external_id,
            provider=normalized_provider,
            account_number=mobile_number,
            content_type=ContentType.objects.get_for_model(Product),
            object_id=product.id,
            payment_type=Payment.PaymentType.PRODUCT
        )
        logger.info(f"Payment created: transaction_id {payment.transaction_id}, status {payment.status}")

        return Response({
            "transaction_id": payment.transaction_id,
            "amount": str(payment_amount),
            "message": "Payment initiated. Please complete the transaction via your mobile device."
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_estate_payment(request):
    property_id = request.data.get('property_id')
    if not property_id:
        logger.error("Property ID not provided.")
        return Response({"error": "Property ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    property = get_object_or_404(Property, id=property_id, owner=request.user)
    offer = UserOffer.objects.filter(user=request.user).first()

    if property.is_available:
        return Response({"detail": "Property already available."}, status=status.HTTP_400_BAD_REQUEST)

    if offer and offer.free_estates_remaining > 0:
        logger.info(f"User {request.user.username} can create properties for free.")
        property.is_available = True
        property.save()
        offer.free_estates_remaining -= 1
        offer.save()
        return Response({
            "detail": "Property activated for free.",
            "free_estates_remaining": offer.free_estates_remaining
        }, status=status.HTTP_200_OK)

    try:
        mobile_number = request.data.get('mobile_number')
        provider = request.data.get('provider', 'Mpesa')

        if not mobile_number:
            logger.error("Mobile number not provided.")
            return Response({"error": "Mobile number is required."}, status=status.HTTP_400_BAD_REQUEST)

        if provider not in ['Mpesa', 'TigoPesa', 'AirtelMoney', 'HaloPesa']:
            logger.error(f"Invalid provider: {provider}")
            return Response({"error": "Invalid provider."}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.AZAMPAY_CLIENT:
            logger.error("AzamPay client not initialized.")
            return Response({"error": "Payment service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        payment_amount = max(
            Decimal('1.00'),
            (property.price * Decimal('0.001')).quantize(Decimal('0.01'))
        )
        external_id = str(uuid.uuid4())
        logger.info(f"Initiating estate payment for user {request.user.username}, external_id {external_id}, amount {payment_amount}")
        checkout_response = settings.AZAMPAY_CLIENT.mobile_checkout(
            amount=float(payment_amount),
            mobile=mobile_number,
            external_id=external_id,
            provider=provider
        )
        logger.debug(f"Checkout response: {checkout_response}")

        if not checkout_response.get('success', False):
            logger.error(f"Payment failed: {checkout_response.get('message', 'Unknown error')}")
            return Response({"error": checkout_response.get('message', 'Payment initiation failed.')}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.create(
            user=request.user,
            amount=payment_amount,
            status=Payment.PaymentStatus.PENDING,
            transaction_id=checkout_response.get('transactionId'),
            external_id=external_id,
            provider=provider,
            account_number=mobile_number,
            content_type=ContentType.objects.get_for_model(Property),
            object_id=property.id,
            payment_type=Payment.PaymentType.ESTATE
        )
        logger.info(f"Payment created: transaction_id {payment.transaction_id}, status {payment.status}")

        return Response({
            "transaction_id": payment.transaction_id,
            "amount": str(payment_amount),
            "message": "Payment initiated. Please complete the transaction via your mobile device."
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_shop_subscription_payment(request):
    try:
        shop = request.user.shop
        subscription = shop.subscription
    except AttributeError:
        logger.error(f"Shop not found for user {request.user.username}")
        return Response({"error": "Shop not found."}, status=status.HTTP_404_NOT_FOUND)

    if shop.is_subscription_active():
        logger.info(f"Shop subscription already active for user {request.user.username}")
        return Response({"detail": "Shop subscription is already active."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment_service = PaymentService.objects.get(name=PaymentService.ServiceName.SHOP_SUBSCRIPTION)
        mobile_number = request.data.get('mobile_number')
        provider = request.data.get('provider', 'Mpesa')

        if not mobile_number:
            logger.error("Mobile number not provided.")
            return Response({"error": "Mobile number is required."}, status=status.HTTP_400_BAD_REQUEST)

        if provider not in ['Mpesa', 'TigoPesa', 'AirtelMoney', 'HaloPesa']:
            logger.error(f"Invalid provider: {provider}")
            return Response({"error": "Invalid provider."}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.AZAMPAY_CLIENT:
            logger.error("AzamPay client not initialized.")
            return Response({"error": "Payment service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        external_id = str(uuid.uuid4())
        logger.info(f"Initiating shop subscription payment for user {request.user.username}, service {payment_service.name}, external_id {external_id}")
        checkout_response = settings.AZAMPAY_CLIENT.mobile_checkout(
            amount=float(payment_service.price),
            mobile=mobile_number,
            external_id=external_id,
            provider=provider
        )
        logger.debug(f"Checkout response: {checkout_response}")

        if not checkout_response.get('success', False):
            logger.error(f"Payment failed: {checkout_response.get('message', 'Unknown error')}")
            return Response({"error": checkout_response.get('message', 'Payment initiation failed.')}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.create(
            user=request.user,
            service=payment_service,
            amount=payment_service.price,
            status=Payment.PaymentStatus.PENDING,
            transaction_id=checkout_response.get('transactionId'),
            external_id=external_id,
            provider=provider,
            account_number=mobile_number,
            content_type=ContentType.objects.get_for_model(Subscription),
            object_id=subscription.id,
            payment_type=Payment.PaymentType.SUBSCRIPTION
        )
        logger.info(f"Payment created: transaction_id {payment.transaction_id}, status {payment.status}")

        return Response({
            "transaction_id": payment.transaction_id,
            "amount": str(payment_service.price),
            "message": "Payment initiated. Please complete the transaction via your mobile device."
        }, status=status.HTTP_201_CREATED)

    except PaymentService.DoesNotExist:
        logger.error("Shop subscription service not found")
        return Response({"error": "Shop subscription service not available."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def azampay_callback(request):
    logger.debug(f"Callback received from IP: {request.META.get('REMOTE_ADDR')}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    raw_body = request.body
    logger.debug(f"Raw callback request body: {raw_body}")

    try:
        data = json.loads(raw_body) if raw_body else {}
        logger.debug(f"Parsed callback payload: {data}")
        logger.debug(f"Payload keys: {list(data.keys())}")

        transaction_id = data.get('transactionId') or data.get('reference')
        external_id = data.get('externalId') or data.get('utilityref')
        status_value = data.get('status') or data.get('transactionstatus')

        required_fields = ['reference', 'utilityref', 'transactionstatus']
        missing = [f for f in required_fields if f not in data]
        if missing:
            logger.error(f"Missing required fields: {missing}")
            return Response({"status": "success", "warning": f"Missing fields: {missing}"}, status=status.HTTP_200_OK)

        if not all([transaction_id, external_id, status_value]):
            logger.error(f"Missing required values: transaction_id={transaction_id}, external_id={external_id}, status={status_value}")
            return Response({"status": "success", "warning": "Missing required field values"}, status=status.HTTP_200_OK)

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

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def azampay_callback_compatible(request):
    return azampay_callback(request)