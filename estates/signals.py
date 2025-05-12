from django.db.models.signals import post_save
from django.dispatch import receiver
from estates.models import Property
from estates.tasks import queue_video_processing

@receiver(post_save, sender=Property)
def process_property_video(sender, instance, created, **kwargs):
    if created and instance.video and not instance.is_video_processing:
        queue_video_processing(instance.id)