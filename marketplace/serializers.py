from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage, WhatsAppClick
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
        fields = ['id', 'attribute', 'category_id', 'value']

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
        queryset=AttributeValue.objects.all(), 
        many=True, 
        required=True, 
        write_only=True
    )
    attribute_values = AttributeValueSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    brand = BrandSerializer(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(), 
        source='brand', 
        write_only=True
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        source='category', 
        write_only=True
    )
    shop = serializers.PrimaryKeyRelatedField(
        queryset=Shop.objects.all(), 
        required=False, 
        allow_null=True
    )
    payment_amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 'brand_id', 'category', 'category_id',
            'owner', 'shop', 'price', 'attribute_values', 'attribute_value_ids', 'images',
            'created_at', 'updated_at', 'is_active', 'payment_amount'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at', 'is_active']

    def get_payment_amount(self, obj):
        return str(max(
            Decimal('1.00'),
            (obj.price * Decimal('0.001')).quantize(Decimal('0.01'))
        ))

    def to_internal_value(self, data):
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
                raise serializers.ValidationError(
                    f"Attribute value {attr_value.id} is invalid for this category."
                )
        return value

    def validate(self, data):
        errors = {}
        required_fields = {
            'name': "Product name is required.",
            'description': "Description is required.",
            'brand': "Brand is required.",
            'category': "Category is required.",
            'price': "Price is required.",
            'attribute_value_ids': "At least one attribute is required."
        }
        
        for field, message in required_fields.items():
            if field not in data or not data[field]:
                errors[field] = message
                
        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        attribute_value_ids = validated_data.pop('attribute_value_ids', [])
        product = Product.objects.create(**validated_data)
        if attribute_value_ids:
            product.attribute_values.set(attribute_value_ids)
        return product

class ProductImageUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'is_primary']
    
    def to_representation(self, instance):
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
            'updated_at',
            'is_active'
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
    

class WhatsAppClickSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product'
    )

    class Meta:
        model = WhatsAppClick
        fields = ['product_id', 'clicked_at']
        read_only_fields = ['clicked_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user if request.user.is_authenticated else None
        validated_data['ip_address'] = request.META.get('REMOTE_ADDR')
        return super().create(validated_data)