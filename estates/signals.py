# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django_q.tasks import async_task
# from estates.models import Property
# from video_transcoding.tasks import transcode_video
# import logging

# logger = logging.getLogger(__name__)

# @receiver(post_save, sender=Property)
# def trigger_video_transcoding(sender, instance, created, **kwargs):
#     """Trigger video transcoding for new or updated videos."""
#     logger.info(f"post_save signal triggered for Property ID {instance.id}, created={created}")
#     original_video = getattr(instance, '_original_video', None)
#     current_video = instance.video.name if instance.video else None

#     if instance.video and (created or current_video != original_video):
#         logger.info(f"Queuing video transcoding for Property ID {instance.id}")
#         async_task(
#             'video_transcoding.tasks.transcode_video',
#             instance.id,
#             profile='mp4_h264',
#             model='estates.Property',
#             field='transcoded_video',
#             thumbnail_field='thumbnail',
#             duration_field='duration',
#             group=f'property_video_{instance.id}'
#         )
#     else:
#         logger.info(f"Video transcoding not queued for Property ID {instance.id}. Video present: {bool(instance.video)}, Changed: {current_video != original_video}")

#     instance._original_video = current_video
