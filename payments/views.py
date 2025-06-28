import json
import re
import traceback
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import uuid
import logging
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from .models import PaymentService, Payment, Wallet
from .serializers import PaymentServiceSerializer, PaymentSerializer, WalletSerializer, WalletDepositSerializer
from shops.models import Shop, Subscription, UserOffer
from marketplace.models import Brand, Product
from estates.models import Property
from django_pesapalv3.views import PaymentRequestMixin

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


class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='deposit')
    def deposit(self, request):
        """Initiate a Pesapal v3 deposit to fund the wallet."""
        logger.debug(f"Deposit request received: {request.data}")
        logger.debug(f"Request headers: {dict(request.headers)}")

        serializer = WalletDepositSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']
        mobile_number = serializer.validated_data['mobile_number']
        provider = serializer.validated_data['provider']
        order_id = uuid.uuid4().hex

        try:
            # Prepare Pesapal payment request
            payment_data = {
                'id': order_id,
                'currency': 'TZS',
                'amount': float(amount),
                'description': f"Wallet deposit for {request.user.username}",
                'callback_url': settings.PESAPAL_CALLBACK_URL,
                'notification_id': settings.PESAPAL_NOTIFICATION_ID,
                'billing_address': {
                    'email_address': request.user.email or 'no-email@example.com',
                    'phone_number': str(mobile_number),  # Ensure string format
                    'first_name': request.user.username,
                }
            }
            logger.debug(f"Payment data: {payment_data}")

            # Initiate payment using django-pesapal v3
            payment_request = PaymentRequestMixin()
            response = payment_request.submit_order_request(**payment_data)
            logger.debug(f"Pesapal API response: {response}")

            if response.get('status') == '200':
                with transaction.atomic():
                    payment = Payment.objects.create(
                        user=request.user,
                        amount=amount,
                        status=Payment.PaymentStatus.PENDING,
                        transaction_id=order_id,
                        external_id=response.get('order_tracking_id'),
                        provider=provider,
                        account_number=str(mobile_number),
                        payment_type=Payment.PaymentType.DEPOSIT
                    )
                    logger.info(f"Deposit payment created: order_id {order_id}")
                return Response({
                    "transaction_id": payment.transaction_id,
                    "amount": str(amount),
                    "redirect_url": response.get('redirect_url'),
                    "message": "Deposit initiated. Please complete the transaction via the provided URL."
                }, status=status.HTTP_201_CREATED)
            else:
                error_message = response.get('error', {}).get('message', 'Deposit initiation failed.')
                logger.error(f"Pesapal deposit failed: {error_message}")
                return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

        except requests.RequestException as e:
            logger.error(f"Pesapal API request failed: {str(e)}\nTraceback: {traceback.format_exc()}")
            return Response({"error": f"Payment service unavailable: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.error(f"Deposit initiation error: {str(e)}\nTraceback: {traceback.format_exc()}")
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='check-payment-status/(?P<transaction_id>[^/.]+)')
    def check_payment_status(self, request, transaction_id):
        """Check the status of a Pesapal v3 payment."""
        logger.debug(f"Checking payment status for transaction_id: {transaction_id}")
        payment = get_object_or_404(Payment, transaction_id=transaction_id, user=request.user)
        try:
            # Check order status using django-pesapal v3
            payment_request = PaymentRequestMixin()
            response = payment_request.get_transaction_status(payment.external_id)
            logger.debug(f"Pesapal order status response: {response}")

            if response.get('status') == '200':
                payment_status = response.get('payment_status_description')
                reference = response.get('payment_reference')

                with transaction.atomic():
                    if payment.status != Payment.PaymentStatus.PENDING:
                        logger.info(f"Payment {payment.id} already processed: {payment.status}")
                        return Response({
                            "transaction_id": transaction_id,
                            "status": payment.status,
                            "reference": reference
                        }, status=status.HTTP_200_OK)

                    if payment_status == 'Completed':
                        if payment.payment_type == Payment.PaymentType.DEPOSIT:
                            payment.user.wallet.add_funds(
                                amount=payment.amount,
                                transaction_id=transaction_id,
                                external_id=reference,
                                provider=payment.provider,
                                account_number=payment.account_number,
                                description=f"Pesapal deposit for user {payment.user.username}"
                            )
                            payment.status = Payment.PaymentStatus.COMPLETED
                            payment.save()
                            logger.info(f"Deposit {payment.id} completed for user {payment.user.username}, amount: {payment.amount} TZS")
                        else:
                            logger.error(f"Invalid payment type: {payment.payment_type}")
                            return Response({"error": "Invalid payment type"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        payment.status = Payment.PaymentStatus.FAILED
                        payment.save()
                        logger.error(f"Deposit {payment.id} failed for user {payment.user.username}: {payment_status}")

                    return Response({
                        "transaction_id": transaction_id,
                        "status": payment.status,
                        "reference": reference
                    }, status=status.HTTP_200_OK)
            else:
                error_message = response.get('error', {}).get('message', 'Unknown error')
                logger.error(f"Order status check failed: {error_message}")
                return Response({"error": "Unable to fetch payment status"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except requests.RequestException as e:
            logger.error(f"Order status check failed: {str(e)}\nTraceback: {traceback.format_exc()}")
            return Response({"error": f"Payment service unavailable: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.error(f"Order status check error: {str(e)}\nTraceback: {traceback.format_exc()}")
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_product_payment(request):
    """Initiate a payment for product activation using wallet."""
    product_id = request.data.get('product_id')
    if not product_id:
        logger.error("Product ID not provided.")
        return Response({"error": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    product = get_object_or_404(Product, id=product_id, owner=request.user)
    shop = getattr(request.user, 'shop', None)
    offer = UserOffer.objects.filter(user=request.user).first()

    if product.is_active:
        logger.info(f"Product {product_id} already active for user {request.user.username}.")
        return Response({"detail": "Product already active."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            if shop and shop.is_subscription_active():
                product.is_active = True
                product.save()
                logger.info(f"Product {product_id} activated via shop subscription for user {request.user.username}.")
                return Response({"detail": "Product activated via shop subscription."}, status=status.HTTP_200_OK)

            free_products_remaining = offer.free_products_remaining if offer else 0
            if offer and offer.consume_free_product():
                product.is_active = True
                product.save()
                logger.info(f"Product {product_id} activated using free offer for user {request.user.username}.")
                return Response({
                    "detail": "Product activated using free offer.",
                    "free_products_remaining": offer.free_products_remaining
                }, status=status.HTTP_200_OK)

            product.activate_product()
            logger.info(f"Product {product_id} activated for user {request.user.username}")
            return Response({
                "detail": "Product activated.",
                "product_id": product.id,
                "is_active": product.is_active,
                "free_products_remaining": free_products_remaining
            }, status=status.HTTP_200_OK)
    except ValidationError as e:
        logger.error(f"Product activation failed for product {product_id}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error during product activation {product_id}: {str(e)}")
        return Response({"error": "Activation failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_estate_payment(request):
    """Initiate a payment for property activation using wallet."""
    property_id = request.data.get('property_id')
    if not property_id:
        logger.error("Property ID not provided.")
        return Response({"error": "Property ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    property_instance = get_object_or_404(Property, id=property_id, owner=request.user)
    offer = UserOffer.objects.filter(user=request.user).first()

    if property_instance.is_available:
        logger.info(f"Property {property_id} already available for user {request.user.username}.")
        return Response({"detail": "Property already activated."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            free_estates_remaining = offer.free_estates_remaining if offer else 0
            if offer and offer.consume_free_estate():
                property_instance.is_available = True
                property_instance.save()
                logger.info(f"Property {property_id} activated using free offer for user {request.user.username}.")
                return Response({
                    "detail": "Property activated using free offer.",
                    "property_id": property_instance.id,
                    "is_available": property_instance.is_available,
                    "free_estates_remaining": offer.free_estates_remaining
                }, status=status.HTTP_200_OK)

            payment_amount = (property_instance.price * Decimal('0.01')).quantize(Decimal('0.01'))
            payment = Payment.objects.create(
                user=request.user,
                amount=payment_amount,
                status=Payment.PaymentStatus.PENDING,
                content_type=ContentType.objects.get_for_model(Property),
                object_id=property_instance.id,
                payment_type=Payment.PaymentType.ESTATE,
                service=None
            )
            payment.process_payment()
            property_instance.is_available = True
            property_instance.save()
            logger.info(f"Property {property_id} activated for user {request.user.username}, amount: {payment_amount} TZS")
            return Response({
                "detail": "Property activated.",
                "property_id": property_instance.id,
                "is_available": property_instance.is_available,
                "free_estates_remaining": free_estates_remaining
            }, status=status.HTTP_200_OK)
    except ValidationError as e:
        logger.error(f"Property activation failed for property {property_id}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error during property activation {property_id}: {str(e)}")
        return Response({"error": "Activation failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_shop_subscription_payment(request):
    """Initiate a payment for a 1-month shop subscription using wallet."""
    shop_id = request.data.get('shop_id')
    if not shop_id:
        logger.error("Shop ID not provided.")
        return Response({"error": "Shop ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    shop = get_object_or_404(Shop, id=shop_id, user=request.user)
    subscription = getattr(shop, 'subscription', None)

    if not subscription:
        logger.error(f"No subscription found for shop {shop_id}")
        return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)

    if subscription.status == 'active' and subscription.end_date > timezone.now():
        logger.info(f"Shop {shop_id} subscription already active for user {request.user.username}.")
        return Response({"detail": "Subscription already active."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment_service = PaymentService.objects.get(name=PaymentService.ServiceName.SHOP_SUBSCRIPTION)
        with transaction.atomic():
            payment = Payment.objects.create(
                user=request.user,
                service=payment_service,
                amount=payment_service.price,
                status=Payment.PaymentStatus.PENDING,
                content_type=ContentType.objects.get_for_model(Subscription),
                object_id=subscription.id,
                payment_type=Payment.PaymentType.SUBSCRIPTION
            )
            payment.process_payment()
            subscription.status = 'active'
            subscription.start_date = timezone.now()
            subscription.end_date = subscription.start_date + timedelta(days=30)
            subscription.save()
            logger.info(f"Subscription activated for shop {shop_id}, user {request.user.username}, amount: {payment_service.price} TZS")
            return Response({
                "detail": "Subscription activated.",
                "shop_id": shop.id,
                "subscription_status": subscription.status,
                "end_date": subscription.end_date
            }, status=status.HTTP_200_OK)
    except PaymentService.DoesNotExist:
        logger.error("Shop subscription service not found")
        return Response({"error": "Shop subscription service not available."}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        logger.error(f"Subscription activation failed for shop {shop_id}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error during subscription activation for shop {shop_id}: {str(e)}")
        return Response({"error": "Activation failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_brand_payment(request):
    """Initiate a payment for brand creation using wallet."""
    brand_id = request.data.get('brand_id')
    if not brand_id:
        logger.error("Brand ID not provided.")
        return Response({"error": "Brand ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    brand = get_object_or_404(Brand, id=brand_id, created_by=request.user)

    if brand.is_active:
        logger.info(f"Brand {brand_id} already active for user {request.user.username}.")
        return Response({"detail": "Brand already active."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment_service = PaymentService.objects.get(name=PaymentService.ServiceName.BRAND_CREATION)
        with transaction.atomic():
            payment = Payment.objects.create(
                user=request.user,
                service=payment_service,
                amount=payment_service.price,
                status=Payment.PaymentStatus.PENDING,
                content_type=ContentType.objects.get_for_model(Brand),
                object_id=brand.id,
                payment_type=Payment.PaymentType.BRAND
            )
            payment.process_payment()
            brand.is_active = True
            brand.save()
            logger.info(f"Brand {brand_id} activated for user {request.user.username}, amount: {payment_service.price} TZS")
            return Response({
                "detail": "Brand activated.",
                "brand_id": brand.id,
                "is_active": brand.is_active
            }, status=status.HTTP_200_OK)
    except PaymentService.DoesNotExist:
        logger.error("Brand creation service not found")
        return Response({"error": "Brand creation service not available."}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        logger.error(f"Brand activation failed for brand {brand_id}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error during brand activation {brand_id}: {str(e)}")
        return Response({"error": "Activation failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def pesapal_callback(request):
    """Handle Pesapal v3 payment callback for wallet deposits."""
    logger.debug(f"Callback received from IP: {request.META.get('REMOTE_ADDR')}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Raw callback data: {request.GET if request.method == 'GET' else request.body}")

    try:
        # Extract Pesapal callback parameters
        order_tracking_id = request.GET.get('OrderTrackingId') if request.method == 'GET' else request.POST.get('OrderTrackingId')
        order_merchant_reference = request.GET.get('OrderMerchantReference') if request.method == 'GET' else request.POST.get('OrderMerchantReference')
        order_notification_type = request.GET.get('OrderNotificationType') if request.method == 'GET' else request.POST.get('OrderNotificationType')

        if not all([order_tracking_id, order_merchant_reference, order_notification_type]):
            logger.error(f"Missing required fields: tracking_id={order_tracking_id}, merchant_reference={order_merchant_reference}")
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            payment = get_object_or_404(Payment, transaction_id=order_merchant_reference, external_id=order_tracking_id)
            if payment.status != Payment.PaymentStatus.PENDING:
                logger.info(f"Payment {payment.id} already processed: {payment.status}")
                return Response({"status": "success", "detail": "Payment already processed"}, status=status.HTTP_200_OK)

            # Verify payment status using django-pesapal v3
            payment_request = PaymentRequestMixin()
            response = payment_request.get_transaction_status(order_tracking_id)
            payment_status = response.get('payment_status_description')

            if payment_status == 'Completed':
                if payment.payment_type == Payment.PaymentType.DEPOSIT:
                    payment.user.wallet.add_funds(
                        amount=payment.amount,
                        transaction_id=order_merchant_reference,
                        external_id=order_tracking_id,
                        provider=payment.provider,
                        account_number=payment.account_number,
                        description=f"Pesapal deposit for user {payment.user.username}"
                    )
                    payment.status = Payment.PaymentStatus.COMPLETED
                    payment.save()
                    logger.info(f"Deposit {payment.id} completed for user {payment.user.username}, amount: {payment.amount} TZS")
                else:
                    logger.error(f"Invalid payment type for callback: {payment.payment_type}")
                    return Response({"error": "Invalid payment type for callback"}, status=status.HTTP_400_BAD_REQUEST)
            elif payment_status in ['Failed', 'Invalid']:
                payment.status = Payment.PaymentStatus.FAILED
                payment.save()
                logger.error(f"Deposit {payment.id} failed for user {payment.user.username}: {payment_status}")

            return Response({
                "status": "success",
                "detail": f"Deposit callback processed for order_id: {order_merchant_reference}"
            }, status=status.HTTP_200_OK)

    except Payment.DoesNotExist:
        logger.error(f"Payment not found for order_id: {order_merchant_reference}")
        return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Callback processing error: {str(e)}")
        return Response({"error": "Callback processing failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)