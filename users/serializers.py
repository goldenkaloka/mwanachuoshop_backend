from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from .models import NewUser, Profile
from allauth.socialaccount.models import SocialAccount
from phonenumber_field.serializerfields import PhoneNumberField
from core.models import Campus, University
from django.apps import apps
from drf_spectacular.utils import extend_schema_field

class CustomRegisterSerializer(RegisterSerializer):
    phonenumber = PhoneNumberField(region='TZ', required=True)
    
    # Location fields - optional during registration
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
        data = self.validated_data if isinstance(self.validated_data, dict) else {}
        return {
            'username': data.get('username', ''),
            'password1': data.get('password1', ''),
            'email': data.get('email', ''),
            'phonenumber': data.get('phonenumber', ''),
        }

    def save(self, request):
        cleaned_data = self.get_cleaned_data()
        user = self.context['request'].user if self.context['request'].user.is_authenticated else None
        if not user:
            user = NewUser.objects.create_user(
                email=cleaned_data['email'],
                username=cleaned_data['username'],
                phonenumber=cleaned_data['phonenumber'],
                password=cleaned_data['password1'],
            )
        user.save()
        Profile.objects.get_or_create(user=user)
        return user

class CustomUserDetailsSerializer(UserDetailsSerializer):
    profile_id = serializers.IntegerField(source='profile.id', read_only=True, allow_null=True)
    profile_image = serializers.SerializerMethodField()
    
    class Meta(UserDetailsSerializer.Meta):
        model = NewUser
        fields = ('id', 'username', 'email', 'phonenumber', 'profile_id', 'profile_image')
        read_only_fields = ('id', 'profile_id', 'profile_image')
        ref_name = "UsersAppCustomUserDetails"

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_profile_image(self, obj) -> str:
        if obj.profile and obj.profile.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.profile.image.url) if request else obj.profile.image.url
        return None


class PublicUserSerializer(serializers.ModelSerializer):
    """Serializer for public user discovery - only exposes safe fields"""
    university_names = serializers.SerializerMethodField()
    university_short_names = serializers.SerializerMethodField()
    campus_names = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    
    class Meta:
        model = NewUser
        fields = (
            'id',
            'username',
            'university_names',
            'university_short_names',
            'campus_names',
            'profile_image',
            'start_date'
        )
        read_only_fields = fields
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_profile_image(self, obj) -> str:
        """Get profile image URL if available"""
        if obj.profile and obj.profile.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.profile.image.url) if request else obj.profile.image.url
        return None

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_university_names(self, obj) -> list:
        if obj.profile:
            return obj.profile.get_university_names()
        return []

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_university_short_names(self, obj) -> list:
        if obj.profile:
            return obj.profile.get_university_short_names()
        return []

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_campus_names(self, obj) -> list:
        if obj.profile:
            return obj.profile.get_campus_names()
        return []

class ProfileSerializer(serializers.ModelSerializer):
    user = CustomUserDetailsSerializer(read_only=True)
    campuses = serializers.PrimaryKeyRelatedField(
        queryset=apps.get_model('core', 'Campus').objects.all(),
        many=True,
        required=False
    )
    class Meta:
        model = Profile
        fields = ('id', 'user', 'image', 'instagram', 'tiktok', 'facebook', 'campuses')
        read_only_fields = ('user', 'id')

    def update(self, instance, validated_data):
        campuses = validated_data.pop('campuses', None)
        if campuses is not None:
            instance.campuses.set(campuses)
        return super().update(instance, validated_data)