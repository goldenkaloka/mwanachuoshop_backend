from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers
from .models import NewUser, Profile

class CustomRegisterSerializer(RegisterSerializer):
    firstname = serializers.CharField(max_length=150, required=True)
    phonenumber = serializers.CharField(required=True)
    
    def validate(self, data):
        # Add any custom validation here
        if not data.get('firstname'):
            raise serializers.ValidationError("First name is required")
        if not data.get('phonenumber'):
            raise serializers.ValidationError("Phone number is required")
        return super().validate(data)
    
    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'first_name': self.validated_data.get('firstname', ''),  # Note: first_name vs firstname
            'phonenumber': self.validated_data.get('phonenumber', '')
        }

class CustomUserDetailsSerializer(UserDetailsSerializer):
    profile_id = serializers.IntegerField(source='profile.id', read_only=True)
    has_shop = serializers.BooleanField(source='profile.has_shop', read_only=True)
    whatsapp = serializers.CharField(source='profile.whatsapp', read_only=True)
    
    class Meta(UserDetailsSerializer.Meta):
        model = NewUser
        fields = UserDetailsSerializer.Meta.fields + (
            'firstname',
            'phonenumber',
            'profile_id',
            'has_shop',
            'whatsapp',
            'free_product_limit',
            'products_posted',
        )
        read_only_fields = ('email', 'username', 'free_product_limit', 'products_posted')

class ProfileSerializer(serializers.ModelSerializer):
    user = CustomUserDetailsSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ('user', 'whatsapp_verified', 'whatsapp_last_verified', 
                           'whatsapp_verification_attempts')
        
    def update(self, instance, validated_data):
        # Handle image upload separately if needed
        return super().update(instance, validated_data)