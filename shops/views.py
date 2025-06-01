from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import Shop, ShopMedia, Promotion, Event, Services, UserOffer, Subscription
from .serializers import ShopSerializer, ShopMediaSerializer, PromotionSerializer, EventSerializer, ServicesSerializer, UserOfferSerializer, SubscriptionSerializer
from .permissions import IsOwnerWithActiveSubscriptionOrReadOnly
import logging

logger = logging.getLogger(__name__)

class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ShopMediaViewSet(viewsets.ModelViewSet):
    queryset = ShopMedia.objects.all()
    serializer_class = ShopMediaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

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
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.user != self.request.user:
            raise PermissionDenied("You can only add promotions to your own shops.")
        if not shop.is_subscription_active():
            raise PermissionDenied("Cannot add promotions to a shop with an inactive subscription.")
        serializer.save()

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.user != self.request.user:
            raise PermissionDenied("You can only add events to your own shops.")
        if not shop.is_subscription_active():
            raise PermissionDenied("Cannot add events to a shop with an inactive subscription.")
        serializer.save()

class ServicesViewSet(viewsets.ModelViewSet):
    queryset = Services.objects.all()
    serializer_class = ServicesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerWithActiveSubscriptionOrReadOnly]

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
        return Subscription.objects.filter(user=self.request.user)