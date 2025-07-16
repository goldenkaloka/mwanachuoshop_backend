import os
import random
import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files import File
from django.conf import settings
from django.utils import timezone
from phonenumber_field.phonenumber import PhoneNumber
from django.contrib.gis.geos import Point
from shops.models import (
    Shop, ShopMedia, Promotion, Event, Services, 
    UserOffer, Subscription
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample shop data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of shops to create (default: 10)'
        )
        parser.add_argument(
            '--media-dir',
            type=str,
            help='Directory containing sample media files',
            default='sample_media/shops'
        )

    def handle(self, *args, **options):
        self.count = options['count']
        self.media_dir = options['media_dir']
        
        self.stdout.write(f"Starting to populate {self.count} shops...")
        
        # Verify media directory exists
        if not os.path.exists(self.media_dir):
            self.stdout.write(self.style.ERROR(
                f"Media directory '{self.media_dir}' not found. "
                "Please create it with shop profile images."
            ))
            return
        
        # Create test users if they don't exist
        users = self.create_test_users()
        
        # Create shops
        self.create_shops(users)
        
        self.stdout.write(self.style.SUCCESS(
            f"Successfully populated {self.count} shops with related data!"
        ))

    def create_test_users(self):
        users = []
        for i in range(1, 6):  # Create 5 test users
            username = f"shopowner{i}"
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password="testpass123"
                )
                self.stdout.write(f"Created user: {username}")
            
            # Create UserOffer for each user
            self.create_user_offer(user)
            users.append(user)
        
        return users

    def create_user_offer(self, user):
        offer, created = UserOffer.objects.get_or_create(
            user=user,
            defaults={
                'free_products_remaining': random.randint(5, 20),
                'free_estates_remaining': random.randint(0, 5),
                'shop_trial_end_date': timezone.now() + timedelta(days=random.randint(7, 30))
            }
        )
        if created:
            self.stdout.write(f"Created UserOffer for {user.username}")

    def create_shops(self, users):
        # Tanzanian phone number prefixes
        tz_prefixes = ['74', '75', '76', '77', '78', '79', '65', '67', '68', '69']
        
        # Sample locations in Tanzania with coordinates
        tz_locations = [
            {"name": "Dar es Salaam", "lat": -6.8235, "lng": 39.2695},
            {"name": "Arusha", "lat": -3.3731, "lng": 36.6823},
            {"name": "Mwanza", "lat": -2.5167, "lng": 32.9000},
            {"name": "Dodoma", "lat": -6.1730, "lng": 35.7460},
            {"name": "Mbeya", "lat": -8.9000, "lng": 33.4500},
            {"name": "Morogoro", "lat": -6.8167, "lng": 37.6667},
            {"name": "Tanga", "lat": -5.0667, "lng": 39.1000},
            {"name": "Zanzibar City", "lat": -6.1659, "lng": 39.2026},
            {"name": "Kigoma", "lat": -4.8833, "lng": 29.6333},
            {"name": "Moshi", "lat": -3.3500, "lng": 37.3333}
        ]
        
        # Sample shop names by category
        shop_categories = {
            "restaurant": ["Mama's Kitchen", "Spice Garden", "Nyama Choma Grill", "Zanzibar Flavors"],
            "fashion": ["Swahili Styles", "Kanga Boutique", "Kitenge Palace", "Afro Chic"],
            "electronics": ["Tech Hub", "Gadget Zone", "Smart Solutions", "Digital World"],
            "beauty": ["Spa Haven", "Glow Salon", "Natural Beauty", "Hair Masters"],
            "grocery": ["Fresh Mart", "Daily Needs", "Village Market", "Organic Corner"]
        }
        
        # Get available sample images
        sample_images = self.get_sample_files(self.media_dir)
        
        if not sample_images:
            self.stdout.write(self.style.ERROR(
                f"No sample images found in {self.media_dir}. "
                "Please add some sample image files (JPG, PNG)."
            ))
            return
        
        for i in range(1, self.count + 1):
            # Select random user (cycling through the 5 we created)
            user = users[i % len(users)]
            
            # Create shop data
            category = random.choice(list(shop_categories.keys()))
            name = f"{random.choice(shop_categories[category])} {i}"
            phone = f"+255{random.choice(tz_prefixes)}{random.randint(100000, 999999)}"
            location_data = random.choice(tz_locations)
            location_point = Point(location_data["lng"], location_data["lat"])
            
            # Create operating hours
            operating_hours = {
                "monday": {"open": "08:00", "close": "18:00"},
                "tuesday": {"open": "08:00", "close": "18:00"},
                "wednesday": {"open": "08:00", "close": "18:00"},
                "thursday": {"open": "08:00", "close": "18:00"},
                "friday": {"open": "08:00", "close": "18:00"},
                "saturday": {"open": "09:00", "close": "16:00"},
                "sunday": {"open": "09:00", "close": "14:00"}
            }
            
            # Random social media links
            social_media = {
                "facebook": f"https://facebook.com/{name.replace(' ', '')}",
                "instagram": f"https://instagram.com/{name.replace(' ', '')}",
                "twitter": f"https://twitter.com/{name.replace(' ', '')}"
            } if random.choice([True, False]) else None
            
            # Select a random image
            image_path = random.choice(sample_images)
            
            with open(image_path, 'rb') as img_file:
                shop = Shop(
                    user=user,
                    name=name,
                    phone=PhoneNumber.from_string(phone),
                    location=location_point,
                    description=f"A wonderful {category} located in {location_data['name']}. "
                                f"We offer the best services and products in town!",
                    operating_hours=operating_hours,
                    social_media=social_media
                )
                shop.image.save(
                    os.path.basename(image_path),
                    File(img_file),
                    save=False
                )
                shop.save()
                
            self.stdout.write(f"Created shop: {name}")
            
            # Add shop media images
            self.add_shop_media(shop, sample_images)
            
            # Create promotions
            self.create_promotions(shop)
            
            # Create events
            self.create_events(shop)
            
            # Create services
            self.create_services(shop)
            
            # Create subscription
            self.create_subscription(shop, user)

    def add_shop_media(self, shop, sample_images):
        num_images = random.randint(1, 5)
        
        for i in range(num_images):
            image_path = random.choice(sample_images)
            
            with open(image_path, 'rb') as img_file:
                shop_media = ShopMedia(
                    shop=shop,
                    is_primary=(i == 0)  # First image is primary
                )
                shop_media.image.save(
                    os.path.basename(image_path),
                    File(img_file),
                    save=False
                )
                shop_media.save()
        
        self.stdout.write(f"Added {num_images} images to shop {shop.name}")

    def create_promotions(self, shop):
        promotion_titles = [
            "Grand Opening Discount",
            "Seasonal Sale",
            "Buy One Get One Free",
            "Student Special",
            "Weekend Flash Sale"
        ]
        
        num_promotions = random.randint(1, 3)
        
        for i in range(num_promotions):
            start_date = timezone.now() - timedelta(days=random.randint(0, 3))
            end_date = start_date + timedelta(days=random.randint(7, 30))
            
            Promotion.objects.create(
                shop=shop,
                title=f"{random.choice(promotion_titles)} {i+1}",
                description=f"Special promotion for our valued customers. "
                            f"Get amazing deals at {shop.name}!",
                start_date=start_date,
                end_date=end_date
            )
        
        self.stdout.write(f"Added {num_promotions} promotions to shop {shop.name}")

    def create_events(self, shop):
        event_titles = [
            "Live Music Night",
            "Product Launch",
            "Charity Fundraiser",
            "Cultural Festival",
            "Workshop Session"
        ]
        
        num_events = random.randint(0, 2)
        
        for i in range(num_events):
            start_time = timezone.now() + timedelta(days=random.randint(7, 60))
            end_time = start_time + timedelta(hours=random.randint(2, 6))
            
            Event.objects.create(
                shop=shop,
                title=f"{random.choice(event_titles)} {i+1}",
                description=f"Join us for an exciting event at {shop.name}. "
                           f"Food, drinks, and entertainment provided!",
                start_time=start_time,
                end_time=end_time,
                is_free=random.choice([True, False]),
                ticket_price=round(random.uniform(5000, 20000), 2) if random.choice([True, False]) else None
            )
        
        if num_events > 0:
            self.stdout.write(f"Added {num_events} events to shop {shop.name}")

    def create_services(self, shop):
        service_types = {
            "restaurant": [
                {"name": "Table Reservation", "price": 0, "duration": 60},
                {"name": "Catering Service", "price": 50000, "duration": 240},
                {"name": "Cooking Class", "price": 20000, "duration": 120}
            ],
            "fashion": [
                {"name": "Tailoring", "price": 15000, "duration": 180},
                {"name": "Clothing Repair", "price": 5000, "duration": 60},
                {"name": "Custom Design", "price": 30000, "duration": 240}
            ],
            "electronics": [
                {"name": "Device Repair", "price": 10000, "duration": 60},
                {"name": "Software Installation", "price": 15000, "duration": 90},
                {"name": "Tech Consultation", "price": 20000, "duration": 60}
            ],
            "beauty": [
                {"name": "Hair Styling", "price": 10000, "duration": 60},
                {"name": "Manicure/Pedicure", "price": 15000, "duration": 90},
                {"name": "Facial Treatment", "price": 20000, "duration": 120}
            ],
            "grocery": [
                {"name": "Home Delivery", "price": 3000, "duration": 30},
                {"name": "Bulk Order Discount", "price": 0, "duration": 0},
                {"name": "Custom Packaging", "price": 5000, "duration": 15}
            ]
        }
        
        # Determine shop category based on name
        category = "restaurant"  # default
        for cat, names in service_types.items():
            if any(name.lower() in shop.name.lower() for name in names):
                category = cat
                break
        
        for service in service_types[category]:
            Services.objects.create(
                shop=shop,
                name=service['name'],
                description=f"Professional {service['name']} service at {shop.name}",
                price=service['price'],
                duration=timedelta(minutes=service['duration'])
            )
        
        self.stdout.write(f"Added {len(service_types[category])} services to shop {shop.name}")

    def create_subscription(self, shop, user):
        is_trial = random.choice([True, False])
        start_date = timezone.now() - timedelta(days=random.randint(0, 10))
        
        if is_trial:
            end_date = start_date + timedelta(days=random.randint(7, 30))
            status = Subscription.Status.ACTIVE
        else:
            end_date = start_date + timedelta(days=random.randint(30, 365))
            status = random.choice([
                Subscription.Status.ACTIVE,
                Subscription.Status.ACTIVE,
                Subscription.Status.EXPIRED,
                Subscription.Status.CANCELED
            ])
        
        Subscription.objects.create(
            user=user,
            shop=shop,
            status=status,
            start_date=start_date,
            end_date=end_date,
            is_trial=is_trial
        )
        
        self.stdout.write(f"Added {'trial' if is_trial else 'regular'} subscription for shop {shop.name}")

    def get_sample_files(self, directory):
        """Get all image files from a directory"""
        if not os.path.exists(directory):
            return []
            
        extensions = ['.jpg', '.jpeg', '.png', '.gif']
        
        files = []
        for filename in os.listdir(directory):
            if os.path.splitext(filename)[1].lower() in extensions:
                files.append(os.path.join(directory, filename))
        
        return files