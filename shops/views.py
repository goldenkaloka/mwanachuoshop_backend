from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Shop, ShopMedia, Promotion, Event, Services, UserOffer, Subscription
from .serializers import ShopSerializer, ShopMediaSerializer, PromotionSerializer, EventSerializer, ServicesSerializer, UserOfferSerializer, SubscriptionSerializer
from .permissions import IsOwnerWithActiveSubscriptionOrReadOnly
import logging
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from payments.models import PaymentService
from decimal import Decimal
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class ShopRelatedViewSetMixin:
    """
    A mixin for viewsets whose models have a direct ForeignKey to a Shop.
    - Filters querysets to show only active/public content or content owned by the user.
    - Checks for shop ownership and active subscription on creation.
    """
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

    def get_queryset(self):
        # The base queryset must be defined in the viewset's `queryset` attribute.
        queryset = super().get_queryset().select_related('shop__user', 'shop__subscription')
        user = self.request.user

        # Base filter for what is considered "publicly active"
        active_q = Q(
            shop__subscription__status=Subscription.Status.ACTIVE,
            shop__subscription__end_date__gt=timezone.now(),
            shop__is_active=True
        )

        if not user.is_authenticated:
            return queryset.filter(active_q)
        
        if user.is_staff:
            return queryset

        # Authenticated non-staff see their own content + active public content
        owner_q = Q(shop__user=user)
        return queryset.filter(owner_q | active_q).distinct()

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.user != self.request.user:
            raise PermissionDenied("You can only add items to your own shop.")
        if not shop.is_subscription_active():
            raise PermissionDenied("Cannot add items to a shop with an inactive subscription.")
        serializer.save()

class ShopViewSet(viewsets.ModelViewSet):
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

    def get_queryset(self):
        """
        Return shops based on user authentication and subscription status.
        - Unauthenticated users: Only active shops (with active subscriptions).
        - Authenticated non-staff: Their own shops (active or inactive) plus other active shops.
        - Staff: All shops.
        """
        queryset = Shop.objects.select_related('user', 'subscription').prefetch_related(
            'media', 'services', 'promotions', 'events'
        )
        now = timezone.now()
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                subscription__status=Subscription.Status.ACTIVE,
                subscription__end_date__gt=now,
                is_active=True
            )
        elif not self.request.user.is_staff:
            queryset = queryset.filter(
                (Q(user=self.request.user)) | 
                (Q(subscription__status=Subscription.Status.ACTIVE) & Q(subscription__end_date__gt=now) & Q(is_active=True))
            )
        return queryset

    def perform_create(self, serializer):
        """
        Create a shop and assign it to the authenticated user.
        Free one-month subscription is created via post_save signal.
        """
        with transaction.atomic():
            shop = serializer.save(user=self.request.user)
            logger.info(f"Created shop {shop.id} for user {self.request.user.username}")

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_shop(self, request):
        """
        Retrieve the authenticated user's shop and its subscription status.
        """
        try:
            shop = Shop.objects.select_related('subscription', 'user').prefetch_related(
                'media', 'services', 'promotions', 'events'
            ).get(user=request.user)
            serializer = self.get_serializer(shop)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Shop.DoesNotExist:
            logger.info(f"No shop found for user {request.user.username}")
            return Response({"detail": "Shop not found."}, status=status.HTTP_404_NOT_FOUND)

class ShopMediaViewSet(ShopRelatedViewSetMixin, viewsets.ModelViewSet):
    queryset = ShopMedia.objects.all()
    serializer_class = ShopMediaSerializer

    def create(self, request, *args, **kwargs):
        # The custom create method can be simplified. DRF's default create
        # handles validation and calls perform_create automatically.
        logger.debug(f"Received request data: {request.data}")
        return super().create(request, *args, **kwargs)

class PromotionViewSet(ShopRelatedViewSetMixin, viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer

class EventViewSet(ShopRelatedViewSetMixin, viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class ServicesViewSet(ShopRelatedViewSetMixin, viewsets.ModelViewSet):
    queryset = Services.objects.all()
    serializer_class = ServicesSerializer

class UserOfferViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserOffer.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='me')
    def me(self, request):
        offer = UserOffer.objects.filter(user=request.user).first()
        if offer:
            serializer = self.get_serializer(offer)
            return Response(serializer.data)
        return Response({'detail': 'No offer found for this user.'}, status=404)

class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related('shop')

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def extend(self, request, pk=None):
        """
        Extend the subscription duration for the authenticated user's shop by 1 month via wallet payment.
        """
        try:
            subscription = self.get_object()
            if subscription.user != request.user:
                raise PermissionDenied("You can only extend your own shop's subscription.")

            with transaction.atomic():
                subscription.activate_subscription()
                logger.info(f"Extended subscription {subscription.id} for shop {subscription.shop.id} by 1 month")
            
            serializer = self.get_serializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PaymentService.DoesNotExist:
            logger.error(f"Shop subscription service not found for subscription {pk}")
            return Response({"error": "Shop subscription service not available."}, status=status.HTTP_404_NOT_FOUND)
        except Subscription.DoesNotExist:
            logger.error(f"Subscription {pk} not found for user {request.user.username}")
            return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Subscription extension failed for subscription {pk}: {str(e)}")
            deposit_url = request.build_absolute_uri(reverse('wallet-deposit'))
            return Response({"error": str(e), "deposit_url": deposit_url}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error extending subscription {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
