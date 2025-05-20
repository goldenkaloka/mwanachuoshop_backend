# estates/pagination.py
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

class InfiniteScrollPagination(CursorPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'  # Default ordering for cursor pagination

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })