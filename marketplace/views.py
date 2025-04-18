# views.py

from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db import models
from django.db.models import Prefetch, Count, Q, Min, Max
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from .models import Brand, Category, Product, ProductLine, ProductImage, AttributeValue
from .serializers import (
    BrandFilterSerializer, CategoryFilterSerializer, PriceRangeSerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer
)
from shops.models import SubscriptionPlan
from users.models import ProductPayment, SubscriptionPayment
from marketplace.utils.payment import PaymentProcessor
from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import Prefetch
import logging
import traceback

logger = logging.getLogger(__name__)

class ProductListCreateView(generics.ListCreateAPIView):
    """
    Enhanced Product List/Create View with:
    - Comprehensive error handling
    - Detailed request logging
    - Robust validation
    - Clear error responses
    """
    serializer_class = ProductListSerializer
    
    def get_queryset(self):
        """
        Get filtered and optimized queryset for product listing
        """
        queryset = Product.objects.filter(is_active=True).select_related(
            'brand', 'category', 'shop'
        ).prefetch_related(
            Prefetch(
                'product_lines',
                queryset=ProductLine.objects.filter(is_active=True).prefetch_related(
                    Prefetch(
                        'images',
                        queryset=ProductImage.objects.all().order_by('order')
                    ),
                    Prefetch(
                        'attribute_values',
                        queryset=AttributeValue.objects.select_related('attribute')
                    )
                )
            )
        ).order_by('-created_at')
        
        # Apply filters from query parameters
        search_query = self.request.query_params.get('search')
        category_ids = self.request.query_params.getlist('category')
        brand_ids = self.request.query_params.getlist('brand')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        queryset = Product.objects.search_and_filter(
            search_query=search_query,
            category_ids=category_ids,
            brand_ids=brand_ids,
            min_price=min_price,
            max_price=max_price
        )
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Enhanced create method with:
        - Detailed request logging
        - Comprehensive error handling
        - Clear error responses
        """
        try:
            logger.info(
                "Product creation request received",
                extra={
                    'user': request.user.username if request.user else 'anonymous',
                    'data': request.data
                }
            )
            
            # Ensure we have the request in context for the serializer
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            logger.debug(
                "Product data validated successfully",
                extra={'validated_data': serializer.validated_data}
            )
            
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            
            logger.info(
                "Product created successfully",
                extra={
                    'product_id': serializer.data.get('id'),
                    'user': request.user.username
                }
            )
            
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
            
        except serializers.ValidationError as ve:
            logger.warning(
                "Product creation validation failed",
                extra={
                    'errors': ve.detail,
                    'user': request.user.username if request.user else 'anonymous'
                }
            )
            return Response(
                {
                    'status': 'validation_error',
                    'errors': ve.detail,
                    'message': 'Please check the provided data'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(
                "Product creation failed",
                extra={
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'user': request.user.username if request.user else 'anonymous',
                    'traceback': traceback.format_exc()
                }
            )
            return Response(
                {
                    'status': 'error',
                    'message': 'An unexpected error occurred',
                    'error': str(e),
                    'error_type': type(e).__name__
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        """
        Custom perform_create to ensure owner is set
        """
        if self.request and self.request.user:
            serializer.save(owner=self.request.user)
        else:
            raise serializers.ValidationError("Authentication required")

class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return []
        return [IsAuthenticated()]
    
    def get_queryset(self):
        return Product.objects.select_related(
            'owner__profile', 'brand', 'category', 'shop'
        ).prefetch_related(
            Prefetch(
                'product_lines',
                queryset=ProductLine.objects.prefetch_related(
                    'images',
                    Prefetch(
                        'attribute_values',
                        queryset=AttributeValue.objects.select_related('attribute')
                    )
                )
            )
        )
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class UserProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(
            owner=self.request.user
        ).select_related(
            'brand', 'category', 'shop'
        ).prefetch_related(
            Prefetch(
                'product_lines',
                queryset=ProductLine.objects.prefetch_related(
                    'images'
                )
            )
        ).order_by('-created_at')

@csrf_exempt
def azam_payment_callback(request):
    """Handle AzamPay payment callback for subscriptions"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reference_id = data.get('referenceId')
            status = data.get('status')
            
            payment = SubscriptionPayment.objects.get(transaction_id=reference_id)
            
            if status == 'SUCCESS':
                payment.mark_as_completed()
                if payment.subscription:
                    payment.subscription.is_active = True
                    payment.subscription.save()
                    if not payment.shop.is_active:
                        payment.shop.is_active = True
                        payment.shop.save()
            else:
                payment.status = 'failed'
                payment.save()
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def azam_product_payment_callback(request):
    """Handle AzamPay payment callback for product payments"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reference_id = data.get('referenceId')
            status = data.get('status')
            
            payment = ProductPayment.objects.get(transaction_id=reference_id)
            
            if status == 'SUCCESS':
                payment.mark_as_completed()
                if payment.product:
                    payment.product.is_active = True
                    payment.product.save()
            else:
                payment.status = 'failed'
                payment.save()
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

class InitiateSubscriptionPaymentAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        shop = request.user.shops.first()
        plan_slug = request.data.get('plan')
        payment_method = request.data.get('payment_method', 'azampay')
        
        if not shop:
            return Response(
                {"error": "You don't have a shop"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            plan = SubscriptionPlan.objects.get(slug=plan_slug, active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"error": "Invalid subscription plan"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment, response = PaymentProcessor.process_subscription_payment(
            shop=shop,
            plan=plan,
            payment_method=payment_method
        )
        
        if not response:
            return Response(
                {"error": "Payment initiation failed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            "payment_id": payment.id,
            "status": payment.status,
            "azampay_response": response
        })

class InitiateProductPaymentAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        payment_method = request.data.get('payment_method', 'azampay')
        
        try:
            product = Product.objects.get(id=product_id, owner=request.user)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        payment, response = PaymentProcessor.process_product_payment(
            user=request.user,
            product=product,
            payment_method=payment_method
        )
        
        if not response:
            return Response(
                {"error": "Payment initiation failed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            "payment_id": payment.id,
            "status": payment.status,
            "azampay_response": response
        })
    

# views.py

# views.py
class FilterOptionsView(APIView):
    def get(self, request):
        categories = Category.objects.annotate(
            product_count=models.Count(
                'products',
                filter=models.Q(products__is_active=True)
            )
        ).filter(product_count__gt=0)
        
        brands = Brand.objects.annotate(
            product_count=models.Count(
                'products',
                filter=models.Q(products__is_active=True)
            )
        ).filter(product_count__gt=0)
        
        # Get price range from active product lines
        price_aggregation = ProductLine.objects.filter(
            product__is_active=True,
            is_active=True
        ).aggregate(
            min_price=models.Min('price'),
            max_price=models.Max('price')
        )
        
        # Handle case where there are no products
        price_range = {
            'min': price_aggregation['min_price'] or 0,
            'max': price_aggregation['max_price'] or 1000
        }
        
        return Response({
            'categories': CategoryFilterSerializer(categories, many=True).data,
            'brands': BrandFilterSerializer(brands, many=True).data,
            'price_range': price_range  # Directly return the dict, not serialized
        })
    

class CategoryListView(generics.ListAPIView):
    serializer_class = CategoryFilterSerializer
    
    def get_queryset(self):
        return Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count(
                'products',
                filter=Q(products__is_active=True)
            )
        ).filter(
            product_count__gt=0
        ).order_by('name')

class BrandListView(generics.ListAPIView):
    serializer_class = BrandFilterSerializer
    
    def get_queryset(self):
        return Brand.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count(
                'products',
                filter=Q(products__is_active=True)
            )
        ).filter(
            product_count__gt=0
        ).order_by('name')