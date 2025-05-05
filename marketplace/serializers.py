from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage
from payments.models import Payment, PaymentService
from shops.models import Shop, UserOffer

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'is_active']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'logo']

class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ['id', 'name']

class AttributeValueSerializer(serializers.ModelSerializer):
    attribute = AttributeSerializer(read_only=True)
    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute','category_id', 'value']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'is_primary']
        extra_kwargs = {
            'product': {'read_only': True}
        }


class ProductSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    attribute_value_ids = serializers.PrimaryKeyRelatedField(
        queryset=AttributeValue.objects.all(), many=True, required=True, write_only=True
    )
    attribute_values = AttributeValueSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    brand = BrandSerializer(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(), source='brand', write_only=True
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    shop = serializers.PrimaryKeyRelatedField(
        queryset=Shop.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 'brand_id', 'category', 'category_id',
            'owner', 'shop', 'price', 'attribute_values', 'attribute_value_ids', 'images',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        print(f"Serializer to_internal_value input: {data}")
        if 'price' in data and isinstance(data['price'], str):
            try:
                data['price'] = Decimal(data['price'])
            except (ValueError, TypeError):
                raise serializers.ValidationError({"price": "Invalid price format."})
        return super().to_internal_value(data)

    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Category is not active.")
        return value

    def validate_price(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Price must be a positive number.")
        return value

    def validate_attribute_value_ids(self, value):
        category = self.initial_data.get('category_id')
        if not value:
            raise serializers.ValidationError("At least one attribute value is required.")
        for attr_value in value:
            if not AttributeValue.objects.filter(id=attr_value.id, category_id=category).exists():
                raise serializers.ValidationError(f"Attribute value {attr_value.id} is invalid or not in category {category}.")
        return value

    def validate(self, data):
        print(f"Serializer validate input: {data}")
        errors = {}
        if not data.get('name'):
            errors['name'] = "This field is required."
        if not data.get('description'):
            errors['description'] = "This field is required."
        if not data.get('brand'):
            errors['brand_id'] = "This field is required."
        if not data.get('category'):
            errors['category_id'] = "This field is required."
        if 'price' not in data:
            errors['price'] = "This field is required."
        if 'attribute_value_ids' not in data:
            errors['attribute_value_ids'] = "This field is required."

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            errors['authentication'] = "Authentication required."

        if errors:
            print(f"Validation errors: {errors}")
            raise serializers.ValidationError(errors)

        user = request.user
        shop = Shop.objects.filter(user=user).first()

        # Check if user can create products for free
        offer = UserOffer.objects.filter(user=user).first()
        if offer and offer.free_products_remaining > 0:
            print(f"User {user.email} has {offer.free_products_remaining} free products remaining.")
            return data

        if shop and shop.is_subscription_active():
            print(f"User {user.email} has active shop subscription.")
            return data

        # Check if user has a completed payment for product creation
        try:
            payment_service = PaymentService.objects.get(name=PaymentService.ServiceName.PRODUCT_CREATION)
            has_paid = Payment.objects.filter(
                user=user,
                service=payment_service,
                status=Payment.PaymentStatus.COMPLETED
            ).exists()
        except PaymentService.DoesNotExist:
            raise serializers.ValidationError({
                "non_field_errors": ["Product creation service is not configured."],
                "payment_required": True
            })

        if not has_paid:
            raise serializers.ValidationError({
                "non_field_errors": [
                    "You must purchase a product creation service to post more products. "
                    "Please initiate payment to continue."
                ],
                "payment_required": True,
                "payment_service_id": payment_service.id,
                "payment_service_price": str(payment_service.price),
                "payment_endpoint": "/api/create-product-payment/"
            })

        return data

    def create(self, validated_data):
        print(f"Creating product with validated_data: {validated_data}")
        attribute_value_ids = validated_data.pop('attribute_value_ids', [])
        product = Product.objects.create(**validated_data)
        if attribute_value_ids:
            product.attribute_values.set(attribute_value_ids)
        print(f"Created product {product.id} with attribute_values: {attribute_value_ids}")
        return product
    
class ProductImageUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'is_primary']
    
    def to_representation(self, instance):
        """Return a dictionary with full image URL and is_primary"""
        request = self.context.get('request')
        image_url = instance.image.url
        if request:
            image_url = request.build_absolute_uri(image_url)
        
        return {
            'image': image_url,
            'is_primary': instance.is_primary
        }

class ProductListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 
            'name', 
            'price', 
            'image_url',
            'brand',
            'category',
            'created_at'
        ]
    
    def get_image_url(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ProductImageUrlSerializer(primary_image, context=self.context).data
        
        first_image = obj.images.first()
        if first_image:
            return ProductImageUrlSerializer(first_image, context=self.context).data
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageUrlSerializer(many=True, read_only=True)
    attribute_values = AttributeValueSerializer(many=True, read_only=True)
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    owner = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'price',
            'images',
            'brand',
            'category',
            'attribute_values',
            'owner',
            'created_at',
            'updated_at'
        ]
    
    def get_owner(self, obj):
        owner = obj.owner
        profile = owner.profile
        return {
            'username': owner.username,
            'phone': str(owner.phonenumber),
            'whatsapp': str(profile.whatsapp) if profile and profile.whatsapp else None,
            'instagram': profile.instagram if profile else None,
            'tiktok': profile.tiktok if profile else None
        }