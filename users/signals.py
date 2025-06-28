from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import NewUser
from .models import Profile

@receiver(post_save, sender=NewUser)  
def create_profile(sender, instance, created, **kwargs):
    """
    Ensures a Profile object is created for every new user.
    This is the single source of truth for Profile creation.
    """
    if created:
        Profile.objects.get_or_create(user=instance)
