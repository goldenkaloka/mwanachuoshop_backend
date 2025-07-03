import logging
import mimetypes
from decimal import Decimal
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import get_object_or_404, reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
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
    filterset_fields = ['is_available', 'property_type']
    search_fields = ['title', 'location']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def create(self, request, *args, **kwargs):
        logger.info(f"Creating property for user {request.user.username}. Request data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = request.user
            offer = UserOffer.objects.filter(user=user).first()
            is_available = False
            free_estates_remaining = offer.free_estates_remaining if offer else 0

            if offer and offer.free_estates_remaining > 0:
                logger.info(f"User {user.username} has {offer.free_estates_remaining} free offers.")
                is_available = True
                offer.free_estates_remaining -= 1
                offer.save()

            instance = serializer.save(
                owner=user,
                is_available=is_available
            )

            if not is_available:
                try:
                    instance.activate_property()
                    is_available = True
                    logger.info(f"Property {instance.id} activated via wallet for user {user.username}")
                except ValidationError as e:
                    logger.error(f"Property activation failed for property {instance.id}: {str(e)}")
                    deposit_url = request.build_absolute_uri(reverse('wallet-deposit'))
                    return Response({
                        "error": str(e),
                        "detail": "Property created but not activated due to payment issue.",
                        "property_id": instance.id,
                        "is_available": False,
                        "deposit_url": deposit_url,
                        "free_estates_remaining": free_estates_remaining
                    }, status=status.HTTP_400_BAD_REQUEST)

            response_status = status.HTTP_201_CREATED
            detail_message = "Property created and activated."

            response_data = {
                'id': instance.id,
                'property_id': instance.id,
                'is_available': is_available,
                'free_estates_remaining': free_estates_remaining,
                'detail': detail_message,
                **self.get_serializer(instance, context={'exclude_images': True}).data
            }
            headers = self.get_success_headers(response_data)
            logger.info(f"Property {instance.id} created for user {user.username}. Available: {is_available}, Free offers left: {free_estates_remaining}")
            return Response(response_data, status=response_status, headers=headers)

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
            instance = serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset()
        my_properties = self.request.query_params.get('my_properties', 'false').lower() == 'true'
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if my_properties:
            if not self.request.user.is_authenticated:
                raise permissions.PermissionDenied("Authentication required for user-specific properties.")
            queryset = queryset.filter(owner=self.request.user)
        elif not self.request.user.is_staff:
            queryset = queryset.filter(is_available=True)
        
        if min_price is not None:
            try:
                queryset = queryset.filter(price__gte=Decimal(min_price))
            except ValueError:
                pass
        if max_price is not None:
            try:
                queryset = queryset.filter(price__lte=Decimal(max_price))
            except ValueError:
                pass
        
        return queryset.select_related('owner', 'property_type').prefetch_related('images')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['exclude_images'] = self.request.query_params.get('exclude_images', 'false').lower() == 'true'
        return context

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
    property_id = request.data.get('property_id')
    if not property_id:
        logger.error("property_id not provided.")
        return Response({"error": "property_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    property_instance = get_object_or_404(Property, id=property_id)

    if property_instance.owner != request.user:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if property_instance.is_available:
        logger.info(f"Property {property_id} already available for user {request.user.username}")
        return Response({"detail": "Property already activated."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            offer = UserOffer.objects.filter(user=request.user).first()
            if offer and offer.free_estates_remaining > 0:
                offer.free_estates_remaining -= 1
                offer.save()
                property_instance.is_available = True
                property_instance.save()
                logger.info(f"Property {property_id} activated using free offer for user {request.user.username}.")
                return Response({
                    "detail": "Property activated using free offer.",
                    "property_id": property_id,
                    "is_available": True,
                    "free_estates_remaining": offer.free_estates_remaining
                }, status=status.HTTP_200_OK)

            property_instance.activate_property()
            logger.info(f"Property {property_id} activated for user {request.user.username}")
            return Response({
                "detail": "Property activated.",
                "property_id": property_id,
                "is_available": True,
                "free_estates_remaining": offer.free_estates_remaining if offer else 0
            }, status=status.HTTP_200_OK)
    except ValidationError as e:
        logger.error(f"Property activation failed for property {property_id}: {str(e)}")
        deposit_url = request.build_absolute_uri(reverse('wallet-deposit'))
        return Response({
            "error": str(e),
            "detail": "Deposit required to activate property.",
            "deposit_url": deposit_url,
            "property_id": property_id,
            "is_available": False,
            "free_estates_remaining": offer.free_estates_remaining if offer else 0
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error during property activation for property {property_id}: {str(e)}")
        return Response({
            "error": "Activation failed due to unexpected error.",
            "detail": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)