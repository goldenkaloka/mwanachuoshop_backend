from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from .models import NewUser, Profile
from allauth.socialaccount.models import SocialAccount
from phonenumber_field.serializerfields import PhoneNumberField

class CustomRegisterSerializer(RegisterSerializer):
    phonenumber = PhoneNumberField(region='TZ', required=False)  # Optional for social auth

    def validate_phonenumber(self, value):
        if not value and not self.context.get('social_login'):
            raise serializers.ValidationError("Phone number is required for standard registration")
        if value:
            try:
                # Check if phonenumber is already in use
                if NewUser.objects.filter(phonenumber=value).exists():
                    raise serializers.ValidationError("This phone number is already registered")
            except Exception as e:
                raise serializers.ValidationError(f"Invalid phone number: {str(e)}")
        return value

    def validate(self, data):
        return super().validate(data)

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'phonenumber': self.validated_data.get('phonenumber', ''),
        }

    def save(self, request):
        # Get cleaned data
        cleaned_data = self.get_cleaned_data()
        # Create user with phonenumber
        user = self.context['request'].user if self.context['request'].user.is_authenticated else None
        if not user:
            user = NewUser.objects.create_user(
                email=cleaned_data['email'],
                username=cleaned_data['username'],
                phonenumber=cleaned_data['phonenumber'],
                password=cleaned_data['password1'],
            )
        # Create or update Profile
        Profile.objects.get_or_create(user=user)
        return user

class CustomUserDetailsSerializer(UserDetailsSerializer):
    profile_id = serializers.IntegerField(source='profile.id', read_only=True, allow_null=True)
    profile_image = serializers.SerializerMethodField()

    class Meta(UserDetailsSerializer.Meta):
        model = NewUser
        fields = ('id', 'username', 'email', 'phonenumber', 'profile_id', 'profile_image')
        read_only_fields = ('id', 'profile_id', 'profile_image')

    def get_profile_image(self, obj):
        if obj.profile and obj.profile.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.profile.image.url) if request else obj.profile.image.url
        return None

class ProfileSerializer(serializers.ModelSerializer):
    user = CustomUserDetailsSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'user', 'image', 'instagram', 'tiktok', 'facebook')
        read_only_fields = ('user', 'id')

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)