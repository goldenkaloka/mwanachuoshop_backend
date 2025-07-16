from django.core.management.base import BaseCommand
from django.db.models import F
from django.contrib.postgres.search import SearchVector
from marketplace.models import Product

class Command(BaseCommand):
    help = "Rebuilds the search index for products"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Rebuilding product search index...'))
        
        # This approach uses an F expression for a more efficient bulk update.
        # It directly updates the search_vector field for all products in the database.
        Product.objects.update(
            search_vector=(
                SearchVector('name', weight='A') +
                SearchVector('description', weight='B')
            )
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully rebuilt product search index.'))
        self.stdout.write(self.style.WARNING('Consider running this periodically (e.g., via Django Q) to keep the index up-to-date.'))