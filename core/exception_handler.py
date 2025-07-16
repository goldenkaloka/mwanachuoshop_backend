from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
import traceback
from django.conf import settings

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF to standardize error responses.
    """
    response = drf_exception_handler(exc, context)
    logger = logging.getLogger(__name__)

    if response is not None:
        # Standardize DRF error response
        data = {
            'success': False,
            'error': response.data.get('detail') or response.data,
            'code': response.status_code,
        }
        if settings.DEBUG:
            data['details'] = response.data
        response.data = data
        return response
    else:
        # Handle non-DRF exceptions
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        data = {
            'success': False,
            'error': str(exc),
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
        if settings.DEBUG:
            data['details'] = traceback.format_exc()
        return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
from rest_framework.response import Response
from rest_framework import status
import logging
import traceback
from django.conf import settings

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF to standardize error responses.
    """
    response = drf_exception_handler(exc, context)
    logger = logging.getLogger(__name__)

    if response is not None:
        # Standardize DRF error response
        data = {
            'success': False,
            'error': response.data.get('detail') or response.data,
            'code': response.status_code,
        }
        if settings.DEBUG:
            data['details'] = response.data
        response.data = data
        return response
    else:
        # Handle non-DRF exceptions
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        data = {
            'success': False,
            'error': str(exc),
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
        if settings.DEBUG:
            data['details'] = traceback.format_exc()
        return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 