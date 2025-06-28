
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

        # Step 2: Create Categories (Google eCommerce Taxonomy)
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

        # Step 3: Create Attributes
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

        # Step 4: Create Attribute Values
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

        # Step 5: Create Brands
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

        # Step 6: Create Products
        products_data = [
            {
                'name': 'Samsung Galaxy S22',
                'description': 'Advanced smartphone with 5G and triple camera.',
                'brand': 'Samsung',
                'category': 'Mobile Phones',
                'condition': Product.Condition.NEW,
                'price': Decimal('900000.00'),
                'attribute_values': [('Color', 'Black'), ('Storage', '256GB')],
                'image_urls': ['https://images.samsung.com/is/image/samsung/p6pim/za/sm-s901bzkdafu/gallery/za-galaxy-s22-5g-s901-406769-sm-s901bzkdafu-530465289?$650_519_PNG$']
            },
            {
                'name': 'Apple iPhone 14',
                'description': 'Latest iPhone with A15 Bionic chip.',
                'brand': 'Apple',
                'category': 'Mobile Phones',
                'condition': Product.Condition.NEW,
                'price': Decimal('1200000.00'),
                'attribute_values': [('Color', 'Silver'), ('Storage', '256GB')],
                'image_urls': ['https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-14-finish-select-202209-6-1inch-midnight?wid=5120&hei=2880&fmt=p-jpg&qlt=80&.v=1663707507562']
            },
            {
                'name': 'Nike Air Max 270',
                'description': 'Comfortable running shoes for daily wear.',
                'brand': 'Nike',
                'category': 'Shoes',
                'condition': Product.Condition.NEW,
                'price': Decimal('150000.00'),
                'attribute_values': [('Color', 'Blue'), ('Size', 'US 9')],
                'image_urls': ['https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/1e3f907f-127a-4f7e-b9f7-459dc3f7a3d9/air-max-270-mens-shoes-KkLcGR.png']
            },
            {
                'name': 'Adidas Ultraboost',
                'description': 'High-performance running shoes.',
                'brand': 'Adidas',
                'category': 'Shoes',
                'condition': Product.Condition.USED,
                'price': Decimal('100000.00'),
                'attribute_values': [('Color', 'Red'), ('Size', 'US 8')],
                'image_urls': ['https://assets.adidas.com/images/h_840,f_auto,q_auto:sensitive,fl_lossy,c_fill,g_auto/6f6f6f6f6f6f6f6f/ultraboost-22-shoes-GX5456_01_standard.jpg']
            },
            {
                'name': 'IKEA Poang Chair',
                'description': 'Ergonomic chair for home comfort.',
                'brand': 'IKEA',
                'category': 'Furniture',
                'condition': Product.Condition.USED,
                'price': Decimal('200000.00'),
                'attribute_values': [('Color', 'Brown'), ('Material', 'Wood')],
                'image_urls': ['https://www.ikea.com/us/en/images/products/poang-armchair-brown__0577238_PE668768_S5.JPG']
            },
            {
                'name': 'Canon EOS R6',
                'description': 'Mirrorless camera with 20MP sensor.',
                'brand': 'Canon',
                'category': 'Cameras & Photography',
                'condition': Product.Condition.NEW,
                'price': Decimal('2500000.00'),
                'attribute_values': [('Color', 'Black')],
                'image_urls': ['https://i1.adis.ws/i/canon/eos-r6-front-45-degree?$prod-hero--sm$']
            },
            {
                'name': 'Pandora Charm Bracelet',
                'description': 'Sterling silver charm bracelet.',
                'brand': 'Pandora',
                'category': 'Jewelry',
                'condition': Product.Condition.NEW,
                'price': Decimal('120000.00'),
                'attribute_values': [('Color', 'Gold'), ('Material', 'Silver')],
                'image_urls': ['https://us.pandora.net/dw/image/v2/AAVX_PRD/on/demandware.static/-/Sites-pandora-master-catalog/default/dw1a5b6b8d/images/productimages/590702HV.jpg']
            },
            {
                'name': 'Samsung Odyssey G7',
                'description': '27-inch curved gaming monitor.',
                'brand': 'Samsung',
                'category': 'Electronics',
                'condition': Product.Condition.NEW,
                'price': Decimal('600000.00'),
                'attribute_values': [('Color', 'Black')],
                'image_urls': ['https://images.samsung.com/is/image/samsung/p6pim/za/ls32ag700nuxxu/gallery/za-odyssey-g7-g70a-ls32ag700nuxxu-531123456?$650_519_PNG$']
            },
            {
                'name': 'Apple MacBook Air M2',
                'description': 'Lightweight laptop with M2 chip.',
                'brand': 'Apple',
                'category': 'Laptops',
                'condition': Product.Condition.NEW,
                'price': Decimal('1500000.00'),
                'attribute_values': [('Color', 'Silver'), ('Storage', '512GB')],
                'image_urls': ['https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/macbook-air-m2-midnight-gallery1-20220606?wid=2000&hei=1536&fmt=jpeg&qlt=95']
            },
            {
                'name': 'Nike Dri-FIT T-Shirt',
                'description': 'Breathable athletic t-shirt.',
                'brand': 'Nike',
                'category': 'Clothing',
                'condition': Product.Condition.NEW,
                'price': Decimal('50000.00'),
                'attribute_values': [('Color', 'Blue'), ('Size', 'Medium')],
                'image_urls': ['https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/1e3f907f-127a-4f7e-b9f7-459dc3f7a3d9/dri-fit-t-shirt-Cz3X9k.png']
            },
            {
                'name': 'Adidas Track Jacket',
                'description': 'Comfortable track jacket for sports.',
                'brand': 'Adidas',
                'category': 'Clothing',
                'condition': Product.Condition.USED,
                'price': Decimal('80000.00'),
                'attribute_values': [('Color', 'Red'), ('Size', 'Large')],
                'image_urls': ['https://assets.adidas.com/images/h_840,f_auto,q_auto:sensitive,fl_lossy,c_fill,g_auto/6f6f6f6f6f6f6f6f/track-jacket-HR7923_01_standard.jpg']
            },
            {
                'name': 'IKEA Kallax Shelf',
                'description': 'Versatile storage shelf for home.',
                'brand': 'IKEA',
                'category': 'Furniture',
                'condition': Product.Condition.NEW,
                'price': Decimal('250000.00'),
                'attribute_values': [('Color', 'White'), ('Material', 'Wood')],
                'image_urls': ['https://www.ikea.com/us/en/images/products/kallax-shelving-unit-white__0644757_PE702938_S5.JPG']
            },
            {
                'name': 'Canon PowerShot G7X',
                'description': 'Compact camera for vlogging.',
                'brand': 'Canon',
                'category': 'Cameras & Photography',
                'condition': Product.Condition.USED,
                'price': Decimal('500000.00'),
                'attribute_values': [('Color', 'Black')],
                'image_urls': ['https://i1.adis.ws/i/canon/powershot-g7x-mark-ii-front?$prod-hero--sm$']
            },
            {
                'name': 'Pandora Heart Necklace',
                'description': 'Elegant heart-shaped silver necklace.',
                'brand': 'Pandora',
                'category': 'Jewelry',
                'condition': Product.Condition.NEW,
                'price': Decimal('100000.00'),
                'attribute_values': [('Color', 'Silver'), ('Material', 'Silver')],
                'image_urls': ['https://us.pandora.net/dw/image/v2/AAVX_PRD/on/demandware.static/-/Sites-pandora-master-catalog/default/dw1a5b6b8d/images/productimages/398425C01.jpg']
            },
            {
                'name': 'Samsung Galaxy Watch 5',
                'description': 'Smartwatch with fitness tracking.',
                'brand': 'Samsung',
                'category': 'Electronics',
                'condition': Product.Condition.NEW,
                'price': Decimal('350000.00'),
                'attribute_values': [('Color', 'Black')],
                'image_urls': ['https://images.samsung.com/is/image/samsung/p6pim/za/sm-r900nzkaxfa/gallery/za-galaxy-watch5-40mm-r900-455123789?$650_519_PNG$']
            },
            {
                'name': 'Apple AirPods Pro',
                'description': 'Wireless earbuds with noise cancellation.',
                'brand': 'Apple',
                'category': 'Electronics',
                'condition': Product.Condition.NEW,
                'price': Decimal('300000.00'),
                'attribute_values': [('Color', 'White')],
                'image_urls': ['https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-pro-2nd-gen?wid=572&hei=572&fmt=jpeg&qlt=95']
            },
            {
                'name': 'Nike Running Shorts',
                'description': 'Lightweight shorts for running.',
                'brand': 'Nike',
                'category': 'Clothing',
                'condition': Product.Condition.NEW,
                'price': Decimal('60000.00'),
                'attribute_values': [('Color', 'Black'), ('Size', 'Small')],
                'image_urls': ['https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/1e3f907f-127a-4f7e-b9f7-459dc3f7a3d9/running-shorts-Fn3X9k.png']
            },
            {
                'name': 'Adidas Hiking Backpack',
                'description': 'Durable backpack for outdoor adventures.',
                'brand': 'Adidas',
                'category': 'Outdoor Gear',
                'condition': Product.Condition.NEW,
                'price': Decimal('120000.00'),
                'attribute_values': [('Color', 'Blue')],
                'image_urls': ['https://assets.adidas.com/images/h_840,f_auto,q_auto:sensitive,fl_lossy,c_fill,g_auto/6f6f6f6f6f6f6f6f/backpack-HR7924_01_standard.jpg']
            },
            {
                'name': 'IKEA Dining Table',
                'description': 'Modern dining table for 4-6 people.',
                'brand': 'IKEA',
                'category': 'Kitchen & Dining',
                'condition': Product.Condition.NEW,
                'price': Decimal('400000.00'),
                'attribute_values': [('Color', 'White'), ('Material', 'Stainless Steel')],
                'image_urls': ['https://www.ikea.com/us/en/images/products/ingatorp-extendable-table-white__0737092_PE740879_S5.JPG']
            },
            {
                'name': 'Pandora Earrings',
                'description': 'Sparkling silver stud earrings.',
                'brand': 'Pandora',
                'category': 'Jewelry',
                'condition': Product.Condition.NEW,
                'price': Decimal('80000.00'),
                'attribute_values': [('Color', 'Silver'), ('Material', 'Silver')],
                'image_urls': ['https://us.pandora.net/dw/image/v2/AAVX_PRD/on/demandware.static/-/Sites-pandora-master-catalog/default/dw1a5b6b8d/images/productimages/297685C01.jpg']
            },
        ]

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
                products[product_data['name']] = product
                self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} product: {product.name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to create product {product_data["name"]}: {str(e)}'))
                continue

        # Step 7: Assign Attribute Values to Products
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

        # Step 8: Create Product Images
        self.stdout.write(self.style.NOTICE('Creating product images...'))
        for product_data in products_data:
            product = products.get(product_data['name'])
            if not product:
                continue
            for url in product_data['image_urls']:
                try:
                    response = requests.get(url, stream=True, timeout=10)
                    if response.status_code == 200:
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as img_temp:
                            img_temp.write(response.content)
                            img_temp.flush()
                            product_image = ProductImage(product=product, is_primary=not product.images.exists())
                            product_image.image.save(
                                f'{slugify(product.name)}_{uuid.uuid4().hex[:8]}.jpg',
                                File(img_temp),
                                save=True
                            )
                            self.stdout.write(self.style.SUCCESS(f'Added image for product: {product.name}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to download image {url}: {str(e)}'))

        # Step 9: Activate Products
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

        self.stdout.write(self.style.SUCCESS('Successfully populated eCommerce data with 20 products'))