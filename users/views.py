from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from .models import Profile
from .serializers import CustomRegisterSerializer, CustomUserDetailsSerializer, ProfileSerializer
from dj_rest_auth.views import UserDetailsView
from dj_rest_auth.registration.views import RegisterView
from django.middleware.csrf import get_token
from rest_framework.views import APIView
from rest_framework.response import Response




class CustomRegisterView(RegisterView):
    serializer_class = CustomRegisterSerializer

class CustomUserDetailsView(UserDetailsView):
    serializer_class = CustomUserDetailsSerializer

class ProfileView(RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
    

class CSRFView(APIView):
    def get(self, request):
        return Response({'csrfToken': get_token(request)})