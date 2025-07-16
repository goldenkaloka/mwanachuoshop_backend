from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class SmartContentPagination(PageNumberPagination):
    """Optimized pagination for smart content filtering"""
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
        })

class UniversityPagination(PageNumberPagination):
    """Optimized pagination for university listings"""
    page_size = 50
    page_size_query_param = 'limit'
    max_page_size = 200

class CampusPagination(PageNumberPagination):
    """Optimized pagination for campus listings"""
    page_size = 30
    page_size_query_param = 'limit'
    max_page_size = 100

class LocationPagination(PageNumberPagination):
    """Optimized pagination for location-based content"""
    page_size = 25
    page_size_query_param = 'limit'
    max_page_size = 150 