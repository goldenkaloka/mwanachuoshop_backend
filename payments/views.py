import json
from django.conf import settings
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import uuid
import logging
from .models import PaymentService, Payment
from .serializers import PaymentServiceSerializer, PaymentSerializer
from shops.models import Subscription

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
    shop = getattr(request.user, 'shop', None)
    offer = getattr(request.user, 'offer', None)

    if (shop and shop.is_subscription_active()) or (offer and offer.free_products_remaining > 0):
        logger.info(f"User {request.user.username} can create products for free.")
        return Response({"detail": "You can create products for free."}, status=status.HTTP_200_OK)

    try:
        payment_service = PaymentService.objects.get(name=PaymentService.ServiceName.PRODUCT_CREATION)
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
        logger.info(f"Initiating product payment for user {request.user.username}, service {payment_service.name}, external_id {external_id}")
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
            account_number=mobile_number
        )
        logger.info(f"Payment created: transaction_id {payment.transaction_id}, status {payment.status}")

        return Response({
            "transaction_id": payment.transaction_id,
            "external_id": payment.external_id,
            "message": "Payment initiated. Please complete the transaction via your mobile device."
        }, status=status.HTTP_201_CREATED)

    except PaymentService.DoesNotExist:
        logger.error("Product creation service not found")
        return Response({"error": "Product creation service not available."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_estate_payment(request):
    shop = getattr(request.user, 'shop', None)
    offer = getattr(request.user, 'offer', None)

    if (shop and shop.is_subscription_active()) or (offer and offer.free_estates_remaining > 0):
        logger.info(f"User {request.user.username} can create properties for free.")
        return Response({"detail": "You can create properties for free."}, status=status.HTTP_200_OK)

    try:
        payment_service = PaymentService.objects.get(name=PaymentService.ServiceName.ESTATE_CREATION)
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
        logger.info(f"Initiating estate payment for user {request.user.username}, service {payment_service.name}, external_id {external_id}")
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
            account_number=mobile_number
        )
        logger.info(f"Payment created: transaction_id {payment.transaction_id}, status {payment.status}")

        return Response({
            "transaction_id": payment.transaction_id,
            "external_id": payment.external_id,
            "message": "Payment initiated. Please complete the transaction via your mobile device."
        }, status=status.HTTP_201_CREATED)

    except PaymentService.DoesNotExist:
        logger.error("Estate creation service not found")
        return Response({"error": "Estate creation service not available."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        return Response({"detail": "Shop subscription is already active."}, status=status.HTTP_200_OK)

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
            subscription=subscription
        )
        logger.info(f"Payment created: transaction_id {payment.transaction_id}, status {payment.status}")

        return Response({
            "transaction_id": payment.transaction_id,
            "external_id": payment.external_id,
            "message": "Payment initiated. Please complete the transaction via your mobile device."
        }, status=status.HTTP_201_CREATED)

    except PaymentService.DoesNotExist:
        logger.error("Shop subscription service not found")
        return Response({"error": "Shop subscription service not available."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def azampay_callback(request):
    # Log request metadata
    logger.debug(f"Callback received from IP: {request.META.get('REMOTE_ADDR')}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Log raw request body
    raw_body = request.body
    logger.debug(f"Raw callback request body: {raw_body}")

    try:
        # Parse JSON payload
        data = json.loads(raw_body) if raw_body else {}
        logger.debug(f"Parsed callback payload: {data}")
        logger.debug(f"Payload keys: {list(data.keys())}")

        # Handle variable field names
        transaction_id = data.get('transactionId') or data.get('reference')
        external_id = data.get('externalId') or data.get('utilityref')
        status_value = data.get('status') or data.get('transactionstatus')

        # Validate required fields
        required_fields = ['reference', 'utilityref', 'transactionstatus']
        missing = [f for f in required_fields if f not in data]
        if missing:
            logger.error(f"Missing required fields: {missing}")
            return Response({"status": "success", "warning": f"Missing fields: {missing}"}, status=status.HTTP_200_OK)

        if not all([transaction_id, external_id, status_value]):
            logger.error(f"Missing required values: transaction_id={transaction_id}, external_id={external_id}, status={status_value}")
            return Response({"status": "success", "warning": "Missing required field values"}, status=status.HTTP_200_OK)

        try:
            payment = Payment.objects.get(external_id=external_id, transaction_id=transaction_id)
            logger.debug(f"Callback received for transaction_id {transaction_id}, status {status_value}")
            if status_value.lower() == 'success':
                payment.status = Payment.PaymentStatus.COMPLETED
                if payment.service.name == PaymentService.ServiceName.SHOP_SUBSCRIPTION:
                    payment.subscription.extend_subscription()
                logger.debug(f"Payment {payment.id} marked as completed")
            else:
                payment.status = Payment.PaymentStatus.FAILED
                logger.debug(f"Payment {payment.id} marked as failed")
            payment.save()
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for transaction_id {transaction_id}, external_id {external_id}")
            return Response({"status": "success", "warning": f"Payment not found for transaction_id {transaction_id}"}, status=status.HTTP_200_OK)

        return Response({"status": "success", "detail": f"Payment {payment.id} updated to {payment.status}"}, status=status.HTTP_200_OK)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        return Response({"error": "Invalid JSON format in request body"}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def azampay_callback_compatible(request):
    return azampay_callback(request)