from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
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

logger = logging.getLogger(__name__)

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
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                subscription__status=Subscription.Status.ACTIVE,
                subscription__end_date__gt=timezone.now(),
                is_active=True
            )
        elif not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(user=self.request.user) | 
                Q(
                    subscription__status=Subscription.Status.ACTIVE,
                    subscription__end_date__gt=timezone.now(),
                    is_active=True
                )
            )
        return queryset

    def perform_create(self, serializer):
        """
        Create a shop and assign it to the authenticated user.
        Trial subscription is created via post_save signal.
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

class ShopMediaViewSet(viewsets.ModelViewSet):
    queryset = ShopMedia.objects.all()
    serializer_class = ShopMediaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset().select_related('shop__subscription')
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                shop__subscription__status=Subscription.Status.ACTIVE,
                shop__subscription__end_date__gt=timezone.now(),
                shop__is_active=True
            )
        elif not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(shop__user=self.request.user) | 
                Q(
                    shop__subscription__status=Subscription.Status.ACTIVE,
                    shop__subscription__end_date__gt=timezone.now(),
                    shop__is_active=True
                )
            )
        return queryset

    def create(self, request, *args, **kwargs):
        logger.debug(f"Received request data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"ShopMediaViewSet create error: {serializer.errors}, data: {request.data}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        try:
            shop = serializer.validated_data['shop']
            if shop.user != self.request.user:
                raise PermissionDenied("You can only add media to your own shops.")
            if not shop.is_subscription_active():
                raise PermissionDenied("Cannot add media to a shop with an inactive subscription.")
            serializer.save()
        except Exception as e:
            logger.error(f"ShopMediaViewSet perform_create error: {str(e)}, data: {serializer.validated_data}")
            raise

class PromotionViewSet(viewsets.ModelViewSet):
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

    def get_queryset(self):
        queryset = Promotion.objects.select_related('shop__subscription')
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                shop__subscription__status=Subscription.Status.ACTIVE,
                shop__subscription__end_date__gt=timezone.now(),
                shop__is_active=True
            )
        elif not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(shop__user=self.request.user) | 
                Q(
                    shop__subscription__status=Subscription.Status.ACTIVE,
                    shop__subscription__end_date__gt=timezone.now(),
                    shop__is_active=True
                )
            )
        return queryset

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.user != self.request.user:
            raise PermissionDenied("You can only add promotions to your own shops.")
        if not shop.is_subscription_active():
            raise PermissionDenied("Cannot add promotions to a shop with an inactive subscription.")
        serializer.save()

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

    def get_queryset(self):
        queryset = Event.objects.select_related('shop__subscription')
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                shop__subscription__status=Subscription.Status.ACTIVE,
                shop__subscription__end_date__gt=timezone.now(),
                shop__is_active=True
            )
        elif not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(shop__user=self.request.user) | 
                Q(
                    shop__subscription__status=Subscription.Status.ACTIVE,
                    subscription__end_date__gt=timezone.now(),
                    shop__is_active=True
                )
            )
        return queryset

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.user != self.request.user:
            raise PermissionDenied("You can only add events to your own shops.")
        if not shop.is_subscription_active():
            raise PermissionDenied("Cannot add events to a shop with an inactive subscription.")
        serializer.save()

class ServicesViewSet(viewsets.ModelViewSet):
    serializer_class = ServicesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

    def get_queryset(self):
        queryset = Services.objects.select_related('shop__subscription')
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                shop__subscription__status=Subscription.Status.ACTIVE,
                shop__subscription__end_date__gt=timezone.now(),
                shop__is_active=True
            )
        elif not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(shop__user=self.request.user) | 
                Q(
                    shop__subscription__status=Subscription.Status.ACTIVE,
                    shop__subscription__end_date__gt=timezone.now(),
                    shop__is_active=True
                )
            )
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Return a list of services, ensuring a 200 response even if the queryset is empty.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.user != self.request.user:
            raise PermissionDenied("You can only add services to your own shops.")
        if not shop.is_subscription_active():
            raise PermissionDenied("Cannot add services to a shop with an inactive subscription.")
        serializer.save()

class UserOfferViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserOffer.objects.filter(user=self.request.user)

class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related('shop')

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def extend(self, request, pk=None):
        """
        Extend the subscription duration for the authenticated user's shop by 1 month.
        """
        try:
            subscription = self.get_object()
            if subscription.user != request.user:
                raise PermissionDenied("You can only extend your own shop's subscription.")

            with transaction.atomic():
                subscription.extend_subscription(months=1)
                logger.info(f"Extended subscription {subscription.id} for shop {subscription.shop.id} by 1 month")
            
            serializer = self.get_serializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            logger.error(f"Subscription {pk} not found for user {request.user.username}")
            return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error extending subscription {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)