from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import Shop, ShopMedia, Promotion, Event, Services, UserOffer, Subscription
from .serializers import ShopSerializer, ShopMediaSerializer, PromotionSerializer, EventSerializer, ServicesSerializer, UserOfferSerializer, SubscriptionSerializer
import logging

logger = logging.getLogger(__name__)

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'shop') and hasattr(obj.shop, 'user'):
            return obj.shop.user == request.user
        return False

class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ShopMediaViewSet(viewsets.ModelViewSet):
    queryset = ShopMedia.objects.all()
    serializer_class = ShopMediaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

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
            serializer.save()
        except Exception as e:
            logger.error(f"ShopMediaViewSet perform_create error: {str(e)}, data: {serializer.validated_data}")
            raise

class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.user != self.request.user:
            raise PermissionDenied("You can only add promotions to your own shops.")
        serializer.save()

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.user != self.request.user:
            raise PermissionDenied("You can only add events to your own shops.")
        serializer.save()

class ServicesViewSet(viewsets.ModelViewSet):
    queryset = Services.objects.all()
    serializer_class = ServicesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.user != self.request.user:
            raise PermissionDenied("You can only add services to your own shops.")
        serializer.save()

class UserOfferViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserOfferSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return UserOffer.objects.filter(user=self.request.user)

class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)