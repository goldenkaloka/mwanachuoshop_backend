from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from core.models import University, Campus
from marketplace.models import Product, Category
from estates.models import Property
from shops.models import Shop
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Populate sample location data for testing location-based filtering'

    def handle(self, *args, **options):
        # Get universities and campuses
        universities = University.objects.filter(is_active=True)
        campuses = Campus.objects.filter(is_active=True)
        
        if not universities.exists():
            self.stdout.write(self.style.ERROR('No universities found. Run populate_campuses first.'))
            return
            
        if not campuses.exists():
            self.stdout.write(self.style.ERROR('No campuses found. Run populate_campuses first.'))
            return

        # Sample location data around Dar es Salaam
        dar_es_salaam_locations = [
            {'lat': -6.7735, 'lng': 39.2692, 'name': 'Mlimani Area'},
            {'lat': -6.8124, 'lng': 39.2331, 'name': 'Muhimbili Area'},
            {'lat': -6.8235, 'lng': 39.2695, 'name': 'Ilala Area'},
            {'lat': -6.7735, 'lng': 39.2692, 'name': 'City Centre'},
            {'lat': -6.8124, 'lng': 39.2331, 'name': 'Muhimbili Campus Area'},
        ]

        # Sample product data
        product_data = [
            {'name': 'Laptop for Students', 'price': 500000, 'description': 'Affordable laptop for university students'},
            {'name': 'Textbooks Bundle', 'price': 25000, 'description': 'Essential textbooks for various courses'},
            {'name': 'Student Backpack', 'price': 15000, 'description': 'Durable backpack for daily use'},
            {'name': 'Scientific Calculator', 'price': 8000, 'description': 'Advanced calculator for engineering students'},
            {'name': 'Study Desk Lamp', 'price': 12000, 'description': 'LED desk lamp for late-night studying'},
            {'name': 'Wireless Mouse', 'price': 5000, 'description': 'Comfortable wireless mouse for laptops'},
            {'name': 'USB Flash Drive 32GB', 'price': 8000, 'description': 'High-speed USB drive for assignments'},
            {'name': 'Student ID Card Holder', 'price': 2000, 'description': 'Protective holder for student ID'},
        ]

        # Sample property data
        property_data = [
            {'title': 'Student Apartment Near Campus', 'price': 150000, 'description': 'Furnished 1-bedroom apartment'},
            {'title': 'Shared Student Housing', 'price': 80000, 'description': 'Shared accommodation for students'},
            {'title': 'Studio Apartment', 'price': 120000, 'description': 'Compact studio near university'},
            {'title': 'Student Hostel Room', 'price': 60000, 'description': 'Single room in student hostel'},
            {'title': 'Family House Near Campus', 'price': 300000, 'description': 'Large house suitable for families'},
        ]

        # Sample shop data
        shop_data = [
            {'name': 'Campus Bookstore', 'description': 'Textbooks and stationery'},
            {'name': 'Student Cafe', 'description': 'Affordable meals and coffee'},
            {'name': 'Tech Gadgets Store', 'description': 'Electronics and accessories'},
            {'name': 'Printing Services', 'description': 'Document printing and binding'},
            {'name': 'Student Pharmacy', 'description': 'Health and wellness products'},
        ]

        created_count = 0

        # Create products with location data
        self.stdout.write('Creating products with location data...')
        for i, product_info in enumerate(product_data):
            location = random.choice(dar_es_salaam_locations)
            university = random.choice(universities)
            campus = random.choice(campuses.filter(university=university))
            
            # Get or create a category
            category, created = Category.objects.get_or_create(
                name='Electronics' if 'laptop' in product_info['name'].lower() or 'calculator' in product_info['name'].lower() else 'Stationery',
                defaults={'description': 'General category'}
            )
            
            # Create Point object for location
            point = Point(float(location['lng']), float(location['lat']))
            
            product = Product.objects.create(
                name=product_info['name'],
                price=product_info['price'],
                description=product_info['description'],
                category=category,
                location=point,
                is_active=True
            )
            created_count += 1
            self.stdout.write(f'  Created product: {product.name} at {location["name"]}')

        # Create properties with location data
        self.stdout.write('Creating properties with location data...')
        for i, property_info in enumerate(property_data):
            location = random.choice(dar_es_salaam_locations)
            university = random.choice(universities)
            campus = random.choice(campuses.filter(university=university))
            
            # Create Point object for location
            point = Point(float(location['lng']), float(location['lat']))
            
            property_obj = Property.objects.create(
                title=property_info['title'],
                price=property_info['price'],
                description=property_info['description'],
                location=point,
                is_available=True,
                is_active=True
            )
            created_count += 1
            self.stdout.write(f'  Created property: {property_obj.title} at {location["name"]}')

        # Create shops with location data
        self.stdout.write('Creating shops with location data...')
        for i, shop_info in enumerate(shop_data):
            location = random.choice(dar_es_salaam_locations)
            university = random.choice(universities)
            campus = random.choice(campuses.filter(university=university))
            
            # Create Point object for location
            point = Point(float(location['lng']), float(location['lat']))
            
            shop = Shop.objects.create(
                name=shop_info['name'],
                description=shop_info['description'],
                location=point,
                is_active=True
            )
            created_count += 1
            self.stdout.write(f'  Created shop: {shop.name} at {location["name"]}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} items with location data')
        )
        
        # Summary
        self.stdout.write('\nSummary:')
        self.stdout.write(f'  Products with location: {Product.objects.filter(location__isnull=False).count()}')
        self.stdout.write(f'  Properties with location: {Property.objects.filter(location__isnull=False).count()}')
        self.stdout.write(f'  Shops with location: {Shop.objects.filter(location__isnull=False).count()}') 