"""
User service for handling user-related operations.
"""
import logging
from typing import List, Dict, Any, Optional
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.core.cache import cache

from core.models import University, Campus

User = get_user_model()
logger = logging.getLogger(__name__)


class UserService:
    """Service for handling user-related operations."""

    CACHE_TIMEOUT = 1800  # 30 minutes

    @staticmethod
    def get_users_by_university(
        university_id: int,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get users for a specific university with optional search."""
        cache_key = f'users_university_{university_id}_{search}_{page}_{page_size}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        try:
            university = University.objects.get(id=university_id, is_active=True)
        except University.DoesNotExist:
            return {
                'university': None,
                'users': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size
            }

        users = User.objects.filter(
            university=university,
            is_active=True
        ).select_related('university', 'specific_location', 'profile')

        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(phonenumber__icontains=search)
            )

        total_count = users.count()
        start = (page - 1) * page_size
        end = start + page_size
        users_page = users[start:end]

        result = {
            'university': {
                'id': university.id,
                'name': university.name,
                'short_name': university.short_name
            },
            'users': [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'phonenumber': user.phonenumber,
                    'university': user.university.name if user.university else None,
                    'campus': user.specific_location.name if user.specific_location else None,
                    'profile_image': user.profile.image.url if user.profile and user.profile.image else None,
                    'start_date': user.start_date,
                    'is_active': user.is_active,
                }
                for user in users_page
            ],
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
        }

        cache.set(cache_key, result, UserService.CACHE_TIMEOUT)
        return result

    @staticmethod
    def search_users(
        query: str,
        location: Optional[str] = None,
        university_id: Optional[int] = None,
        campus_id: Optional[int] = None,
        sort_by: str = 'relevance'
    ) -> List[Dict[str, Any]]:
        """Search users with advanced filtering."""
        queryset = User.objects.filter(is_active=True)
        used_rank = False

        if query:
            # Clean the query to remove special characters
            clean_query = query.replace('@', '').replace('#', '').replace('$', '').replace('%', '').replace('^', '').replace('&', '').replace('*', '').replace('(', '').replace(')', '').replace('-', '').replace('+', '').replace('=', '').replace('[', '').replace(']', '').replace('{', '').replace('}', '').replace('|', '').replace('\\', '').replace(':', '').replace(';', '').replace('"', '').replace("'", '').replace('<', '').replace('>', '').replace(',', '').replace('.', '').replace('?', '').replace('/', '')
            
            if clean_query.strip():
                try:
                    from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
                    from django.db import connection
                    
                    if 'postgresql' in connection.vendor:
                        search_vector = SearchVector('username', weight='A') + SearchVector('email', weight='B')
                        search_query = SearchQuery(clean_query)
                        queryset = queryset.annotate(
                            search=search_vector,
                            rank=SearchRank(search_vector, search_query)
                        ).filter(search=search_query)
                        used_rank = True
                    else:
                        queryset = queryset.filter(
                            Q(username__icontains=query) | Q(email__icontains=query)
                        )
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {e}")
                    queryset = queryset.filter(
                        Q(username__icontains=query) | Q(email__icontains=query)
                    )
            else:
                queryset = queryset.filter(
                    Q(username__icontains=query) | Q(email__icontains=query)
                )

        # Apply filters
        if location:
            queryset = queryset.filter(
                Q(university__name__icontains=location) |
                Q(specific_location__name__icontains=location)
            )
        if university_id:
            queryset = queryset.filter(university_id=university_id)
        if campus_id:
            queryset = queryset.filter(specific_location_id=campus_id)

        # Apply sorting
        if sort_by == 'newest':
            queryset = queryset.order_by('-start_date')
        else:  # relevance
            if used_rank:
                queryset = queryset.order_by('-rank', '-start_date')
            else:
                queryset = queryset.order_by('-start_date')

        # Convert to dict
        users = []
        for user in queryset[:50]:
            users.append({
                'id': user.id,
                'type': 'user',
                'title': user.username,
                'description': user.email,
                'image': user.profile.image.url if user.profile and user.profile.image else None,
                'location': user.university.name if user.university else None,
                'university': user.university.name if user.university else None,
                'campus': user.specific_location.name if user.specific_location else None,
                'created_at': user.start_date,
                'relevance_score': getattr(user, 'rank', 0.5),
                'url': f'/users/{user.id}'
            })

        return users

    @staticmethod
    def get_user_statistics() -> Dict[str, Any]:
        """Get user statistics across universities."""
        cache_key = 'user_statistics'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        # Get university counts
        university_counts = University.objects.filter(
            is_active=True
        ).annotate(
            user_count=Count('newuser', filter=Q(newuser__is_active=True))
        ).values('id', 'name', 'short_name', 'user_count')

        total_users = User.objects.filter(is_active=True).count()

        result = {
            'university_counts': [
                {
                    'university': {
                        'id': uni['id'],
                        'name': uni['name'],
                        'short_name': uni['short_name']
                    },
                    'user_count': uni['user_count']
                }
                for uni in university_counts
            ],
            'total_users': total_users
        }

        cache.set(cache_key, result, UserService.CACHE_TIMEOUT)
        return result

    @staticmethod
    def update_user_university(
        user_id: int,
        university_id: int,
        campus_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update user's university association."""
        try:
            user = User.objects.get(id=user_id)
            university = University.objects.get(id=university_id, is_active=True)
            
            user.university = university
            
            if campus_id:
                try:
                    campus = Campus.objects.get(id=campus_id, university=university)
                    user.specific_location = campus
                except Campus.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Invalid campus ID for the selected university'
                    }
            else:
                user.specific_location = None
            
            user.save()
            
            # Clear related cache
            UserService.clear_user_cache()
            
            return {
                'success': True,
                'message': f'User university updated to {university.name}',
                'university': {
                    'id': university.id,
                    'name': university.name,
                    'short_name': university.short_name
                }
            }
            
        except User.DoesNotExist:
            return {
                'success': False,
                'error': 'User not found'
            }
        except University.DoesNotExist:
            return {
                'success': False,
                'error': 'University not found'
            }

    @staticmethod
    def clear_user_cache():
        """Clear all user-related cache."""
        cache_keys = [
            'user_statistics',
            'users_university_*',
        ]
        
        for key in cache_keys:
            if '*' in key:
                continue
            cache.delete(key)
        
        logger.info("User cache cleared") 