from rest_framework import viewsets, status, permissions, mixins, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.conf import settings
import os
from .models import Property, PropertyType, PropertyImage, Video
from .serializers import (
    PropertySerializer, 
    PropertyTypeSerializer,
    PropertyImageSerializer,
    VideoSerializer
)
from .tasks import process_video_task

class PropertyTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None

class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = Property.objects.select_related(
            'owner', 'property_type'
        ).prefetch_related(
            'images', 'videos'
        )
        
        if self.request.user.is_authenticated:
            if self.action == 'list':
                return queryset.filter(owner=self.request.user)
        else:
            return queryset.filter(is_available=True)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_images(self, request, slug=None):
        property = self.get_object()
        images = request.FILES.getlist('images')
        
        if not images:
            return Response(
                {"error": "No images provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_instances = []
        has_primary = PropertyImage.objects.filter(
            property=property, 
            is_primary=True
        ).exists()
        
        for image in images:
            image_instance = PropertyImage(
                property=property,
                image=image,
                is_primary=(not has_primary and not image_instances)
            )
            image_instance.save()
            image_instances.append(image_instance)
            has_primary = True
        
        serializer = PropertyImageSerializer(image_instances, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def set_primary_image(self, request, slug=None):
        property = self.get_object()
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response(
                {"error": "image_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            image = PropertyImage.objects.get(id=image_id, property=property)
            image.is_primary = True
            image.save()
            return Response(
                {"message": "Primary image set successfully"},
                status=status.HTTP_200_OK
            )
        except PropertyImage.DoesNotExist:
            return Response(
                {"error": "Image not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class PropertyImageViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = PropertyImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PropertyImage.objects.filter(
            property__slug=self.kwargs['property_slug'],
            property__owner=self.request.user
        ).order_by('-is_primary', 'created_at')
    
    def perform_create(self, serializer):
        property = get_object_or_404(
            Property,
            slug=self.kwargs['property_slug'],
            owner=self.request.user
        )
        has_primary = PropertyImage.objects.filter(
            property=property,
            is_primary=True
        ).exists()
        
        serializer.save(
            property=property,
            is_primary=not has_primary
        )

class VideoViewSet(viewsets.ModelViewSet):
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Video.objects.select_related('property', 'property__owner')
        
        if self.request.user.is_authenticated:
            if 'property_slug' in self.kwargs:
                return queryset.filter(
                    property__slug=self.kwargs['property_slug'],
                    property__owner=self.request.user
                )
            return queryset.filter(property__owner=self.request.user)
        
        return queryset.filter(
            property__is_available=True,
            status=Video.COMPLETED
        )
    
    def perform_create(self, serializer):
        if 'property_slug' in self.kwargs:
            property = get_object_or_404(
                Property,
                slug=self.kwargs['property_slug'],
                owner=self.request.user
            )
            video = serializer.save(property=property)
            # Trigger async video processing
            process_video_task.delay(video.id)
        else:
            raise serializers.ValidationError("Property slug is required")
    
    @action(detail=True, methods=['get'])
    def hls_playlist(self, request, pk=None):
        video = self.get_object()
        
        if not video.hls_playlist:
            return Response(
                {"error": "HLS playlist not available"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        hls_playlist_path = os.path.join(settings.MEDIA_ROOT, video.hls_playlist)
        
        if not os.path.exists(hls_playlist_path):
            return Response(
                {"error": "HLS playlist file not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            with open(hls_playlist_path, 'r') as m3u8_file:
                m3u8_content = m3u8_file.read()
            
            base_url = request.build_absolute_uri('/')[:-1]
            m3u8_content = m3u8_content.replace(
                '{{ dynamic_path }}', 
                f"{base_url}{reverse('video-hls-segment', kwargs={'pk': video.pk})}/"
            )
            
            return Response(
                m3u8_content,
                content_type='application/vnd.apple.mpegurl'
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='hls_segment/(?P<segment_name>[^/.]+)')
    def hls_segment(self, request, pk=None, segment_name=None):
        video = self.get_object()
        
        if not video.hls_playlist:
            raise Http404("HLS playlist not available")
        
        hls_directory = os.path.dirname(os.path.join(settings.MEDIA_ROOT, video.hls_playlist))
        segment_path = os.path.join(hls_directory, segment_name)
        
        if not os.path.exists(segment_path):
            raise Http404("HLS segment not found")
        
        return FileResponse(
            open(segment_path, 'rb'),
            content_type='video/mp2t'
        )