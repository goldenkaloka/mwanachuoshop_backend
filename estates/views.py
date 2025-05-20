import os
from django.http import FileResponse, Http404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django.shortcuts import get_object_or_404
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
import logging

from estates.models import Property, PropertyImage, PropertyType
from estates.serializers import PropertyImageSerializer, PropertySerializer, PropertyTypeSerializer
from estates.pagination import InfiniteScrollPagination

logger = logging.getLogger(__name__)

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user.is_staff
        elif hasattr(obj, 'property'):
            return obj.property.owner == request.user or request.user.is_staff
        return False

class PropertyTypeViewSet(viewsets.ModelViewSet):
    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer
    pagination_class = None
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    pagination_class = InfiniteScrollPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_available', 'property_type', 'video_status']
    search_fields = ['title', 'location']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'serve_hls_playlist', 'serve_hls_segment']:
            return [permissions.AllowAny()]
        elif self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        my_properties = self.request.query_params.get('my_properties', 'false').lower() == 'true'
        has_video = self.request.query_params.get('has_video', 'false').lower() == 'true'
        
        if my_properties:
            if not self.request.user.is_authenticated:
                raise permissions.PermissionDenied("Authentication required for user-specific properties.")
            queryset = queryset.filter(owner=self.request.user)
        elif not self.request.user.is_staff:
            queryset = queryset.filter(is_available=True)
            
        if has_video:
            queryset = queryset.exclude(video__isnull=True).filter(video_status='Completed')
            
        return queryset.select_related('owner', 'property_type').prefetch_related('images')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        response_serializer = self.get_serializer(instance, context={'exclude_images': True})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['exclude_images'] = self.request.query_params.get('exclude_images', 'false').lower() == 'true'
        return context

    @action(detail=True, methods=['get'], url_path='playlist', url_name='property-playlist')
    def serve_hls_playlist(self, request, pk=None):
        logger.info(f"Attempting to serve HLS playlist for Property ID (pk): {pk}")
        try:
            property_instance = get_object_or_404(Property, pk=pk, video_status='Completed')
            logger.info(f"Property ID {pk} found with video_status='Completed'. Playlist path: {property_instance.hls_playlist}")
        except Http404:
            logger.warning(f"Property ID {pk} not found or video_status not 'Completed' when requesting playlist.")
            return Response({"error": "Playlist not found or video processing not complete."}, status=status.HTTP_404_NOT_FOUND)

        try:
            if not property_instance.hls_playlist:
                logger.error(f"Property ID {pk} has no HLS playlist path defined.")
                return Response({"error": "HLS playlist path not configured for this property."}, status=status.HTTP_404_NOT_FOUND)

            hls_playlist_path = os.path.join(settings.MEDIA_ROOT, str(property_instance.hls_playlist))
            
            if not os.path.exists(hls_playlist_path):
                logger.error(f"HLS playlist file not found at {hls_playlist_path} for Property ID {pk}")
                return Response({"error": "HLS playlist file not found on server."}, status=status.HTTP_404_NOT_FOUND)

            logger.info(f"Serving HLS playlist for Property ID {pk} from {hls_playlist_path}")
            return FileResponse(open(hls_playlist_path, 'rb'), content_type='application/vnd.apple.mpegurl')
        
        except Exception as e:
            logger.error(f"Failed to serve HLS playlist for Property ID {pk}: {str(e)}", exc_info=True)
            return Response({"error": f"Internal server error serving playlist: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @action(detail=True, methods=['get'], url_path='segments/(?P<segment_name>[^/]+\.ts)$')
    def serve_hls_segment(self, request, pk=None, segment_name=None):
        logger.info(f"SEGMENT REQUEST: pk='{pk}', segment_name='{segment_name}'")

        try:
            property_instance = get_object_or_404(Property, pk=pk, video_status='Completed')
            logger.info(f"SEGMENT: Property ID {pk} (video_status='Completed') found for segment '{segment_name}'.")
        except Http404:
            logger.warning(f"SEGMENT: Property ID {pk} not found OR video_status not 'Completed' for segment '{segment_name}'. Responding with 404.")
            return Response({"error": "Segment not found or video processing not complete."}, status=status.HTTP_404_NOT_FOUND)

        try:
            if not property_instance.hls_playlist:
                logger.error(f"Property ID {pk} has no HLS playlist path defined, cannot determine segment directory.")
                return Response({"error": "HLS playlist path not configured, cannot serve segment."}, status=status.HTTP_404_NOT_FOUND)

            hls_directory = os.path.normpath(os.path.dirname(os.path.join(settings.MEDIA_ROOT, str(property_instance.hls_playlist))))
            segment_path = os.path.normpath(os.path.join(hls_directory, segment_name))
            
            logger.debug(f"SEGMENT: Attempting to serve segment. Property_ID={pk}, Segment_Name='{segment_name}', Full_Path='{segment_path}'")

            if not os.path.exists(segment_path):
                logger.error(f"SEGMENT: File not found at path '{segment_path}' for Property ID {pk}, segment '{segment_name}'.")
                return Response({"error": f"HLS segment content file not found at '{segment_path}'"}, status=status.HTTP_404_NOT_FOUND)
            
            if not os.access(segment_path, os.R_OK):
                logger.error(f"SEGMENT: File at '{segment_path}' is not readable for Property ID {pk}, segment '{segment_name}'.")
                return Response({"error": "Segment content not readable (permission issue)."}, status=status.HTTP_403_FORBIDDEN)

            logger.info(f"SEGMENT: Serving segment '{segment_name}' for Property ID {pk} from '{segment_path}'")
            return FileResponse(open(segment_path, 'rb'), content_type='video/mp2t')
        
        except FileNotFoundError:
            logger.error(f"SEGMENT: FileNotFoundError for Property ID {pk}, segment '{segment_name}'. Path: '{segment_path}'")
            return Response({"error": f"HLS segment content (FileNotFoundError) for '{segment_name}'"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"SEGMENT: Generic error serving segment for Property ID {pk}, segment '{segment_name}': {str(e)}", exc_info=True)
            return Response({"error": f"Failed to serve HLS segment: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropertyImageViewSet(viewsets.ModelViewSet):
    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageSerializer
    pagination_class = InfiniteScrollPagination
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def perform_create(self, serializer):
        property_instance = serializer.validated_data['property']
        if property_instance.owner != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only add images to your own properties.")
        serializer.save()

    def get_queryset(self):
        return super().get_queryset().select_related('property')