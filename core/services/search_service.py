"""
Search service for handling unified search functionality.
"""
import logging
from typing import List, Dict, Any, Optional
from django.db.models import Q, Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db import connection

logger = logging.getLogger(__name__)


class SearchService:
    """Service for handling search operations across all content types."""

    @staticmethod
    def is_postgres() -> bool:
        """Check if the database is PostgreSQL."""
        return 'postgresql' in connection.vendor

    @staticmethod
    def clean_query(query: str) -> str:
        """Clean search query by removing special characters."""
        special_chars = '@#$%^&*()+-=[]{}|\\:;"\'<>?,./'
        for char in special_chars:
            query = query.replace(char, '')
        return query.strip()

    @staticmethod
    def search_products(
        query: str,
        category: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        location: Optional[str] = None,
        university_id: Optional[int] = None,
        campus_id: Optional[int] = None,
        sort_by: str = 'relevance'
    ) -> List[Dict[str, Any]]:
        """Search products with advanced filtering."""
        from marketplace.models import Product

        queryset = Product.objects.filter(is_active=True)
        used_rank = False

        if query:
            clean_query = SearchService.clean_query(query)
            if clean_query and SearchService.is_postgres():
                try:
                    search_vector = SearchVector('name', weight='A') + SearchVector('description', weight='B')
                    search_query = SearchQuery(clean_query)
                    queryset = queryset.annotate(
                        search=search_vector,
                        rank=SearchRank(search_vector, search_query)
                    ).filter(search=search_query)
                    used_rank = True
                except Exception as e:
                    logger.warning(f"PostgreSQL search failed for query '{query}': {e}")
                    queryset = queryset.filter(
                        Q(name__icontains=query) | Q(description__icontains=query)
                    )
            else:
                queryset = queryset.filter(
                    Q(name__icontains=query) | Q(description__icontains=query)
                )

        # Apply filters
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        if location:
            queryset = queryset.filter(
                Q(university__name__icontains=location) |
                Q(campus__name__icontains=location) |
                Q(specific_location__name__icontains=location)
            )
        if university_id:
            queryset = queryset.filter(university_id=university_id)
        if campus_id:
            queryset = queryset.filter(campus_id=campus_id)

        # Apply sorting
        queryset = SearchService._apply_sorting(queryset, sort_by, used_rank, 'created_at')

        # Convert to dict
        products = []
        for product in queryset[:50]:
            products.append({
                'id': product.id,
                'type': 'product',
                'title': product.name,
                'description': product.description,
                'price': float(product.price),
                'image': product.images.first().image.url if product.images.exists() else None,
                'category': product.category.name if product.category else None,
                'location': product.get_location_context(),
                'university': product.university.name if product.university else None,
                'campus': product.campus.name if product.campus else None,
                'created_at': product.created_at,
                'relevance_score': getattr(product, 'rank', 0.5),
                'url': f'/products/{product.id}'
            })

        return products

    @staticmethod
    def search_estates(
        query: str,
        category: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        location: Optional[str] = None,
        university_id: Optional[int] = None,
        campus_id: Optional[int] = None,
        sort_by: str = 'relevance'
    ) -> List[Dict[str, Any]]:
        """Search estates/properties with advanced filtering."""
        from estates.models import Property

        queryset = Property.objects.filter(is_available=True)
        used_rank = False

        if query:
            clean_query = SearchService.clean_query(query)
            if clean_query and SearchService.is_postgres():
                try:
                    search_vector = SearchVector('title', weight='A') + SearchVector('features', weight='B')
                    search_query = SearchQuery(clean_query)
                    queryset = queryset.annotate(
                        search=search_vector,
                        rank=SearchRank(search_vector, search_query)
                    ).filter(search=search_query)
                    used_rank = True
                except Exception as e:
                    logger.warning(f"PostgreSQL search failed for query '{query}': {e}")
                    queryset = queryset.filter(
                        Q(title__icontains=query) | Q(features__icontains=query)
                    )
            else:
                queryset = queryset.filter(
                    Q(title__icontains=query) | Q(features__icontains=query)
                )

        # Apply filters
        if category:
            queryset = queryset.filter(property_type__name__icontains=category)
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        if location:
            queryset = queryset.filter(
                Q(location__icontains=location) |
                Q(university__name__icontains=location) |
                Q(campus__name__icontains=location)
            )
        if university_id:
            queryset = queryset.filter(university_id=university_id)
        if campus_id:
            queryset = queryset.filter(campus_id=campus_id)

        # Apply sorting
        queryset = SearchService._apply_sorting(queryset, sort_by, used_rank, 'created_at')

        # Convert to dict
        estates = []
        for estate in queryset[:50]:
            estates.append({
                'id': estate.id,
                'type': 'estate',
                'title': estate.title,
                'description': estate.features,
                'price': float(estate.price),
                'image': estate.images.first().image.url if estate.images.exists() else None,
                'category': estate.property_type.name if estate.property_type else None,
                'location': estate.location,
                'university': estate.university.name if estate.university else None,
                'campus': estate.campus.name if estate.campus else None,
                'created_at': estate.created_at,
                'relevance_score': getattr(estate, 'rank', 0.5),
                'url': f'/estates/{estate.id}'
            })

        return estates

    @staticmethod
    def _apply_sorting(queryset, sort_by: str, used_rank: bool, default_field: str) -> Any:
        """Apply sorting to queryset based on sort_by parameter."""
        if sort_by == 'price_low':
            return queryset.order_by('price')
        elif sort_by == 'price_high':
            return queryset.order_by('-price')
        elif sort_by == 'newest':
            return queryset.order_by(f'-{default_field}')
        elif sort_by == 'popular':
            return queryset.annotate(view_count=Count('whatsapp_clicks')).order_by('-view_count')
        else:  # relevance
            if used_rank:
                return queryset.order_by('-rank', f'-{default_field}')
            else:
                return queryset.order_by(f'-{default_field}')

    @staticmethod
    def unified_search(
        query: str = '',
        content_types: List[str] = None,
        category: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        location: Optional[str] = None,
        university_id: Optional[int] = None,
        campus_id: Optional[int] = None,
        sort_by: str = 'relevance',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Perform unified search across all content types."""
        if content_types is None:
            content_types = ['products', 'estates', 'shops', 'services', 'users']

        if not query and not category and not location:
            raise ValueError('At least one search parameter (query, category, or location) is required')

        results = {
            'query': query,
            'filters': {
                'content_types': content_types,
                'category': category,
                'price_range': {'min': price_min, 'max': price_max},
                'location': location,
                'university_id': university_id,
                'campus_id': campus_id
            },
            'total_results': 0,
            'results': [],
            'facets': {
                'categories': [],
                'price_ranges': [],
                'locations': [],
                'universities': []
            }
        }

        # Search across different content types
        if 'products' in content_types:
            products = SearchService.search_products(
                query, category, price_min, price_max, location, university_id, campus_id, sort_by
            )
            results['results'].extend(products)

        if 'estates' in content_types:
            estates = SearchService.search_estates(
                query, category, price_min, price_max, location, university_id, campus_id, sort_by
            )
            results['results'].extend(estates)

        # Add other content types as needed...

        # Sort combined results
        results['results'] = SearchService._sort_combined_results(results['results'], sort_by)

        # Pagination
        total_count = len(results['results'])
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        results['results'] = results['results'][start_idx:end_idx]

        results['total_results'] = total_count
        results['pagination'] = {
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'has_next': end_idx < total_count,
            'has_previous': page > 1
        }

        return results

    @staticmethod
    def _sort_combined_results(results: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """Sort combined results from different content types."""
        if sort_by == 'relevance':
            return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
        elif sort_by == 'newest':
            return sorted(results, key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == 'price_low':
            return sorted(results, key=lambda x: x.get('price', 0))
        elif sort_by == 'price_high':
            return sorted(results, key=lambda x: x.get('price', 0), reverse=True)
        else:
            return results 