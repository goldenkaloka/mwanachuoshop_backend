from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    SubscriptionPlan, 
    ShopSubscription, 
    Shop, 
    ShopMedia, 
    ShopService, 
    ShopPromotion
)
from .serializers import (
    SubscriptionPlanSerializer,
    ShopSubscriptionSerializer,
    ShopSerializer,
    ShopMediaSerializer,
    ShopServiceSerializer,
    ShopPromotionSerializer
)


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()

class ShopSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = ShopSubscription.objects.all()
    serializer_class = ShopSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['shop', 'plan', 'is_active', 'is_trial']

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return self.queryset.filter(shop__owner=self.request.user)

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            shop = serializer.validated_data['shop']
            if shop.owner != self.request.user:
                raise permissions.PermissionDenied("You don't own this shop")
        serializer.save()

class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['owner', 'region', 'is_active', 'is_verified']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('active') == 'true':
            queryset = queryset.active()
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, slug=None):
        shop = self.get_object()
        if shop.owner != request.user:
            return Response(
                {"detail": "You can only subscribe your own shop"},
                status=status.HTTP_403_FORBIDDEN
            )

        plan_id = request.data.get('plan_id')
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"detail": "Invalid subscription plan"},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = shop.add_subscription(duration_days=plan.duration_days, plan=plan)
        return Response(
            ShopSubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def services(self, request, slug=None):
        shop = self.get_object()
        services = shop.services.all()
        serializer = ShopServiceSerializer(services, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def promotions(self, request, slug=None):
        shop = self.get_object()
        promotions = shop.promotions.all()
        serializer = ShopPromotionSerializer(promotions, many=True)
        return Response(serializer.data)

class ShopMediaViewSet(viewsets.ModelViewSet):
    queryset = ShopMedia.objects.all()
    serializer_class = ShopMediaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return self.queryset.filter(shop__owner=self.request.user)

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.owner != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You don't own this shop")
        
        # Ensure only one primary media per type per shop
        media_type = serializer.validated_data['media_type']
        if serializer.validated_data.get('is_primary', False):
            ShopMedia.objects.filter(
                shop=shop,
                media_type=media_type
            ).update(is_primary=False)
        
        serializer.save()

class ShopServiceViewSet(viewsets.ModelViewSet):
    queryset = ShopService.objects.all()
    serializer_class = ShopServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return self.queryset.filter(shop__owner=self.request.user)

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.owner != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You don't own this shop")
        
        if not shop.active_subscription:
            raise serializers.ValidationError(
                "Shop must have an active subscription to add services"
            )
        
        serializer.save()

class ShopPromotionViewSet(viewsets.ModelViewSet):
    queryset = ShopPromotion.objects.all()
    serializer_class = ShopPromotionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['shop', 'is_active']

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            if self.request.user.is_authenticated:
                queryset = queryset.filter(shop__owner=self.request.user)
            else:
                queryset = queryset.filter(is_active=True)
        return queryset

    def perform_create(self, serializer):
        shop = serializer.validated_data['shop']
        if shop.owner != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You don't own this shop")
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def increment_views(self, request, pk=None):
        promotion = self.get_object()
        promotion.views += 1
        promotion.save()
        return Response({'views': promotion.views})