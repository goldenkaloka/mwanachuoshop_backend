from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
import logging

from .models import NewUser, Profile
from .serializers import CustomUserDetailsSerializer, ProfileSerializer, CustomRegisterSerializer
from core.models import University, Campus
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from users.serializers import PublicUserSerializer

logger = logging.getLogger(__name__)
User = get_user_model()

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFView(APIView):
    """View to get CSRF token"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return JsonResponse({'csrfToken': get_token(request)})

class CSRFResponseSerializer(serializers.Serializer):
    csrfToken = serializers.CharField()

@extend_schema(
    responses={200: CSRFResponseSerializer},
    description="Get CSRF token."
)
class CSRFView(APIView):
    """View to get CSRF token"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return JsonResponse({'csrfToken': get_token(request)})

class CustomRegisterView(CreateAPIView):
    """Custom registration view with location fields"""
    permission_classes = [AllowAny]
    serializer_class = CustomRegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save(request)
        
        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        # Return profile info as well
        profile = user.profile
        return Response({
            'message': 'User registered successfully',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phonenumber': str(user.phonenumber),
                'campus': profile.campus.id if profile.campus else None,
            }
        }, status=status.HTTP_201_CREATED)

class ProfileView(RetrieveUpdateAPIView):
    """View for user profile management"""
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
    
    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for User model - authenticated access only"""
    queryset = User.objects.filter(is_active=True)
    serializer_class = CustomUserDetailsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter users by campus if specified"""
        queryset = super().get_queryset()
        campus_id = self.request.query_params.get('campus_id')
        if campus_id:
            queryset = queryset.filter(profile__campuses__id=campus_id)
        return queryset.select_related('profile').prefetch_related('profile__campuses')
    
    @extend_schema(
        responses={200: PublicUserSerializer(many=True)},
        description="Public user discovery endpoint with campus filtering."
    )
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public(self, request):
        """Public user discovery endpoint with campus filtering"""
        queryset = User.objects.filter(is_active=True)
        
        # Campus filtering
        campus_id = request.query_params.get('campus_id')
        if campus_id:
            queryset = queryset.filter(profile__campuses__id=campus_id)
        
        # University filtering through campus
        university_id = request.query_params.get('university_id')
        if university_id:
            pass  # No universities field on profile, so skip this filter
        
        # Search filtering
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Optimize queries
        queryset = queryset.select_related('profile').prefetch_related('profile__campuses')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        users_page = queryset[start:end]
        
        # Use public serializer that only exposes safe fields
        serializer = PublicUserSerializer(users_page, many=True, context={'request': request})
        
        return Response({
            'users': serializer.data,
            'total_count': queryset.count(),
            'page': page,
            'page_size': page_size,
            'filters': {
                'university_id': university_id,
                'campus_id': campus_id,
                'search': search
            }
        })

class CampusSuggestionResponseSerializer(serializers.Serializer):
    suggestions = serializers.ListField(child=serializers.CharField())

@extend_schema(
    responses={200: CampusSuggestionResponseSerializer},
    description="Get campus suggestions."
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_campus_suggestions(request):
    """Get campus suggestions for a specific university"""
    university_id = request.query_params.get('university_id')
    
    if not university_id:
        return Response({'error': 'university_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        university = get_object_or_404(University, id=university_id, is_active=True)
        campuses = Campus.objects.filter(university=university, is_active=True)
        
        return Response({
            'university': {
                'id': university.id,
                'name': university.name,
                'short_name': university.short_name
            },
            'campuses': [
                {
                    'id': campus.id,
                    'name': campus.name,
                    'address': campus.address,
                    'latitude': campus.latitude,
                    'longitude': campus.longitude
                } for campus in campuses
            ]
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting campus suggestions: {str(e)}")
        return Response({'error': 'Failed to get campus suggestions'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
