from datetime import timedelta, timezone
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField



class CustomAccountManager(BaseUserManager):
    def create_superuser(self, email, username, password, **other_fields):
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)
        
        if other_fields.get('is_staff') is not True:
            raise ValueError('Superuser must be assigned to is_staff=True')
        
        if other_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must be assigned to is_superuser=True')
            
        return self.create_user(email, username, password, **other_fields)
        
    def create_user(self, email, username, password, **other_fields):
        if not email:
            raise ValueError('You must provide an email address')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            **other_fields
        )
        user.set_password(password)
        user.save()
        return user


class NewUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(max_length=150, unique=True)
    phonenumber = PhoneNumberField(region='TZ', unique=False)
    start_date = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
   
    objects = CustomAccountManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username',  'phonenumber']
        
    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(
        NewUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    image = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )
    whatsapp = PhoneNumberField(
        region='TZ',
        blank=True,
        null=True
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
