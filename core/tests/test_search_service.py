"""
Tests for the search service functionality.
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from core.services.search_service import SearchService
from core.models import University, Campus
from marketplace.models import Product, Category
from estates.models import Property, PropertyType

User = get_user_model()


class SearchServiceTestCase(TestCase):
    """Test cases for SearchService."""

    def setUp(self):
        """Set up test data."""
        # Create test university
        self.university = University.objects.create(
            name="Test University",
            short_name="TU",
            is_active=True
        )
        
        # Create test campus
        self.campus = Campus.objects.create(
            name="Main Campus",
            university=self.university,
            is_active=True
        )
        
        # Create test category
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic items"
        )
        
        # Create test property type
        self.property_type = PropertyType.objects.create(
            name="Apartment",
            description="Apartment properties"
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name="Laptop",
            description="High-performance laptop",
            price=1000.00,
            category=self.category,
            university=self.university,
            campus=self.campus,
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name="Phone",
            description="Smartphone",
            price=500.00,
            category=self.category,
            university=self.university,
            campus=self.campus,
            is_active=True
        )
        
        # Create test properties
        self.property1 = Property.objects.create(
            title="Modern Apartment",
            features="2 bedrooms, kitchen, living room",
            price=2000.00,
            property_type=self.property_type,
            university=self.university,
            campus=self.campus,
            is_available=True
        )

    def test_clean_query(self):
        """Test query cleaning functionality."""
        # Test with special characters
        dirty_query = "test@#$%^&*()query"
        clean_query = SearchService.clean_query(dirty_query)
        self.assertEqual(clean_query, "testquery")
        
        # Test with spaces
        spaced_query = "  test query  "
        clean_query = SearchService.clean_query(spaced_query)
        self.assertEqual(clean_query, "test query")

    def test_is_postgres(self):
        """Test PostgreSQL detection."""
        # This test will depend on the actual database being used
        result = SearchService.is_postgres()
        self.assertIsInstance(result, bool)

    def test_search_products_basic(self):
        """Test basic product search functionality."""
        results = SearchService.search_products("laptop")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Laptop")
        self.assertEqual(results[0]['type'], "product")

    def test_search_products_with_filters(self):
        """Test product search with filters."""
        results = SearchService.search_products(
            query="laptop",
            category="Electronics",
            price_min=500,
            price_max=1500
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Laptop")

    def test_search_products_no_results(self):
        """Test product search with no matching results."""
        results = SearchService.search_products("nonexistent")
        self.assertEqual(len(results), 0)

    def test_search_estates_basic(self):
        """Test basic estate search functionality."""
        results = SearchService.search_estates("apartment")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Modern Apartment")
        self.assertEqual(results[0]['type'], "estate")

    def test_search_estates_with_filters(self):
        """Test estate search with filters."""
        results = SearchService.search_estates(
            query="apartment",
            category="Apartment",
            price_min=1000,
            price_max=3000
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Modern Apartment")

    def test_unified_search_basic(self):
        """Test basic unified search functionality."""
        results = SearchService.unified_search(
            query="laptop",
            content_types=['products']
        )
        
        self.assertEqual(results['total_results'], 1)
        self.assertEqual(len(results['results']), 1)
        self.assertEqual(results['results'][0]['title'], "Laptop")

    def test_unified_search_multiple_types(self):
        """Test unified search across multiple content types."""
        results = SearchService.unified_search(
            query="",
            content_types=['products', 'estates']
        )
        
        # Should return both products and estates
        self.assertGreaterEqual(results['total_results'], 2)

    def test_unified_search_pagination(self):
        """Test unified search pagination."""
        # Create more products for pagination test
        for i in range(25):
            Product.objects.create(
                name=f"Product {i}",
                description=f"Description {i}",
                price=100.00 + i,
                category=self.category,
                university=self.university,
                campus=self.campus,
                is_active=True
            )
        
        results = SearchService.unified_search(
            query="product",
            content_types=['products'],
            page=1,
            page_size=10
        )
        
        self.assertEqual(len(results['results']), 10)
        self.assertEqual(results['pagination']['page'], 1)
        self.assertEqual(results['pagination']['page_size'], 10)
        self.assertTrue(results['pagination']['has_next'])

    def test_unified_search_invalid_params(self):
        """Test unified search with invalid parameters."""
        with self.assertRaises(ValueError):
            SearchService.unified_search(
                query="",
                content_types=['products']
            )

    def test_apply_sorting_price_low(self):
        """Test sorting by price low."""
        queryset = Product.objects.all()
        sorted_qs = SearchService._apply_sorting(queryset, 'price_low', False, 'created_at')
        self.assertEqual(sorted_qs.first().price, 500.00)

    def test_apply_sorting_price_high(self):
        """Test sorting by price high."""
        queryset = Product.objects.all()
        sorted_qs = SearchService._apply_sorting(queryset, 'price_high', False, 'created_at')
        self.assertEqual(sorted_qs.first().price, 1000.00)

    def test_apply_sorting_newest(self):
        """Test sorting by newest."""
        queryset = Product.objects.all()
        sorted_qs = SearchService._apply_sorting(queryset, 'newest', False, 'created_at')
        # Should be ordered by created_at descending
        self.assertIsNotNone(sorted_qs)

    def test_sort_combined_results(self):
        """Test sorting combined results."""
        results = [
            {'title': 'A', 'relevance_score': 0.5, 'price': 100},
            {'title': 'B', 'relevance_score': 0.8, 'price': 200},
            {'title': 'C', 'relevance_score': 0.3, 'price': 50},
        ]
        
        # Test relevance sorting
        sorted_results = SearchService._sort_combined_results(results, 'relevance')
        self.assertEqual(sorted_results[0]['title'], 'B')  # Highest relevance
        
        # Test price low sorting
        sorted_results = SearchService._sort_combined_results(results, 'price_low')
        self.assertEqual(sorted_results[0]['price'], 50)  # Lowest price
        
        # Test price high sorting
        sorted_results = SearchService._sort_combined_results(results, 'price_high')
        self.assertEqual(sorted_results[0]['price'], 200)  # Highest price


@pytest.mark.django_db
class SearchServiceIntegrationTestCase(TestCase):
    """Integration tests for SearchService."""

    def setUp(self):
        """Set up integration test data."""
        # Create comprehensive test data
        self.university = University.objects.create(
            name="Integration Test University",
            short_name="ITU",
            is_active=True
        )
        
        self.campus = Campus.objects.create(
            name="Test Campus",
            university=self.university,
            is_active=True
        )
        
        self.category = Category.objects.create(
            name="Books",
            description="Educational books"
        )
        
        # Create multiple products
        self.products = []
        for i in range(10):
            product = Product.objects.create(
                name=f"Book {i}",
                description=f"Educational book {i}",
                price=50.00 + (i * 10),
                category=self.category,
                university=self.university,
                campus=self.campus,
                is_active=True
            )
            self.products.append(product)

    def test_search_integration(self):
        """Test complete search integration."""
        # Test search with various parameters
        results = SearchService.unified_search(
            query="book",
            content_types=['products'],
            price_min=60,
            price_max=100,
            sort_by='price_low'
        )
        
        # Should return products with prices between 60 and 100
        self.assertGreater(results['total_results'], 0)
        for result in results['results']:
            self.assertGreaterEqual(result['price'], 60)
            self.assertLessEqual(result['price'], 100)

    def test_search_performance(self):
        """Test search performance with larger datasets."""
        # Create more data for performance testing
        for i in range(100):
            Product.objects.create(
                name=f"Performance Test Product {i}",
                description=f"Description {i}",
                price=100.00 + i,
                category=self.category,
                university=self.university,
                campus=self.campus,
                is_active=True
            )
        
        # Test search performance
        import time
        start_time = time.time()
        
        results = SearchService.unified_search(
            query="performance",
            content_types=['products'],
            page_size=50
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(execution_time, 1.0)  # Less than 1 second
        self.assertEqual(len(results['results']), 50) 