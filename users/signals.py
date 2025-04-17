from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.db.models.signals import post_save
from .models import NewUser
from .models import Profile

@receiver(post_save, sender=NewUser)  
def create_profile(sender, instance, created, **kwargs):
    user = instance
    if created:
        Profile.objects.create(
            user = user,
        )
    else:
        profile = get_object_or_404(Profile, user=user)
        profile.save()
        

