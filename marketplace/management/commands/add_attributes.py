from django.core.management.base import BaseCommand
from django.db import IntegrityError
from marketplace.models import Attribute, AttributeValue, Category

class Command(BaseCommand):
    help = 'Populate Attribute and AttributeValue models for specified e-commerce categories, excluding Brand'

    def handle(self, *args, **kwargs):
        # Define categories based on provided list
        category_names = [
            'Apparel & Accessories',
            'Clothing',
            'Jewelry',
            'Shoes',
            'Electronics',
            'Cameras & Photography',
            'Laptops',
            'Mobile Phones',
            'Home & Garden',
            'Furniture',
            'Kitchen & Dining',
            'Sporting Goods',
            'Outdoor Gear'
        ]

        # Define attributes and their possible values for each category, excluding Brand
        attribute_data = {
            'Apparel & Accessories': {
                'Size': ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'One Size'],
                'Color': ['Black', 'White', 'Blue', 'Red', 'Green', 'Yellow', 'Grey', 'Pink', 'Brown', 'Purple', 'Beige', 'Navy', 'Orange'],
                'Material': ['Cotton', 'Polyester', 'Wool', 'Silk', 'Linen', 'Denim', 'Leather', 'Synthetic', 'Viscose', 'Nylon', 'Spandex'],
                'Gender': ['Men', 'Women', 'Unisex', 'Kids'],
                'Fit': ['Slim', 'Regular', 'Loose', 'Athletic', 'Oversized', 'Tailored'],
                'Style': ['Casual', 'Formal', 'Athleisure', 'Vintage', 'Modern', 'Bohemian', 'Streetwear'],
                'Care Instructions': ['Machine Wash', 'Hand Wash', 'Dry Clean Only', 'Spot Clean'],
                'Sleeve Length': ['Short', 'Long', 'Sleeveless', '3/4 Sleeve', 'Cap Sleeve'],
                'Neckline': ['Crew Neck', 'V-Neck', 'Turtleneck', 'Collar', 'Scoop Neck', 'Boat Neck'],
                'Pattern': ['Solid', 'Striped', 'Checkered', 'Floral', 'Polka Dot', 'Camouflage', 'Plaid', 'Geometric'],
                'Season': ['Spring', 'Summer', 'Fall', 'Winter', 'All Seasons'],
                'Collar Type': ['Spread', 'Point', 'Button-Down', 'Mandarin', 'Stand-Up'],
                'Occasion': ['Everyday', 'Work', 'Party', 'Wedding', 'Outdoor', 'Evening'],
                'Fabric Weight': ['Light', 'Medium', 'Heavy'],
                'Closure Type': ['Zipper', 'Button', 'Pull-On', 'Drawstring', 'Hook-and-Eye'],
                'Stretch': ['Non-Stretch', 'Low Stretch', 'High Stretch'],
                'Hemline': ['Straight', 'Asymmetrical', 'Curved', 'High-Low'],
            },
            'Clothing': {
                'Size': ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'One Size'],
                'Color': ['Black', 'White', 'Blue', 'Red', 'Green', 'Yellow', 'Grey', 'Pink', 'Brown', 'Purple', 'Beige', 'Navy', 'Orange'],
                'Material': ['Cotton', 'Polyester', 'Wool', 'Silk', 'Linen', 'Denim', 'Leather', 'Synthetic', 'Viscose', 'Nylon', 'Spandex'],
                'Gender': ['Men', 'Women', 'Unisex', 'Kids'],
                'Fit': ['Slim', 'Regular', 'Loose', 'Athletic', 'Oversized', 'Tailored'],
                'Style': ['Casual', 'Formal', 'Athleisure', 'Vintage', 'Modern', 'Bohemian', 'Streetwear'],
                'Care Instructions': ['Machine Wash', 'Hand Wash', 'Dry Clean Only', 'Spot Clean'],
                'Sleeve Length': ['Short', 'Long', 'Sleeveless', '3/4 Sleeve', 'Cap Sleeve'],
                'Neckline': ['Crew Neck', 'V-Neck', 'Turtleneck', 'Collar', 'Scoop Neck', 'Boat Neck'],
                'Pattern': ['Solid', 'Striped', 'Checkered', 'Floral', 'Polka Dot', 'Camouflage', 'Plaid', 'Geometric'],
                'Season': ['Spring', 'Summer', 'Fall', 'Winter', 'All Seasons'],
                'Collar Type': ['Spread', 'Point', 'Button-Down', 'Mandarin', 'Stand-Up'],
                'Occasion': ['Everyday', 'Work', 'Party', 'Wedding', 'Outdoor', 'Evening'],
                'Fabric Weight': ['Light', 'Medium', 'Heavy'],
                'Closure Type': ['Zipper', 'Button', 'Pull-On', 'Drawstring', 'Hook-and-Eye'],
                'Stretch': ['Non-Stretch', 'Low Stretch', 'High Stretch'],
                'Hemline': ['Straight', 'Asymmetrical', 'Curved', 'High-Low'],
            },
            'Jewelry': {
                'Material': ['Gold', 'Silver', 'Platinum', 'Stainless Steel', 'Titanium', 'Gemstone', 'Rose Gold', 'Brass', 'Copper'],
                'Gemstone': ['Diamond', 'Emerald', 'Ruby', 'Sapphire', 'Amethyst', 'Topaz', 'Pearl', 'Opal', 'None'],
                'Color': ['Gold', 'Silver', 'Rose Gold', 'Black', 'Multicolor', 'White Gold'],
                'Gender': ['Men', 'Women', 'Unisex'],
                'Type': ['Necklace', 'Ring', 'Bracelet', 'Earrings', 'Pendant', 'Watch', 'Anklet', 'Brooch'],
                'Style': ['Classic', 'Modern', 'Vintage', 'Minimalist', 'Bohemian', 'Statement'],
                'Weight': ['Light', 'Medium', 'Heavy'],
                'Clasp Type': ['Lobster', 'Toggle', 'Magnetic', 'Box', 'Spring Ring', 'Hook'],
                'Chain Length': ['14"', '16"', '18"', '20"', '24"', 'Adjustable'],
                'Finish': ['Polished', 'Matte', 'Brushed', 'Hammered', 'Textured'],
                'Carat Weight': ['0.25ct', '0.5ct', '1ct', '2ct', '3ct+'],
                'Setting Type': ['Prong', 'Bezel', 'Channel', 'Pavé'],
                'Hypoallergenic': ['Yes', 'No'],
                'Chain Type': ['Cable', 'Rope', 'Box', 'Figaro', 'Curb'],
            },
            'Shoes': {
                'Size': ['US 4', 'US 5', 'US 6', 'US 7', 'US 8', 'US 9', 'US 10', 'US 11', 'US 12', 'US 13'],
                'Color': ['Black', 'White', 'Blue', 'Red', 'Brown', 'Grey', 'Tan', 'Green', 'Navy', 'Beige'],
                'Material': ['Leather', 'Synthetic', 'Canvas', 'Suede', 'Mesh', 'Rubber', 'Nylon'],
                'Gender': ['Men', 'Women', 'Unisex', 'Kids'],
                'Style': ['Athletic', 'Casual', 'Formal', 'Running', 'Boots', 'Sandals', 'Sneakers', 'Loafers'],
                'Closure Type': ['Lace-Up', 'Slip-On', 'Velcro', 'Buckle', 'Zipper'],
                'Heel Type': ['Flat', 'Low', 'Medium', 'High', 'Wedge', 'Platform'],
                'Width': ['Narrow', 'Medium', 'Wide', 'Extra Wide'],
                'Sole Material': ['Rubber', 'EVA', 'Polyurethane', 'Leather', 'Cork'],
                'Activity': ['Running', 'Walking', 'Hiking', 'Basketball', 'Casual', 'Dance', 'Work'],
                'Arch Support': ['Low', 'Medium', 'High'],
                'Water Resistance': ['Waterproof', 'Water-Resistant', 'Non-Waterproof'],
                'Traction': ['Standard', 'High Traction', 'Non-Slip'],
                'Cushioning': ['Low', 'Medium', 'High'],
            },
            'Electronics': {
                'Color': ['Black', 'Silver', 'White', 'Grey', 'Blue', 'Gold'],
                'Power Source': ['Battery', 'Corded Electric', 'Rechargeable Battery', 'Solar', 'USB'],
                'Warranty': ['6 Months', '1 Year', '2 Years', '3 Years', 'Limited Lifetime'],
                'Connectivity': ['Wi-Fi', 'Bluetooth', 'USB', 'HDMI', 'Ethernet', 'NFC'],
                'Weight': ['Light', 'Medium', 'Heavy'],
                'Voltage': ['110V', '220V', 'Universal'],
                'Screen Type': ['LED', 'OLED', 'LCD', 'AMOLED', 'TFT'],
                'Energy Rating': ['Energy Star', 'A+', 'A++', 'A+++'],
                'Compatibility': ['iOS', 'Android', 'Windows', 'Universal'],
                'Frequency Response': ['20Hz-20kHz', '50Hz-15kHz', '100Hz-10kHz'],
                'Mounting Type': ['Wall Mount', 'Desktop', 'Portable'],
                'Noise Cancellation': ['Active', 'Passive', 'None'],
                'Operating Temperature': ['0-40°C', '-10-50°C', 'Extreme Conditions'],
            },
            'Cameras & Photography': {
                'Type': ['DSLR', 'Mirrorless', 'Point & Shoot', 'Action Camera', 'Instant Camera'],
                'Sensor Size': ['Full Frame', 'APS-C', 'Micro Four Thirds', '1-inch', '1/2.3-inch'],
                'Megapixels': ['12MP', '16MP', '20MP', '24MP', '30MP+', '50MP+'],
                'Color': ['Black', 'Silver', 'White', 'Red'],
                'Lens Mount': ['Canon EF', 'Nikon F', 'Sony E', 'Fujifilm X', 'Micro Four Thirds', 'None'],
                'Warranty': ['6 Months', '1 Year', '2 Years', '3 Years'],
                'Connectivity': ['Wi-Fi', 'Bluetooth', 'USB', 'HDMI', 'NFC'],
                'ISO Range': ['100-800', '100-1600', '100-3200', '100-6400', '100-12800+'],
                'Shutter Speed': ['1/2000s', '1/4000s', '1/8000s', '30s+'],
                'Video Resolution': ['1080p', '4K', '6K', '8K'],
                'Lens Type': ['Zoom', 'Prime', 'Wide-Angle', 'Telephoto', 'Macro'],
                'Image Stabilization': ['Optical', 'Digital', 'None'],
                'Autofocus Points': ['9', '45', '100+', 'Phase Detection'],
                'Viewfinder Type': ['Optical', 'Electronic', 'None'],
                'Battery Life': ['200 shots', '400 shots', '600 shots+'],
            },
            'Laptops': {
                'Screen Size': ['11"', '12"', '13"', '14"', '15"', '16"', '17"'],
                'Processor': ['Intel Core i3', 'Intel Core i5', 'Intel Core i7', 'Intel Core i9', 'AMD Ryzen 3', 'AMD Ryzen 5', 'AMD Ryzen 7'],
                'RAM': ['4GB', '8GB', '16GB', '32GB', '64GB'],
                'Storage': ['128GB SSD', '256GB SSD', '512GB SSD', '1TB SSD', '1TB HDD', '2TB SSD'],
                'Operating System': ['Windows', 'macOS', 'Linux', 'Chrome OS'],
                'Color': ['Silver', 'Black', 'Grey', 'White', 'Gold'],
                'Warranty': ['6 Months', '1 Year', '2 Years', '3 Years'],
                'Connectivity': ['Wi-Fi', 'Bluetooth', 'USB', 'HDMI', 'Thunderbolt', 'USB-C'],
                'Graphics Card': ['Integrated', 'NVIDIA GeForce', 'AMD Radeon', 'NVIDIA RTX'],
                'Refresh Rate': ['60Hz', '120Hz', '144Hz', '240Hz'],
                'Keyboard Type': ['Backlit', 'Mechanical', 'Standard', 'RGB'],
                'Touchscreen': ['Yes', 'No'],
                'Weight': ['Under 2lbs', '2-4lbs', '4-6lbs', '6lbs+'],
                'Resolution': ['1366x768', '1920x1080', '2560x1440', '4K'],
                'Portability': ['Ultraportable', 'Standard', 'Desktop Replacement'],
            },
            'Mobile Phones': {
                'Screen Size': ['4.7"', '5"', '5.5"', '6"', '6.5"', '6.7"', '7"'],
                'Operating System': ['iOS', 'Android'],
                'Storage': ['32GB', '64GB', '128GB', '256GB', '512GB', '1TB'],
                'Color': ['Black', 'White', 'Blue', 'Red', 'Green', 'Gold', 'Silver'],
                'Camera Resolution': ['8MP', '12MP', '16MP', '48MP', '64MP', '108MP+'],
                'Battery Life': ['2000mAh', '3000mAh', '4000mAh', '5000mAh+'],
                'Connectivity': ['5G', '4G', 'Wi-Fi', 'Bluetooth', 'NFC'],
                'Warranty': ['6 Months', '1 Year', '2 Years'],
                'Screen Type': ['AMOLED', 'IPS LCD', 'Retina', 'Super AMOLED'],
                'Water Resistance': ['IP65', 'IP67', 'IP68', 'None'],
                'SIM Type': ['Single SIM', 'Dual SIM', 'eSIM'],
                'Charging Type': ['USB-C', 'Lightning', 'Wireless', 'Fast Charging'],
                'Refresh Rate': ['60Hz', '90Hz', '120Hz', '144Hz'],
                'Processor': ['A-Series', 'Snapdragon', 'Exynos', 'Dimensity', 'Kirin'],
                'Face Unlock': ['Yes', 'No'],
            },
            'Home & Garden': {
                'Material': ['Wood', 'Metal', 'Plastic', 'Glass', 'Ceramic', 'Bamboo', 'Rattan'],
                'Color': ['Black', 'White', 'Brown', 'Green', 'Blue', 'Natural', 'Grey', 'Red'],
                'Style': ['Modern', 'Traditional', 'Rustic', 'Contemporary', 'Industrial', 'Scandinavian'],
                'Weight': ['Light', 'Medium', 'Heavy'],
                'Power Source': ['Battery', 'Corded Electric', 'Manual', 'Solar'],
                'Finish': ['Matte', 'Glossy', 'Natural', 'Painted', 'Polished'],
                'Indoor/Outdoor': ['Indoor', 'Outdoor', 'Both'],
                'Eco-Friendly': ['Yes', 'No'],
                'Certification': ['FSC-Certified', 'BPA-Free', 'Non-Toxic', 'Organic'],
                'Durability': ['Standard', 'Heavy-Duty', 'Weather-Resistant'],
                'Assembly Required': ['Yes', 'No'],
                'Maintenance': ['Low', 'Medium', 'High'],
            },
            'Furniture': {
                'Material': ['Wood', 'Metal', 'Plastic', 'Glass', 'Fabric', 'Rattan', 'Bamboo'],
                'Color': ['Black', 'White', 'Brown', 'Grey', 'Blue', 'Natural', 'Beige'],
                'Style': ['Modern', 'Traditional', 'Rustic', 'Contemporary', 'Industrial', 'Scandinavian'],
                'Dimensions': ['Small', 'Medium', 'Large', 'Extra Large'],
                'Assembly Required': ['Yes', 'No'],
                'Upholstery': ['Fabric', 'Leather', 'Velvet', 'Microfiber', 'Vinyl'],
                'Frame Material': ['Hardwood', 'Plywood', 'Metal', 'Particle Board'],
                'Weight Capacity': ['100lbs', '200lbs', '300lbs', '500lbs+', '1000lbs+'],
                'Reclinable': ['Yes', 'No'],
                'Foldable': ['Yes', 'No'],
                'Finish': ['Matte', 'Glossy', 'Natural', 'Stained'],
                'Adjustable': ['Yes', 'No'],
                'Ergonomic': ['Yes', 'No'],
            },
            'Kitchen & Dining': {
                'Material': ['Stainless Steel', 'Ceramic', 'Glass', 'Plastic', 'Cast Iron', 'Porcelain', 'Silicone'],
                'Color': ['Silver', 'Black', 'White', 'Red', 'Blue', 'Green', 'Grey'],
                'Style': ['Modern', 'Traditional', 'Contemporary', 'Rustic'],
                'Capacity': ['Small', 'Medium', 'Large', 'Extra Large'],
                'Dishwasher Safe': ['Yes', 'No'],
                'Power Source': ['Electric', 'Manual', 'Battery'],
                'Heat Resistance': ['Up to 200°F', '400°F', '600°F+', 'Oven-Safe'],
                'Non-Stick': ['Yes', 'No'],
                'Set Includes': ['Single Item', '2-Piece', '4-Piece', '6-Piece+', '8-Piece+'],
                'Handle Material': ['Plastic', 'Wood', 'Stainless Steel', 'Silicone'],
                'Microwave Safe': ['Yes', 'No'],
                'Stackable': ['Yes', 'No'],
                'Blade Material': ['Stainless Steel', 'Ceramic', 'Carbon Steel'],
                'Cookware Type': ['Fry Pan', 'Saucepan', 'Dutch Oven', 'Bakeware'],
            },
            'Sporting Goods': {
                'Material': ['Aluminum', 'Carbon Fiber', 'Plastic', 'Rubber', 'Steel', 'Composite', 'Foam'],
                'Color': ['Black', 'White', 'Blue', 'Red', 'Green', 'Yellow', 'Grey'],
                'Type': ['Ball', 'Racket', 'Protective Gear', 'Fitness Equipment', 'Training Aid', 'Net'],
                'Size': ['Small', 'Medium', 'Large', 'Extra Large'],
                'Gender': ['Men', 'Women', 'Unisex', 'Kids'],
                'Sport Type': ['Basketball', 'Soccer', 'Tennis', 'Golf', 'Cycling', 'Baseball', 'Swimming'],
                'Durability': ['Standard', 'High-Impact', 'Weather-Resistant'],
                'Grip Type': ['Rubber', 'Foam', 'Leather', 'Synthetic'],
                'Age Group': ['Adult', 'Youth', 'Senior'],
                'Weight': ['Light', 'Medium', 'Heavy'],
                'Adjustable': ['Yes', 'No'],
                'Portability': ['Portable', 'Fixed'],
                'Surface Compatibility': ['Indoor', 'Outdoor', 'All Surfaces'],
            },
            'Outdoor Gear': {
                'Material': ['Nylon', 'Polyester', 'Aluminum', 'Plastic', 'Steel', 'Canvas', 'Gore-Tex'],
                'Color': ['Black', 'Green', 'Blue', 'Red', 'Grey', 'Brown', 'Camouflage'],
                'Type': ['Tent', 'Backpack', 'Sleeping Bag', 'Camping Stove', 'Cooler', 'Hammock', 'Lantern'],
                'Size': ['Small', 'Medium', 'Large', 'Extra Large'],
                'Weight': ['Ultralight', 'Light', 'Medium', 'Heavy'],
                'Water Resistance': ['Waterproof', 'Water-Resistant', 'Non-Waterproof'],
                'Temperature Rating': ['0°F', '20°F', '40°F+', '-20°F'],
                'Capacity': ['1-Person', '2-Person', '4-Person', '6-Person+', '8-Person+'],
                'Packability': ['Compact', 'Standard', 'Bulky'],
                'UV Protection': ['Yes', 'No'],
                'Ventilation': ['High', 'Medium', 'Low'],
                'Setup Time': ['Quick Setup', 'Standard', 'Complex'],
                'Fuel Type': ['Propane', 'Butane', 'Wood', 'Battery'],
                'Insulation Type': ['Synthetic', 'Down', 'None'],
            },
        }

        # Get or create categories
        categories = {}
        for cat_name in category_names:
            try:
                category = Category.objects.get(name=cat_name)
                categories[cat_name] = category
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Category "{cat_name}" not found. Please create it first.'))
                continue

        # Create Attributes and AttributeValues
        for cat_name, attributes in attribute_data.items():
            if cat_name not in categories:
                continue
            category = categories[cat_name]
            for attr_name, attr_values in attributes.items():
                # Create or get Attribute
                attribute, created = Attribute.objects.get_or_create(name=attr_name)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created attribute: {attr_name}'))
                
                # Create AttributeValues for the category
                for value in attr_values:
                    try:
                        attr_value, created = AttributeValue.objects.get_or_create(
                            attribute=attribute,
                            category=category,
                            value=value
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Created attribute value: {attr_name}: {value} for category {cat_name}'))
                    except IntegrityError:
                        self.stdout.write(self.style.WARNING(f'Attribute value {attr_name}: {value} for category {cat_name} already exists.'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error creating attribute value {attr_name}: {value} for category {cat_name}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Command completed successfully.'))