from django.core.management.base import BaseCommand
from django.db import IntegrityError
from marketplace.models import Brand, Category

class Command(BaseCommand):
    help = 'Populate Brand model with brands known globally and in Tanzania for specified e-commerce categories'

    def handle(self, *args, **kwargs):
        # Define categories and their associated brands, including Tanzania-popular and global brands
        category_brands = {
            'Apparel & Accessories': [
                # Global
                'Nike', 'Adidas', 'H&M', 'Zara', 'Uniqlo', 'Levi’s', 'Gucci', 'Ralph Lauren', 'Tommy Hilfiger',
                'Calvin Klein', 'Lacoste', 'Forever 21', 'ASOS', 'Topshop', 'Mango', 'Puma', 'Superdry',
                'Abercrombie & Fitch', 'American Eagle', 'Gap', 'Banana Republic', 'J.Crew', 'Old Navy', 'Primark',
                'Shein',
                # Tanzania/Africa
                'Ankara House', 'Kipepeo Clothing', 'Moshions (Rwanda)', 'Laduma Ngxokolo (MaXhosa Africa)',
                'ZaraHash (Tanzania)', 'KikoRomeo (Kenya)', 'AfriChic', 'ChicAura Designs (Tanzania)',
                'Duro Olowu (Nigeria)', 'SawaSawa (Tanzania)'
            ],
            'Clothing': [
                # Same as Apparel & Accessories
                'Nike', 'Adidas', 'H&M', 'Zara', 'Uniqlo', 'Levi’s', 'Gucci', 'Ralph Lauren', 'Tommy Hilfiger',
                'Calvin Klein', 'Lacoste', 'Forever 21', 'ASOS', 'Topshop', 'Mango', 'Puma', 'Superdry',
                'Abercrombie & Fitch', 'American Eagle', 'Gap', 'Banana Republic', 'J.Crew', 'Old Navy', 'Primark',
                'Shein', 'Ankara House', 'Kipepeo Clothing', 'Moshions (Rwanda)', 'Laduma Ngxokolo (MaXhosa Africa)',
                'ZaraHash (Tanzania)', 'KikoRomeo (Kenya)', 'AfriChic', 'ChicAura Designs (Tanzania)',
                'Duro Olowu (Nigeria)', 'SawaSawa (Tanzania)'
            ],
            'Jewelry': [
                # Global
                'Tiffany & Co.', 'Pandora', 'Cartier', 'Swarovski', 'Kay Jewelers', 'David Yurman', 'Mejuri',
                'Chopard', 'Bvlgari', 'Van Cleef & Arpels', 'Harry Winston', 'James Allen', 'Brilliant Earth',
                'Blue Nile', 'Gorjana', 'Kendra Scott', 'BaubleBar', 'Alex and Ani', 'Monica Vinader', 'Missoma',
                # Tanzania/Africa
                'Adele Dejak (Kenya)', 'Pichulik (South Africa)', 'Zuri Designs (Tanzania)', 'Afrigems (Tanzania)',
                'Lalesso (Kenya)', 'Soko (Kenya)'
            ],
            'Shoes': [
                # Global
                'Nike', 'Adidas', 'Puma', 'New Balance', 'Reebok', 'Skechers', 'Asics', 'Vans', 'Converse',
                'Clarks', 'Dr. Martens', 'Timberland', 'Crocs', 'Birkenstock', 'Salomon', 'Merrell', 'Under Armour',
                'Brooks', 'Hoka One One', 'Saucony', 'TOMS', 'UGG', 'Steve Madden', 'Aldo', 'Cole Haan', 'Ecco',
                'Sperry',
                # Tanzania/Africa
                'Sawa Shoes (Tanzania)', 'Kipepeo Footwear', 'Ubuntu Footwear (Kenya)', 'Enda (Kenya)',
                'SoleRebels (Ethiopia)'
            ],
            'Electronics': [
                # Global
                'Apple', 'Samsung', 'Sony', 'LG', 'Dell', 'HP', 'Bose', 'Lenovo', 'Asus', 'Acer', 'Microsoft',
                'JBL', 'Anker', 'Logitech', 'Canon', 'Nikon', 'Panasonic', 'GoPro', 'Fujifilm', 'Bowers & Wilkins',
                'Dyson', 'Philips', 'Toshiba', 'Sharp', 'Garmin', 'Fitbit', 'Sennheiser', 'Bang & Olufsen',
                # Tanzania/Africa (limited local brands, focus on global availability)
                'Tecno (Africa)', 'Infinix (Africa)', 'Itel (Africa)'
            ],
            'Cameras & Photography': [
                # Global
                'Canon', 'Nikon', 'Sony', 'Fujifilm', 'Panasonic', 'GoPro', 'Leica', 'Olympus', 'Pentax',
                'Sigma', 'Tamron', 'Hasselblad', 'DJI', 'Insta360', 'Ricoh', 'Polaroid', 'Kodak'
                # Tanzania/Africa: No prominent local camera brands; global brands dominate
            ],
            'Laptops': [
                # Global
                'Apple', 'Dell', 'HP', 'Lenovo', 'Asus', 'Acer', 'Microsoft', 'Razer', 'MSI', 'Samsung',
                'LG', 'Toshiba', 'Alienware', 'Framework', 'Huawei'
                # Tanzania/Africa: No prominent local laptop brands; global brands dominate
            ],
            'Mobile Phones': [
                # Global
                'Apple', 'Samsung', 'Google', 'OnePlus', 'Xiaomi', 'Huawei', 'Oppo', 'Vivo', 'Motorola',
                'Nokia', 'Sony', 'Realme', 'Asus', 'Nothing', 'ZTE',
                # Tanzania/Africa
                'Tecno (Africa)', 'Infinix (Africa)', 'Itel (Africa)'
            ],
            'Home & Garden': [
                # Global
                'IKEA', 'West Elm', 'Ashley Furniture', 'Bosch', 'Dyson', 'Wayfair', 'Crate & Barrel', 'Pottery Barn',
                'CB2', 'Room & Board', 'La-Z-Boy', 'Herman Miller', 'Overstock', 'AllModern', 'Joss & Main',
                'Surya', 'Ruggable', 'Lowe’s', 'Home Depot',
                # Tanzania/Africa
                'Mudu Home (Tanzania)', 'Zanui (Africa)', 'Kilimanjaro Furniture (Tanzania)'
            ],
            'Furniture': [
                # Global
                'IKEA', 'West Elm', 'Ashley Furniture', 'La-Z-Boy', 'Herman Miller', 'Room & Board', 'CB2',
                'Pottery Barn', 'Crate & Barrel', 'Wayfair', 'Overstock', 'AllModern', 'Joss & Main',
                'Article', 'Joybird', 'Arhaus', 'Restoration Hardware',
                # Tanzania/Africa
                'Mudu Home (Tanzania)', 'Kilimanjaro Furniture (Tanzania)', 'Zanui (Africa)'
            ],
            'Kitchen & Dining': [
                # Global
                'Cuisinart', 'KitchenAid', 'Le Creuset', 'Pyrex', 'Tefal', 'All-Clad', 'Calphalon', 'Staub',
                'Zwilling J.A. Henckels', 'Wüsthof', 'OXO', 'Tupperware', 'Lodge', 'Nespresso', 'Keurig',
                'Vitamix', 'Breville', 'Anolon', 'GreenPan', 'Corelle',
                # Tanzania/Africa: Limited local brands; global brands dominate via retailers like Game
            ],
            'Sporting Goods': [
                # Global
                'Wilson', 'Spalding', 'Under Armour', 'Nike', 'Adidas', 'Puma', 'Callaway', 'TaylorMade',
                'Rawlings', 'Mizuno', 'Easton', 'Head', 'Babolat', 'Yonex', 'Franklin Sports', 'Speedo',
                'Columbia', 'Salomon', 'Merrell', 'The North Face',
                # Tanzania/Africa
                'Sawa Sports (Tanzania)', 'AfriSport (Africa)'
            ],
            'Outdoor Gear': [
                # Global
                'The North Face', 'Patagonia', 'Columbia', 'REI', 'Coleman', 'Arc’teryx', 'Marmot', 'Osprey',
                'Black Diamond', 'Salomon', 'Merrell', 'Kelty', 'Big Agnes', 'MSR', 'Therm-a-Rest',
                'Yeti', 'Helinox', 'Sea to Summit', 'Nemo Equipment', 'Gregory',
                # Tanzania/Africa
                'AfriCamp (Tanzania)', 'Safari Gear (Tanzania)'
            ]
        }

        # Get or create categories
        category_names = list(category_brands.keys())
        categories = {}
        for cat_name in category_names:
            try:
                category = Category.objects.get(name=cat_name)
                categories[cat_name] = category
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Category "{cat_name}" not found. Please create it first.'))
                continue

        # Create Brands and associate with categories
        for cat_name, brand_names in category_brands.items():
            if cat_name not in categories:
                continue
            category = categories[cat_name]
            for brand_name in brand_names:
                try:
                    # Create or get Brand (logo and created_by set to None as per model)
                    brand, created = Brand.objects.get_or_create(
                        name=brand_name,
                        defaults={'is_active': False, 'logo': None, 'created_by': None}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created brand: {brand_name}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Brand {brand_name} already exists.'))

                    # Add category to brand's ManyToManyField
                    brand.categories.add(category)
                    self.stdout.write(self.style.SUCCESS(f'Associated {brand_name} with category {cat_name}'))
                except IntegrityError:
                    self.stdout.write(self.style.WARNING(f'Brand {brand_name} already exists or failed to create.'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing brand {brand_name} for category {cat_name}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Command completed successfully.'))