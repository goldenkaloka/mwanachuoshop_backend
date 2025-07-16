from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from django.core.files import File
import tempfile
from django.utils import timezone
from decimal import Decimal
import requests
from django.utils.text import slugify
from users.models import NewUser
from marketplace.models import Category, Brand, Attribute, AttributeValue, Product, ProductImage
import random
import uuid
from core.models import University, Campus
from django.contrib.gis.geos import Point

class Command(BaseCommand):
    help = 'Populate database with 20 sample eCommerce products and related data in specific order'

    def handle(self, *args, **kwargs):
        # Step 1: Authenticate or create user
        email = 'goldenkaloka@gmail.com'
        password = 'Gold@002'
        user = authenticate(email=email, password=password)
        if not user:
            self.stdout.write(self.style.WARNING(f'User {email} not found, creating new user...'))
            if NewUser.objects.filter(email=email).exists():
                self.stdout.write(self.style.ERROR(f'User with email {email} already exists but wrong password'))
                return
            user = NewUser.objects.create_user(
                email=email,
                username='goldenkaloka',
                phonenumber='+255616622485',
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Created user {user.email}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Authenticated user {user.email}'))

        # Step 2: Get University of Dar es Salaam and Mlimani Campus
        try:
            udsm = University.objects.get(name='University of Dar es Salaam')
            mlimani_campus = Campus.objects.get(name='Mlimani Campus', university=udsm)
            self.stdout.write(self.style.SUCCESS(f'Found University: {udsm.name} (ID: {udsm.id})'))
            self.stdout.write(self.style.SUCCESS(f'Found Campus: {mlimani_campus.name} (ID: {mlimani_campus.id})'))
        except (University.DoesNotExist, Campus.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(f'University or Campus not found: {str(e)}'))
            return

        # Step 3: Create Categories (Google eCommerce Taxonomy)
        categories_data = [
            {'name': 'Electronics', 'parent': None},
            {'name': 'Mobile Phones', 'parent': 'Electronics'},
            {'name': 'Laptops', 'parent': 'Electronics'},
            {'name': 'Cameras & Photography', 'parent': 'Electronics'},
            {'name': 'Apparel & Accessories', 'parent': None},
            {'name': 'Clothing', 'parent': 'Apparel & Accessories'},
            {'name': 'Shoes', 'parent': 'Apparel & Accessories'},
            {'name': 'Jewelry', 'parent': 'Apparel & Accessories'},
            {'name': 'Home & Garden', 'parent': None},
            {'name': 'Furniture', 'parent': 'Home & Garden'},
            {'name': 'Kitchen & Dining', 'parent': 'Home & Garden'},
            {'name': 'Sporting Goods', 'parent': None},
            {'name': 'Outdoor Gear', 'parent': 'Sporting Goods'},
        ]

        category_objects = {}
        self.stdout.write(self.style.NOTICE('Creating categories...'))
        for cat_data in categories_data:
            parent = category_objects.get(cat_data['parent']) if cat_data['parent'] else None
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                parent=parent,
                defaults={'is_active': True}
            )
            category_objects[cat_data['name']] = category
            self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} category: {category.name}'))

        # Step 4: Create Attributes
        attributes_data = [
            {'name': 'Color'},
            {'name': 'Size'},
            {'name': 'Storage'},
            {'name': 'Material'},
        ]

        attribute_objects = {}
        self.stdout.write(self.style.NOTICE('Creating attributes...'))
        for attr_data in attributes_data:
            attribute, created = Attribute.objects.get_or_create(name=attr_data['name'])
            attribute_objects[attr_data['name']] = attribute
            self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} attribute: {attribute.name}'))

        # Step 5: Create Attribute Values
        attribute_values_data = [
            {'attribute': 'Color', 'value': 'Black', 'category': 'Mobile Phones'},
            {'attribute': 'Color', 'value': 'Silver', 'category': 'Mobile Phones'},
            {'attribute': 'Color', 'value': 'Blue', 'category': 'Shoes'},
            {'attribute': 'Color', 'value': 'Red', 'category': 'Shoes'},
            {'attribute': 'Color', 'value': 'Blue', 'category': 'Clothing'},
            {'attribute': 'Color', 'value': 'Red', 'category': 'Clothing'},
            {'attribute': 'Color', 'value': 'Brown', 'category': 'Furniture'},
            {'attribute': 'Color', 'value': 'White', 'category': 'Kitchen & Dining'},
            {'attribute': 'Color', 'value': 'Gold', 'category': 'Jewelry'},
            {'attribute': 'Color', 'value': 'Black', 'category': 'Shoes'},
            {'attribute': 'Color', 'value': 'White', 'category': 'Electronics'},
            {'attribute': 'Color', 'value': 'Blue', 'category': 'Outdoor Gear'},
            {'attribute': 'Color', 'value': 'Silver', 'category': 'Jewelry'},
            {'attribute': 'Color', 'value': 'Black', 'category': 'Electronics'},
            {'attribute': 'Color', 'value': 'Black', 'category': 'Clothing'},
            {'attribute': 'Size', 'value': 'Small', 'category': 'Clothing'},
            {'attribute': 'Size', 'value': 'Medium', 'category': 'Clothing'},
            {'attribute': 'Size', 'value': 'Large', 'category': 'Clothing'},
            {'attribute': 'Size', 'value': 'US 8', 'category': 'Shoes'},
            {'attribute': 'Size', 'value': 'US 9', 'category': 'Shoes'},
            {'attribute': 'Storage', 'value': '64GB', 'category': 'Mobile Phones'},
            {'attribute': 'Storage', 'value': '256GB', 'category': 'Mobile Phones'},
            {'attribute': 'Storage', 'value': '512GB', 'category': 'Laptops'},
            {'attribute': 'Material', 'value': 'Wood', 'category': 'Furniture'},
            {'attribute': 'Material', 'value': 'Stainless Steel', 'category': 'Kitchen & Dining'},
            {'attribute': 'Material', 'value': 'Silver', 'category': 'Jewelry'},
        ]

        self.stdout.write(self.style.NOTICE('Creating attribute values...'))
        for value_data in attribute_values_data:
            category = category_objects[value_data['category']]
            attr_value, created = AttributeValue.objects.get_or_create(
                attribute=attribute_objects[value_data['attribute']],
                category=category,
                value=value_data['value']
            )
            self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} attribute value: {attr_value}'))

        # Step 6: Create Brands
        brands_data = [
            {'name': 'Samsung', 'categories': ['Mobile Phones', 'Laptops', 'Electronics'], 'is_active': True},
            {'name': 'Apple', 'categories': ['Mobile Phones', 'Laptops', 'Electronics'], 'is_active': True},
            {'name': 'Nike', 'categories': ['Clothing', 'Shoes'], 'is_active': True},
            {'name': 'Adidas', 'categories': ['Clothing', 'Shoes', 'Outdoor Gear'], 'is_active': True},
            {'name': 'IKEA', 'categories': ['Furniture', 'Kitchen & Dining'], 'is_active': True},
            {'name': 'Canon', 'categories': ['Cameras & Photography'], 'is_active': True},
            {'name': 'Pandora', 'categories': ['Jewelry'], 'is_active': True},
        ]

        brands = {}
        self.stdout.write(self.style.NOTICE('Creating brands...'))
        for brand_data in brands_data:
            brand, created = Brand.objects.get_or_create(
                name=brand_data['name'],
                created_by=user,
                defaults={'is_active': brand_data['is_active']}
            )
            brand.categories.set([category_objects[cat] for cat in brand_data['categories']])
            brands[brand_data['name']] = brand
            self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} brand: {brand.name}'))

        # Step 7: Create Products with updated images and UDSM location
        products_data = [
            {
                'name': 'Samsung Galaxy S22',
                'description': 'Advanced smartphone with 5G and triple camera system. Features a 6.1-inch Dynamic AMOLED display, 50MP main camera, and 25W fast charging.',
                'brand': 'Samsung',
                'category': 'Mobile Phones',
                'condition': Product.Condition.NEW,
                'price': Decimal('900000.00'),
                'attribute_values': [('Color', 'Black'), ('Storage', '256GB')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Apple iPhone 14',
                'description': 'Latest iPhone with A15 Bionic chip, 6.1-inch Super Retina XDR display, and advanced dual-camera system with 12MP main and ultra-wide cameras.',
                'brand': 'Apple',
                'category': 'Mobile Phones',
                'condition': Product.Condition.NEW,
                'price': Decimal('1200000.00'),
                'attribute_values': [('Color', 'Silver'), ('Storage', '256GB')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1592286927502-0e8a2c2c9b8c?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Nike Air Max 270',
                'description': 'Comfortable running shoes with Air Max 270 unit for maximum cushioning. Perfect for daily wear and athletic activities.',
                'brand': 'Nike',
                'category': 'Shoes',
                'condition': Product.Condition.NEW,
                'price': Decimal('150000.00'),
                'attribute_values': [('Color', 'Blue'), ('Size', 'US 9')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Adidas Ultraboost',
                'description': 'High-performance running shoes with responsive Boost midsole and Primeknit upper for ultimate comfort and energy return.',
                'brand': 'Adidas',
                'category': 'Shoes',
                'condition': Product.Condition.USED,
                'price': Decimal('100000.00'),
                'attribute_values': [('Color', 'Red'), ('Size', 'US 8')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'IKEA Poang Chair',
                'description': 'Ergonomic chair with curved birch veneer frame and comfortable cushion. Perfect for reading, relaxing, or as accent furniture.',
                'brand': 'IKEA',
                'category': 'Furniture',
                'condition': Product.Condition.USED,
                'price': Decimal('200000.00'),
                'attribute_values': [('Color', 'Brown'), ('Material', 'Wood')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Canon EOS R6',
                'description': 'Mirrorless camera with 20MP full-frame CMOS sensor, 4K video recording, and advanced autofocus system with 1053 AF points.',
                'brand': 'Canon',
                'category': 'Cameras & Photography',
                'condition': Product.Condition.NEW,
                'price': Decimal('2500000.00'),
                'attribute_values': [('Color', 'Black')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1510127034890-ba275aee7129?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Pandora Charm Bracelet',
                'description': 'Sterling silver charm bracelet with elegant design. Perfect gift for special occasions and personal expression.',
                'brand': 'Pandora',
                'category': 'Jewelry',
                'condition': Product.Condition.NEW,
                'price': Decimal('120000.00'),
                'attribute_values': [('Color', 'Gold'), ('Material', 'Silver')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1573408301185-9146fe634ad0?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Samsung Odyssey G7',
                'description': '27-inch curved gaming monitor with 240Hz refresh rate, 1ms response time, and QHD resolution for immersive gaming experience.',
                'brand': 'Samsung',
                'category': 'Electronics',
                'condition': Product.Condition.NEW,
                'price': Decimal('600000.00'),
                'attribute_values': [('Color', 'Black')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Apple MacBook Air M2',
                'description': 'Lightweight laptop with M2 chip, 13.6-inch Liquid Retina display, and up to 18 hours of battery life. Perfect for students and professionals.',
                'brand': 'Apple',
                'category': 'Laptops',
                'condition': Product.Condition.NEW,
                'price': Decimal('1500000.00'),
                'attribute_values': [('Color', 'Silver'), ('Storage', '512GB')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Nike Dri-FIT T-Shirt',
                'description': 'Breathable athletic t-shirt with moisture-wicking technology. Perfect for workouts, sports, and casual wear.',
                'brand': 'Nike',
                'category': 'Clothing',
                'condition': Product.Condition.NEW,
                'price': Decimal('50000.00'),
                'attribute_values': [('Color', 'Blue'), ('Size', 'Medium')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Adidas Track Jacket',
                'description': 'Comfortable track jacket with classic design and lightweight material. Ideal for sports activities and casual wear.',
                'brand': 'Adidas',
                'category': 'Clothing',
                'condition': Product.Condition.USED,
                'price': Decimal('80000.00'),
                'attribute_values': [('Color', 'Red'), ('Size', 'Large')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'IKEA Kallax Shelf',
                'description': 'Versatile storage shelf with 16 compartments. Perfect for organizing books, toys, or displaying decorative items.',
                'brand': 'IKEA',
                'category': 'Furniture',
                'condition': Product.Condition.NEW,
                'price': Decimal('250000.00'),
                'attribute_values': [('Color', 'White'), ('Material', 'Wood')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Canon PowerShot G7X',
                'description': 'Compact camera with 20.1MP CMOS sensor and 4.2x optical zoom. Perfect for vlogging, travel photography, and everyday use.',
                'brand': 'Canon',
                'category': 'Cameras & Photography',
                'condition': Product.Condition.USED,
                'price': Decimal('500000.00'),
                'attribute_values': [('Color', 'Black')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1510127034890-ba275aee7129?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Pandora Heart Necklace',
                'description': 'Elegant heart-shaped silver necklace with delicate design. Perfect gift for loved ones and special occasions.',
                'brand': 'Pandora',
                'category': 'Jewelry',
                'condition': Product.Condition.NEW,
                'price': Decimal('100000.00'),
                'attribute_values': [('Color', 'Silver'), ('Material', 'Silver')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1573408301185-9146fe634ad0?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Samsung Galaxy Watch 5',
                'description': 'Smartwatch with advanced health tracking, GPS, and long battery life. Compatible with Android and iOS devices.',
                'brand': 'Samsung',
                'category': 'Electronics',
                'condition': Product.Condition.NEW,
                'price': Decimal('350000.00'),
                'attribute_values': [('Color', 'Black')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1544117519-31a4b719223d?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Apple AirPods Pro',
                'description': 'Wireless earbuds with active noise cancellation, spatial audio, and sweat resistance. Perfect for music and calls.',
                'brand': 'Apple',
                'category': 'Electronics',
                'condition': Product.Condition.NEW,
                'price': Decimal('300000.00'),
                'attribute_values': [('Color', 'White')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1544117519-31a4b719223d?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Nike Running Shorts',
                'description': 'Lightweight running shorts with built-in liner and comfortable fit. Perfect for training and athletic activities.',
                'brand': 'Nike',
                'category': 'Clothing',
                'condition': Product.Condition.NEW,
                'price': Decimal('60000.00'),
                'attribute_values': [('Color', 'Black'), ('Size', 'Small')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Adidas Hiking Backpack',
                'description': 'Durable backpack with multiple compartments and comfortable shoulder straps. Ideal for outdoor adventures and travel.',
                'brand': 'Adidas',
                'category': 'Outdoor Gear',
                'condition': Product.Condition.NEW,
                'price': Decimal('120000.00'),
                'attribute_values': [('Color', 'Blue')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1622560480654-d96214fdc887?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'IKEA Dining Table',
                'description': 'Modern dining table with extendable design. Seats 4-6 people comfortably. Perfect for family meals and entertaining.',
                'brand': 'IKEA',
                'category': 'Kitchen & Dining',
                'condition': Product.Condition.NEW,
                'price': Decimal('400000.00'),
                'attribute_values': [('Color', 'White'), ('Material', 'Stainless Steel')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&h=600&fit=crop'
                ]
            },
            {
                'name': 'Pandora Earrings',
                'description': 'Sparkling silver stud earrings with elegant design. Perfect for everyday wear and special occasions.',
                'brand': 'Pandora',
                'category': 'Jewelry',
                'condition': Product.Condition.NEW,
                'price': Decimal('80000.00'),
                'attribute_values': [('Color', 'Silver'), ('Material', 'Silver')],
                'image_urls': [
                    'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=800&h=600&fit=crop',
                    'https://images.unsplash.com/photo-1573408301185-9146fe634ad0?w=800&h=600&fit=crop'
                ]
            },
        ]

        # UDSM Mlimani Campus coordinates (approximate)
        udsm_lat = -6.7783
        udsm_lng = 39.2014

        products = {}
        self.stdout.write(self.style.NOTICE('Creating products...'))
        for product_data in products_data:
            try:
                product, created = Product.objects.get_or_create(
                    name=product_data['name'],
                    owner=user,
                    defaults={
                        'description': product_data['description'],
                        'brand': brands[product_data['brand']],
                        'category': category_objects[product_data['category']],
                        'condition': product_data['condition'],
                        'price': product_data['price'],
                        'is_active': False,
                        'shop': None
                    }
                )
                
                # Assign location near UDSM Mlimani Campus with small random offset
                lat_offset = random.uniform(-0.005, 0.005)  # ~500m radius
                lng_offset = random.uniform(-0.005, 0.005)
                product.location = Point(
                    udsm_lng + lng_offset, 
                    udsm_lat + lat_offset
                )
                
                            self.stdout.write(self.style.SUCCESS(
                    f'Assigned location for {product.name}: UDSM Mlimani Campus ({product.location.x:.4f}, {product.location.y:.4f})'
                ))
                    
                product.save()
                products[product_data['name']] = product
                self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} product: {product.name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to create product {product_data["name"]}: {str(e)}'))
                continue

        # Step 8: Assign Attribute Values to Products
        self.stdout.write(self.style.NOTICE('Assigning attribute values to products...'))
        for product_data in products_data:
            product = products.get(product_data['name'])
            if not product:
                continue
            for attr_name, value in product_data['attribute_values']:
                try:
                    attr_value = AttributeValue.objects.get(
                        attribute=attribute_objects[attr_name],
                        value=value,
                        category=category_objects[product_data['category']]
                    )
                    product.attribute_values.add(attr_value)
                    self.stdout.write(self.style.SUCCESS(f'Assigned {attr_name}: {value} to {product.name}'))
                except AttributeValue.DoesNotExist:
                    self.stdout.write(self.style.ERROR(
                        f'AttributeValue {attr_name}: {value} for category {product_data["category"]} does not exist'
                    ))
                    continue

        # Step 9: Create Product Images
        self.stdout.write(self.style.NOTICE('Creating product images...'))
        for product_data in products_data:
            product = products.get(product_data['name'])
            if not product:
                continue
            for i, url in enumerate(product_data['image_urls']):
                try:
                    response = requests.get(url, stream=True, timeout=10)
                    if response.status_code == 200:
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as img_temp:
                            img_temp.write(response.content)
                            img_temp.flush()
                            product_image = ProductImage(
                                product=product, 
                                is_primary=(i == 0)  # First image is primary
                            )
                            product_image.image.save(
                                f'{slugify(product.name)}_{uuid.uuid4().hex[:8]}.jpg',
                                File(img_temp),
                                save=True
                            )
                            self.stdout.write(self.style.SUCCESS(f'Added image {i+1} for product: {product.name}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to download image {url}: {str(e)}'))

        # Step 10: Activate Products
        self.stdout.write(self.style.NOTICE('Activating products...'))
        for product_data in products_data:
            product = products.get(product_data['name'])
            if not product:
                continue
            try:
                product.is_active = True
                product.save()
                self.stdout.write(self.style.SUCCESS(f'Activated product: {product.name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to activate product {product.name}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Successfully populated eCommerce data with 20 products at UDSM Mlimani Campus'))