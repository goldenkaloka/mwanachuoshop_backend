from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers
from .models import NewUser, Profile

class CustomRegisterSerializer(RegisterSerializer):
    phonenumber = serializers.CharField(required=True)
    
    def validate(self, data):
        if not data.get('phonenumber'):
            raise serializers.ValidationError("Phone number is required")
        return super().validate(data)
    
    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'phonenumber': self.validated_data.get('phonenumber', '')
        }

class CustomUserDetailsSerializer(UserDetailsSerializer):
    profile_id = serializers.IntegerField(source='profile.id', read_only=True)
    whatsapp = serializers.CharField(source='profile.whatsapp', read_only=True)
    
    class Meta(UserDetailsSerializer.Meta):
        model = NewUser
        fields = UserDetailsSerializer.Meta.fields + (
            'phonenumber',
            'profile_id',
            'whatsapp',
        )
        read_only_fields = ('email', 'username')

class ProfileSerializer(serializers.ModelSerializer):
    user = CustomUserDetailsSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ('user', )
        
    def update(self, instance, validated_data):
        # Handle image upload separately if needed
        return super().update(instance, validated_data)