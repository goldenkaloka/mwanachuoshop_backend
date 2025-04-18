from rest_framework import serializers
from .models import (
    Product, ProductLine, ProductImage, 
    AttributeValue, Attribute, Category, Brand
)
from users.serializers import ProfileSerializer
from shops.serializers import ShopSerializer
from django.utils.text import slugify

class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ['id', 'name', 'slug', 'description']

class AttributeValueSerializer(serializers.ModelSerializer):
    attribute = AttributeSerializer()
    
    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute', 'value', 'slug']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']
        read_only_fields = ['id']

class ProductLineSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False)
    attribute_values = AttributeValueSerializer(many=True)
    current_price = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductLine
        fields = [
            'id', 'sku', 'price', 'sale_price', 'current_price',
            'cost_price', 'stock_qty', 'is_active', 'images',
            'attribute_values'
        ]
    
    def get_current_price(self, obj):
        return obj.current_price

class ProductListSerializer(serializers.ModelSerializer):
    brand = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    primary_image = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()
    shop = ShopSerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'brand', 'category',
            'primary_image', 'price_range', 'shop', 'is_featured'
        ]
    
    def get_primary_image(self, obj):
        first_line = obj.product_lines.filter(is_active=True).first()
        if first_line and first_line.images.exists():
            image = first_line.images.filter(is_primary=True).first() or first_line.images.first()
            return ProductImageSerializer(image).data
        return None
    
    def get_price_range(self, obj):
        active_lines = obj.product_lines.filter(is_active=True)
        if active_lines.exists():
            prices = [line.current_price for line in active_lines]
            return {
                'min': min(prices),
                'max': max(prices)
            }
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    owner = ProfileSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    brand = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    product_lines = ProductLineSerializer(many=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'type',
            'brand', 'category', 'owner', 'shop', 'is_active',
            'is_featured', 'created_at', 'updated_at', 'product_lines'
        ]
        read_only_fields = [
            'id', 'slug', 'owner', 'shop', 'created_at',
            'updated_at', 'is_active'
        ]

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    product_lines = ProductLineSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'type', 'brand',
            'category', 'is_featured', 'product_lines'
        ]
    
    def validate(self, data):
        # Add comprehensive validation
        errors = {}
        
        # Check required fields
        required_fields = ['name', 'description', 'type', 'brand', 'category']
        for field in required_fields:
            if field not in data:
                errors[field] = "This field is required."
        
        # Validate product lines if provided
        if 'product_lines' in data:
            for idx, line in enumerate(data['product_lines']):
                line_errors = {}
                
                if 'price' not in line:
                    line_errors['price'] = "Price is required for each product line."
                elif not isinstance(line['price'], (int, float)) or line['price'] <= 0:
                    line_errors['price'] = "Price must be a positive number."
                
                if 'sku' not in line or not line['sku']:
                    line_errors['sku'] = "SKU is required for each product line."
                
                if line_errors:
                    errors[f'product_lines.{idx}'] = line_errors
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data
    
    def create(self, validated_data):
        try:
            request = self.context.get('request')
            if not request or not request.user:
                raise serializers.ValidationError("Authentication required")
            
            product_lines_data = validated_data.pop('product_lines', [])
            
            # Create the product
            product = Product.objects.create(
                owner=request.user,
                **validated_data
            )
            
            # Create product lines
            for line_data in product_lines_data:
                self._create_product_line(product, line_data)
            
            return product
            
        except Exception as e:
            print(f"Error in product creation: {str(e)}")
            raise
    
    def _create_product_line(self, product, line_data):
        try:
            images_data = line_data.pop('images', [])
            attribute_values_data = line_data.pop('attribute_values', [])
            
            product_line = ProductLine.objects.create(
                product=product,
                **line_data
            )
            
            # Create images
            for image_data in images_data:
                ProductImage.objects.create(
                    product_line=product_line,
                    **image_data
                )
            
            # Add attribute values
            for attr_value in attribute_values_data:
                if isinstance(attr_value, dict):
                    product_line.attribute_values.add(attr_value['id'])
                else:
                    product_line.attribute_values.add(attr_value)
            
            return product_line
            
        except Exception as e:
            print(f"Error creating product line: {str(e)}")
            raise    



class CategoryFilterSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

class BrandFilterSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()




class PriceRangeSerializer(serializers.Serializer):
    min = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)