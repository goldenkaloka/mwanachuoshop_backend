from django.http import FileResponse, Http404
from django.urls import reverse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django.shortcuts import get_object_or_404
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import logging
import os
import re
import uuid
from django_q.tasks import async_task

from estates.models import Property, PropertyImage, PropertyType
from estates.serializers import PropertyImageSerializer, PropertySerializer, PropertyTypeSerializer
from estates.pagination import StandardPagePagination
from shops.models import UserOffer
from payments.models import Payment

logger = logging.getLogger(__name__)

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user.is_staff
        elif hasattr(obj, 'property'):
            return obj.property.owner == request.user or request.user.is_staff
        return False

class PropertyTypeViewSet(viewsets.ModelViewSet):
    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer
    pagination_class = None
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    pagination_class = StandardPagePagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_available', 'property_type', 'video_status']
    search_fields = ['title', 'location']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'serve_hls_playlist', 'serve_hls_segment']:
            return [permissions.AllowAny()]
        elif self.action in ['create', 'confirm_property_creation']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def create(self, request, *args, **kwargs):
        logger.info(f"Creating property for user {request.user.username}. Request data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = request.user
            offer = UserOffer.objects.filter(user=user).first()
            is_available = False
            free_estates_remaining = 0  # Default to 0 if no offer

            # Check if user has a free offer
            if offer and offer.free_estates_remaining > 0:
                logger.info(f"User {user.username} has {offer.free_estates_remaining} free offers.")
                is_available = True
                offer.free_estates_remaining -= 1
                offer.save()
                free_estates_remaining = offer.free_estates_remaining

            # Save property
            serializer.save(owner=user, is_available=is_available)
            instance = serializer.instance
            response_data = {
                'id': instance.id,
                'property_id': instance.id,
                'is_available': is_available,
                'payment_required': not is_available,
                'free_estates_remaining': free_estates_remaining,
                **self.get_serializer(instance, context={'exclude_images': True}).data
            }

            if is_available:
                response_data.update({
                    'message': "Property created and activated using free offer.",
                })
            else:
                response_data.update({
                    'message': "Property created. Please call confirm-property-creation to activate with payment.",
                    'confirm_url': request.build_absolute_uri(reverse('property-confirm-property-creation'))
                })

            headers = self.get_success_headers(response_data)
            logger.info(f"Property {instance.id} created for user {user.username}. Available: {is_available}, Free offers left: {free_estates_remaining}")
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        
        with transaction.atomic():
            if serializer.validated_data.get('is_available', instance.is_available) and not instance.is_available:
                offer = UserOffer.objects.filter(user=user).first()
                has_paid = Payment.objects.filter(
                    user=user,
                    payment_type=Payment.PaymentType.ESTATE,
                    status=Payment.PaymentStatus.COMPLETED,
                    content_type=ContentType.objects.get_for_model(Property),
                    object_id=instance.id
                ).exists()
                if not (offer and offer.free_estates_remaining > 0) and not has_paid:
                    logger.error(f"User {user.username} attempted to set property {instance.id} is_available=True without offer or payment.")
                    raise permissions.PermissionDenied("Free offer or payment required to make property available.")
            
            serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset()
        my_properties = self.request.query_params.get('my_properties', 'false').lower() == 'true'
        has_video = self.request.query_params.get('has_video', 'false').lower() == 'true'
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if my_properties:
            if not self.request.user.is_authenticated:
                raise permissions.PermissionDenied("Authentication required for user-specific properties.")
            queryset = queryset.filter(owner=self.request.user)
        elif not self.request.user.is_staff:
            queryset = queryset.filter(is_available=True)
            
        if has_video:
            queryset = queryset.exclude(video__isnull=True).filter(video_status='Completed')
            
        if min_price is not None:
            try:
                queryset = queryset.filter(price__gte=int(min_price))
            except ValueError:
                pass
        if max_price is not None:
            try:
                queryset = queryset.filter(price__lte=int(max_price))
            except ValueError:
                pass
                
        return queryset.select_related('owner', 'property_type').prefetch_related('images')

    @action(detail=False, methods=['post'], url_path='confirm-property-creation',
            permission_classes=[permissions.IsAuthenticated])
    def confirm_property_creation(self, request):
        """Activate a property using payment"""
        logger.info(f"Confirm property creation request for user {request.user.username}: {request.data}")
        property_id = request.data.get('property_id')
        transaction_id = request.data.get('transaction_id')

        if not property_id:
            logger.error("Property ID not provided.")
            return Response(
                {"error": "Property ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            try:
                property_instance = get_object_or_404(Property, id=property_id, owner=request.user)
            except Http404:
                logger.error(f"Property {property_id} not found for user {request.user.username}")
                return Response(
                    {"error": "Property not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if property_instance.is_available:
                logger.warning(f"Property {property_id} is already activated for user {request.user.username}")
                return Response(
                    {"detail": "Property is already activated.", "property_id": property_instance.id},
                    status=status.HTTP_200_OK
                )

            user = request.user

            # Paid activation
            if not transaction_id:
                payment_amount = max(
                    Decimal('1.00'),
                    (property_instance.price * Decimal('0.01')).quantize(Decimal('0.01'))
                )
                logger.info(f"Payment required for property {property_id}: amount {payment_amount}")
                return Response(
                    {
                        "payment_required": True,
                        "amount": str(payment_amount),
                        "property_id": property_instance.id,
                        "payment_url": request.build_absolute_uri(reverse('create-estate-payment')),
                        "message": "Please initiate payment via create-estate-payment."
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )

            try:
                payment = Payment.objects.select_for_update().get(
                    transaction_id=transaction_id,
                    status=Payment.PaymentStatus.COMPLETED,
                    user=user,
                    content_type=ContentType.objects.get_for_model(Property),
                    object_id=property_instance.id
                )
                property_instance.is_available = True
                property_instance.save()
                logger.info(f"Activated property {property_id} via payment {transaction_id}")
                return Response(
                    {"detail": "Property activated via payment", "property_id": property_instance.id},
                    status=status.HTTP_200_OK
                )
            except Payment.DoesNotExist:
                logger.error(f"No completed payment found for transaction_id {transaction_id}, property {property_id}")
                return Response(
                    {"error": "Invalid or incomplete payment"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Payment verification failed for property {property_id}: {str(e)}")
                return Response(
                    {"error": f"Payment processing error: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['exclude_images'] = self.request.query_params.get('exclude_images', 'false').lower() == 'true'
        return context

    @action(detail=True, methods=['get'], url_path='playlist', url_name='property-playlist')
    def serve_hls_playlist(self, request, pk=None):
        logger.info(f"Attempting to serve HLS playlist for Property ID {pk}")
        try:
            property_instance = get_object_or_404(Property, pk=pk, video_status='Completed')
        except Http404:
            logger.warning(f"Property ID {pk} not found or video_status not 'Completed'.")
            return Response({"error": "Playlist not found or video processing not complete."}, status=status.HTTP_404_NOT_FOUND)

        try:
            if not property_instance.hls_playlist:
                logger.error(f"Property ID {pk} has no HLS playlist path defined.")
                return Response({"error": "HLS playlist path not configured."}, status=status.HTTP_404_NOT_FOUND)

            hls_playlist_path = os.path.join(settings.MEDIA_ROOT, str(property_instance.hls_playlist))
            if not os.path.exists(hls_playlist_path):
                logger.error(f"HLS playlist file not found at {hls_playlist_path}")
                return Response({"error": "HLS playlist file not found."}, status=status.HTTP_404_NOT_FOUND)

            logger.info(f"Serving HLS playlist for Property ID {pk}")
            return FileResponse(open(hls_playlist_path, 'rb'), content_type='application/vnd.apple.mpegurl')
        
        except Exception as e:
            logger.error(f"Failed to serve HLS playlist for Property ID {pk}: {str(e)}", exc_info=True)
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path=r'segments/(?P<segment_name>[^/]+\.ts)$')
    def serve_hls_segment(self, request, pk=None, segment_name=None):
        logger.info(f"Segment request: pk={pk}, segment_name={segment_name}")
        try:
            property_instance = get_object_or_404(Property, pk=pk, video_status='Completed')
        except Http404:
            logger.warning(f"Property ID {pk} not found or video_status not 'Completed'.")
            return Response({"error": "Segment not found or video processing not complete."}, status=status.HTTP_404_NOT_FOUND)

        try:
            if not property_instance.hls_playlist:
                logger.error(f"Property ID {pk} has no HLS playlist path.")
                return Response({"error": "HLS playlist path not configured."}, status=status.HTTP_404_NOT_FOUND)

            hls_directory = os.path.normpath(os.path.dirname(os.path.join(settings.MEDIA_ROOT, str(property_instance.hls_playlist))))
            segment_path = os.path.normpath(os.path.join(hls_directory, segment_name))
            
            if not os.path.exists(segment_path):
                logger.error(f"Segment file not found at {segment_path}")
                return Response({"error": "HLS segment file not found."}, status=status.HTTP_404_NOT_FOUND)
            
            if not os.access(segment_path, os.R_OK):
                logger.error(f"Segment file at {segment_path} is not readable.")
                return Response({"error": "Segment not readable."}, status=status.HTTP_403_FORBIDDEN)

            logger.info(f"Serving segment {segment_name} for Property ID {pk}")
            return FileResponse(open(segment_path, 'rb'), content_type='video/mp2t')
        
        except FileNotFoundError:
            logger.error(f"FileNotFoundError for segment {segment_name}.")
            return Response({"error": "HLS segment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error serving segment {segment_name}: {str(e)}", exc_info=True)
            return Response({"error": f"Failed to process segment: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropertyImageViewSet(viewsets.ModelViewSet):
    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageSerializer
    pagination_class = StandardPagePagination
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def perform_create(self, serializer):
        property_instance = serializer.validated_data.get('property')
        if property_instance.owner != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only add images to your own properties.")
        serializer.save()

    def get_queryset(self):
        return super().get_queryset().select_related('property')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_estate_payment(request):
    """Initiate a payment for property activation (1% of property price, minimum $1.00)."""
    property_id = request.data.get('property_id')
    if not property_id:
        logger.error("Property ID not provided.")
        return Response({"error": "Property ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    property_instance = get_object_or_404(Property, id=property_id, owner=request.user)

    if property_instance.is_available:
        logger.info(f"Property {property_id} already available for user {request.user.username}.")
        return Response({"detail": "Property already available."}, status=status.HTTP_400_BAD_REQUEST)

    # Check for existing pending payment
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

    # Paid activation
    try:
        mobile_number = request.data.get('mobile_number')
        provider = request.data.get('provider', 'Mpesa')

        if not mobile_number:
            logger.error("Mobile number not provided.")
            return Response({"error": "Mobile number is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not re.match(r'^(\+?\d{10,12})$', mobile_number):
            logger.error(f"Invalid mobile number format: {mobile_number}")
            return Response({"error": "Invalid mobile number format. Must be 10-12 digits, starting with + or 0."}, 
                           status=status.HTTP_400_BAD_REQUEST)

        provider_map = {
            'mpesa': 'Mpesa',
            'tigo': 'Tigo',
            'airtel': 'Airtel',
            'halopesa': 'Halopesa',
            'halotel': 'Halopesa',
        }
        normalized_provider = provider_map.get(provider.lower(), provider)
        if normalized_provider not in ['Mpesa', 'Tigo', 'Airtel', 'Halopesa']:
            logger.error(f"Invalid provider: {provider}")
            return Response({"error": f"Invalid provider: {provider}. Must be one of Mpesa, Tigo, Airtel, Halopesa."}, 
                           status=status.HTTP_400_BAD_REQUEST)

        if not settings.ZENOPAY_CLIENT:
            logger.error("ZenoPay client not initialized.")
            return Response({"error": "Payment service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        payment_amount = max(
            Decimal('1.00'),
            (property_instance.price * Decimal('0.01')).quantize(Decimal('0.01'))
        )
        external_id = str(uuid.uuid4())
        logger.info(f"Initiating estate payment for user {request.user.username}, property {property_id}, external_id {external_id}, amount {payment_amount}")

        checkout_response = settings.ZENOPAY_CLIENT.mobile_checkout(
            amount=float(payment_amount),
            mobile=mobile_number,
            external_id=external_id,
            provider=normalized_provider
        )
        logger.debug(f"Checkout response: {checkout_response}")

        if not checkout_response.get('success', False):
            logger.error(f"Payment failed: {checkout_response.get('message', 'Unknown error')}")
            return Response({"error": checkout_response.get('message', 'Payment initiation failed.')}, 
                           status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            payment = Payment.objects.create(
                user=request.user,
                amount=payment_amount,
                status=Payment.PaymentStatus.PENDING,
                transaction_id=checkout_response.get('transaction_id'),
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

    except Exception as e:
        logger.error(f"Payment initiation error for property {property_id}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)