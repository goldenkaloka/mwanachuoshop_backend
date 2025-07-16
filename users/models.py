from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from phonenumber_field.modelfields import PhoneNumberField
from core.models import Campus
from django.contrib.gis.db import models as gis_models

class CustomAccountManager(BaseUserManager):
    def create_superuser(self, email, username, phonenumber, password, **other_fields):
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)
        
        if other_fields.get('is_staff') is not True:
            raise ValueError('Superuser must be assigned to is_staff=True')
        
        if other_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must be assigned to is_superuser=True')
            
        return self.create_user(email, username, phonenumber, password, **other_fields)
        
    def create_user(self, email, username, phonenumber, password=None, **other_fields):
        if not email:
            raise ValueError('You must provide an email address')
        if not phonenumber:
            raise ValueError('You must provide a phone number')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            phonenumber=phonenumber,
            **other_fields
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # For social auth users without password
        user.save()
        
        # The associated Profile is created via a post_save signal in users/signals.py
        return user

class NewUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(max_length=150, unique=True)
    phonenumber = PhoneNumberField(region='TZ', unique=True, blank=False, null=False)
    start_date = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    groups = models.ManyToManyField(
        Group,
        related_name='newuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='newuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    objects = CustomAccountManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phonenumber']
    
    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(
        NewUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    campuses = models.ManyToManyField(
        Campus,
        related_name='profiles',
        blank=True
    )
    image = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )
    instagram = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    tiktok = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    facebook = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default='mtoto'
    )

    class Meta:
        pass

    def __str__(self):
        return f"Profile for {self.user.username}"
    
    def get_university_names(self):
        """Get all university names for this profile via campuses"""
        return list({c.university.name for c in self.campuses.all()})

    def get_university_short_names(self):
        """Get all university short names for this profile via campuses"""
        return list({c.university.short_name for c in self.campuses.all()})

    def get_campus_names(self):
        return [c.name for c in self.campuses.all()]

    def has_location_info(self):
        return self.campuses.exists()

    def get_location_display(self):
        if self.campuses.exists():
            return ", ".join([f"{c.name} ({c.university.short_name})" for c in self.campuses.all()])
        return "No location set"