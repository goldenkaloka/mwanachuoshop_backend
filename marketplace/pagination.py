from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

class InfiniteScrollCursorPagination(CursorPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'  # Must match the ordering in the view

    def paginate_queryset(self, queryset, request, view=None):
        logger.info(f"Paginating queryset type: {type(queryset)}")
        page = super().paginate_queryset(queryset, request, view)
        logger.info(f"Page type after pagination: {type(page)}")
        return page

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })