from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Brand, Attribute, AttributeValue, Product, ProductImage, WhatsAppClick
from shops.models import Shop, UserOffer
from users.serializers import CustomUserDetailsSerializer  # Import for owner field

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        allow_null=True,
        required=False,
        write_only=True
    )
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'parent_name', 'is_active']
        read_only_fields = ['is_active']

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
            'created_at', 'updated_at', 'is_active', 'payment_amount', 'condition'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at', 'is_active']

    def get_payment_amount(self, obj):
        """Calculate payment amount as 0.1% of price, with a minimum of 1.00."""
        try:
            return str(max(
                Decimal('1.00'),
                (obj.price * Decimal('0.001')).quantize(Decimal('0.01'))
            ))
        except (TypeError, Decimal.InvalidOperation):
            return str(Decimal('1.00'))

    def to_internal_value(self, data):
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'price' in mutable_data:
            price_value = mutable_data['price']
            try:
                if isinstance(price_value, (str, float, int)):
                    mutable_data['price'] = Decimal(str(price_value))
                else:
                    raise serializers.ValidationError({"price": "Invalid price format."})
            except (ValueError, TypeError, Decimal.InvalidOperation):
                raise serializers.ValidationError({"price": "Invalid price format."})
        return super().to_internal_value(mutable_data)

    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Category is not active.")
        return value

    def validate_price(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Price must be a positive number.")
        return value

    def validate_attribute_value_ids(self, value):
        category_id = self.initial_data.get('category_id')
        if not category_id:
            raise serializers.ValidationError("Category is required to validate attribute values.")
        if not value:
            raise serializers.ValidationError("At least one attribute value is required.")
        for attr_value in value:
            if not AttributeValue.objects.filter(id=attr_value.id, category_id=category_id).exists():
                raise serializers.ValidationError(
                    f"Attribute value {attr_value.id} is invalid for this category."
                )
        return value

    def validate(self, data):
        errors = {}
        required_fields = {
            'name': "Product name is required.",
            'description': "Description is required.",
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
    category = serializers.CharField(source='category.name')
    brand = serializers.CharField(source='brand.name')
    price = serializers.FloatField()
    image_url = serializers.SerializerMethodField()
    condition = serializers.CharField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'brand', 'price', 'image_url',
            'created_at', 'condition'
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and request:
            return {
                'image': request.build_absolute_uri(primary_image.image.url),
                'is_primary': True
            }
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name')
    brand = serializers.CharField(source='brand.name')
    price = serializers.FloatField()
    images = ProductImageUrlSerializer(many=True, read_only=True)
    attribute_values = AttributeValueSerializer(many=True, read_only=True)
    owner = CustomUserDetailsSerializer(read_only=True)
    condition = serializers.CharField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'brand', 'price',
            'images', 'attribute_values', 'owner', 'created_at',
            'updated_at', 'is_active', 'condition'
        ]

class WhatsAppClickSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product'
    )

    class Meta:
        model = WhatsAppClick
        fields = ['product_id', 'clicked_at']
        read_only_fields = ['clicked_at']

    def validate_product_id(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot record click for an inactive product.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user if request.user.is_authenticated else None
        validated_data['ip_address'] = request.META.get('REMOTE_ADDR')
        return super().create(validated_data)
