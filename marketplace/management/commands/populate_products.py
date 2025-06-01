from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.utils import IntegrityError
from marketplace.models import Category, Brand, Attribute, AttributeValue

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates a balanced e-commerce ecosystem with real-world data for university students in Tanzania'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Create or get the user
                user, created = User.objects.get_or_create(
                    email='goldenkaloka@gmail.com',
                    defaults={
                        'username': 'goldenkaloka',
                        'email': 'goldenkaloka@gmail.com',
                        'phonenumber': '+255123456789',
                    }
                )
                if created:
                    user.set_password('Gold@002')
                    user.save()
                    self.stdout.write(self.style.SUCCESS('User created successfully'))
                else:
                    self.stdout.write(self.style.SUCCESS('User already exists'))

                # Define real-world categories (10 main, 5 subcategories each)
                main_categories = [
                    'Textbooks', 'Electronics', 'Clothing', 'Stationery', 'Services',
                    'Food & Beverages', 'Dorm Essentials', 'Sports Gear', 'Accessories', 'Health & Personal Care'
                ]
                subcategories = {
                    'Textbooks': ['Engineering', 'Business', 'Sciences', 'Arts', 'Medical'],
                    'Electronics': ['Smartphones', 'Laptops', 'Accessories', 'Audio', 'Tablets'],
                    'Clothing': ['Casual', 'Formal', 'Traditional', 'Sportswear', 'Footwear'],
                    'Stationery': ['Notebooks', 'Pens', 'Calculators', 'Art Supplies', 'Organizers'],
                    'Services': ['Tutoring', 'Freelance', 'Tech Support', 'Printing', 'Career Prep'],
                    'Food & Beverages': ['Snacks', 'Drinks', 'Meals', 'Desserts', 'Supplements'],
                    'Dorm Essentials': ['Bedding', 'Storage', 'Lighting', 'Appliances', 'Decor'],
                    'Sports Gear': ['Football', 'Fitness', 'Outdoor', 'Athletics', 'Accessories'],
                    'Accessories': ['Bags', 'Watches', 'Jewelry', 'Tech Gadgets', 'Travel'],
                    'Health & Personal Care': ['Toiletries', 'Skincare', 'Hygiene', 'Wellness', 'First Aid']
                }
                categories = {}

                # Create main categories
                for idx, cat_name in enumerate(main_categories, 1):
                    category, _ = Category.objects.get_or_create(
                        name=cat_name,
                        defaults={'parent': None, 'is_active': True}
                    )
                    categories[cat_name] = category
                    self.stdout.write(self.style.SUCCESS(f'Main category "{cat_name}" created or retrieved'))

                # Create subcategories
                for main_cat in main_categories:
                    parent = categories[main_cat]
                    for sub_idx, sub_name in enumerate(subcategories[main_cat], 1):
                        sub_cat_name = f'{sub_name}_{main_cat}'
                        category, _ = Category.objects.get_or_create(
                            name=sub_cat_name,
                            defaults={'parent': parent, 'is_active': True}
                        )
                        categories[sub_cat_name] = category
                        self.stdout.write(self.style.SUCCESS(f'Subcategory "{sub_cat_name}" created or retrieved'))

                # Create brands (50, balanced across categories)
                brands_list = [
                    'Samsung', 'Apple', 'Nike', 'Adidas', 'Pearson', 'Oxford University Press', 'HP', 'Dell',
                    'H&M', 'Zara', 'Azam', 'Tigo', 'Lenovo', 'Canon', 'Sony', 'Bic', 'Staedtler', 'Nescafe',
                    'Kilimanjaro', 'Lipton', 'Puma', 'Uniqlo', 'Anker', 'JBL', 'Xiaomi', 'Vodacom', 'Nivea',
                    'Dove', 'Colgate', 'Dettol', 'Casio', 'Seiko', 'Ray-Ban', 'Herschel', 'Logitech', 'Pilot',
                    'Faber-Castell', 'Sharpie', 'Milo', 'Pepsi', 'Sprite', 'Red Bull', 'Blue Band', 'Omo',
                    'Vaseline', 'Oral-B', 'Listerine', 'Garnier', 'Patanjali', 'Airtel'
                ]
                brands = []
                category_keys = list(categories.keys())
                for i in range(50):
                    brand_name = brands_list[i]
                    category = categories[category_keys[i % len(category_keys)]]
                    brand, _ = Brand.objects.get_or_create(
                        name=brand_name,
                        defaults={'category': category}
                    )
                    brands.append(brand)
                    self.stdout.write(self.style.SUCCESS(f'Brand "{brand.name}" created or retrieved'))

                # Create attributes (50, ~5 per category)
                attribute_types = [
                    'Subject', 'ISBN', 'Binding', 'Language', 'Condition',  # Textbooks
                    'Storage', 'Screen Size', 'Connectivity', 'Brand', 'Battery',  # Electronics
                    'Size', 'Fabric', 'Style', 'Fit', 'Colour',  # Clothing
                    'Type', 'Ink Color', 'Page Count', 'Size', 'Binding',  # Stationery
                    'Type', 'Duration', 'Delivery Mode', 'Language', 'Expertise',  # Services
                    'Type', 'Volume', 'Flavor', 'Dietary', 'Packaging',  # Food & Beverages
                    'Type', 'Material', 'Colour', 'Dimensions', 'Assembly',  # Dorm Essentials
                    'Type', 'Size', 'Surface', 'Brand', 'Durability',  # Sports Gear
                    'Type', 'Material', 'Colour', 'Compatibility', 'Capacity',  # Accessories
                    'Type', 'Volume', 'Scent', 'Ingredient', 'Application'  # Health & Personal Care
                ]
                attributes = {}
                attribute_keys = []
                for i in range(50):
                    attr_name = f'{attribute_types[i]}_{i + 1:02d}'  # Ensure unique names
                    attribute, _ = Attribute.objects.get_or_create(name=attr_name)
                    attributes[attr_name] = attribute
                    attribute_keys.append(attr_name)
                    self.stdout.write(self.style.SUCCESS(f'Attribute "{attr_name}" created or retrieved'))

                # Define attribute values (real-world, balanced)
                attribute_values_data = {
                    'Textbooks': [
                        {'attribute': 'Subject', 'values': ['Calculus', 'Microeconomics', 'Physics', 'Literature']},
                        {'attribute': 'ISBN', 'values': ['9780135189238', '9780078021510', '9781119367505', '9780321976444']},
                        {'attribute': 'Binding', 'values': ['Hardcover', 'Softcover', 'eBook']},
                        {'attribute': 'Language', 'values': ['English', 'Kiswahili']},
                        {'attribute': 'Condition', 'values': ['New', 'Used', 'Like New']},
                    ],
                    'Electronics': [
                        {'attribute': 'Storage', 'values': ['64GB', '128GB', '256GB']},
                        {'attribute': 'Screen Size', 'values': ['6.1 inch', '13.3 inch', '15.6 inch']},
                        {'attribute': 'Connectivity', 'values': ['4G', 'Wi-Fi', 'Bluetooth']},
                        {'attribute': 'Brand', 'values': ['Samsung', 'Apple', 'Xiaomi']},
                        {'attribute': 'Battery', 'values': ['3000mAh', '4000mAh', '5000mAh']},
                    ],
                    'Clothing': [
                        {'attribute': 'Size', 'values': ['S', 'M', 'L']},
                        {'attribute': 'Fabric', 'values': ['Cotton', 'Chiffon', 'Khaki']},
                        {'attribute': 'Style', 'values': ['Casual', 'Traditional', 'Sportswear']},
                        {'attribute': 'Fit', 'values': ['Slim', 'Regular', 'Loose']},
                        {'attribute': 'Colour', 'values': ['Blue', 'Black', 'White']},
                    ],
                    'Stationery': [
                        {'attribute': 'Type', 'values': ['Ballpoint Pen', 'Notebook', 'Calculator']},
                        {'attribute': 'Ink Color', 'values': ['Blue', 'Black', 'Red']},
                        {'attribute': 'Page Count', 'values': ['100 Pages', '200 Pages']},
                        {'attribute': 'Size', 'values': ['A4', 'A5']},
                        {'attribute': 'Binding', 'values': ['Spiral', 'Hardbound']},
                    ],
                    'Services': [
                        {'attribute': 'Type', 'values': ['Math Tutoring', 'Coding Help', 'Essay Editing']},
                        {'attribute': 'Duration', 'values': ['1 Hour', '2 Hours']},
                        {'attribute': 'Delivery Mode', 'values': ['Online', 'In-Person']},
                        {'attribute': 'Language', 'values': ['English', 'Kiswahili']},
                        {'attribute': 'Expertise', 'values': ['Beginner', 'Intermediate']},
                    ],
                    'Food & Beverages': [
                        {'attribute': 'Type', 'values': ['Sango', 'Mango Juice', 'Chips']},
                        {'attribute': 'Volume', 'values': ['250ml', '500ml']},
                        {'attribute': 'Flavor', 'values': ['Sweet', 'Spicy']},
                        {'attribute': 'Dietary', 'values': ['Halal', 'Vegan']},
                        {'attribute': 'Packaging', 'values': ['Bottle', 'Pouch']},
                    ],
                    'Dorm Essentials': [
                        {'attribute': 'Type', 'values': ['Bed Sheets', 'Desk Lamp', 'Storage Bin']},
                        {'attribute': 'Material', 'values': ['Cotton', 'Plastic']},
                        {'attribute': 'Colour', 'values': ['White', 'Blue']},
                        {'attribute': 'Dimensions', 'values': ['Single Bed', '30x40cm']},
                        {'attribute': 'Assembly', 'values': ['Required', 'Not Required']},
                    ],
                    'Sports Gear': [
                        {'attribute': 'Type', 'values': ['Football', 'Running Shoes']},
                        {'attribute': 'Size', 'values': ['7', '9']},
                        {'attribute': 'Surface', 'values': ['Grass', 'Turf']},
                        {'attribute': 'Brand', 'values': ['Nike', 'Adidas']},
                        {'attribute': 'Durability', 'values': ['Standard', 'High']},
                    ],
                    'Accessories': [
                        {'attribute': 'Type', 'values': ['Backpack', 'Smartwatch']},
                        {'attribute': 'Material', 'values': ['Nylon', 'Leather']},
                        {'attribute': 'Colour', 'values': ['Black', 'Brown']},
                        {'attribute': 'Compatibility', 'values': ['Android', 'iOS']},
                        {'attribute': 'Capacity', 'values': ['15L', '20L']},
                    ],
                    'Health & Personal Care': [
                        {'attribute': 'Type', 'values': ['Toothpaste', 'Hand Sanitizer']},
                        {'attribute': 'Volume', 'values': ['100ml', '250ml']},
                        {'attribute': 'Scent', 'values': ['Mint', 'Unscented']},
                        {'attribute': 'Ingredient', 'values': ['Aloe Vera', 'Alcohol']},
                        {'attribute': 'Application', 'values': ['Daily', 'As Needed']},
                    ],
                }

                # Track used attribute-value pairs
                used_attribute_values = set()

                # Assign attribute values
                category_keys = list(categories.keys())
                for cat_idx, (category_name, category) in enumerate(categories.items(), 1):
                    cat_type = category_name.split('_')[-1] if '_' in category_name else category_name
                    attr_values = attribute_values_data.get(cat_type, [])
                    for attr_idx in range(5):
                        if attr_idx < len(attr_values):
                            attr_data = attr_values[attr_idx]
                            attr_name = f"{attr_data['attribute']}_{(attr_idx % len(attribute_types) + 1):02d}"
                            try:
                                attribute = Attribute.objects.get(name=attr_name)
                                base_values = attr_data['values']
                            except Attribute.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'Attribute "{attr_name}" not found, using fallback'))
                                attribute = attributes[attribute_keys[(attr_idx % len(attribute_keys))]]
                                base_values = [f'Value_{cat_idx:03d}_{attr_idx + 1}_{v}' for v in range(1, 4)]
                        else:
                            attribute = attributes[attribute_keys[(attr_idx % len(attribute_keys))]]
                            base_values = [f'Value_{cat_idx:03d}_{attr_idx + 1}_{v}' for v in range(1, 4)]

                        for value in base_values:
                            unique_value = value
                            suffix = 0
                            while (attribute.id, unique_value) in used_attribute_values:
                                suffix += 1
                                unique_value = f'{value}_{cat_idx:03d}_{suffix}'
                            
                            try:
                                attr_value, created = AttributeValue.objects.get_or_create(
                                    attribute=attribute,
                                    category=category,
                                    value=unique_value
                                )
                                if created:
                                    used_attribute_values.add((attribute.id, unique_value))
                                    self.stdout.write(self.style.SUCCESS(
                                        f'AttributeValue "{attribute.name}: {unique_value}" for category "{category_name}" created'
                                    ))
                                else:
                                    self.stdout.write(self.style.SUCCESS(
                                        f'AttributeValue "{attribute.name}: {unique_value}" for category "{category_name}" already exists'
                                    ))
                            except IntegrityError:
                                self.stdout.write(self.style.WARNING(
                                    f'Skipped AttributeValue "{attribute.name}: {unique_value}" due to integrity error'
                                ))

                self.stdout.write(self.style.SUCCESS('Successfully populated balanced e-commerce ecosystem'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error occurred: {str(e)}'))
            raise

    def add_arguments(self, parser):
        pass