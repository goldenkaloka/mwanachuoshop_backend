from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from estates.models import Property
from estates.tasks import queue_video_processing
from shops.models import UserOffer
from payments.models import Payment
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Property)
def check_estate_creation_permissions(sender, instance, **kwargs):
    user = instance.owner
    logger.info(f"Checking estate creation permissions for user {user.username}, property ID {instance.id or 'None'}")

    # Fetch UserOffer
    try:
        offer = UserOffer.objects.filter(user=user).first()
        logger.info(f"Offer found: {offer is not None}, Free estates remaining: {offer.free_estates_remaining if offer else 0}")
    except Exception as e:
        logger.error(f"Error checking UserOffer for user {user.username}: {str(e)}")
        offer = None

    # Check for completed payment for this specific property
    has_paid = False
    if instance.id:  # Only check payment if property has an ID (i.e., exists in DB)
        has_paid = Payment.objects.filter(
            user=user,
            payment_type=Payment.PaymentType.ESTATE,
            status=Payment.PaymentStatus.COMPLETED,
            content_type=ContentType.objects.get_for_model(Property),
            object_id=instance.id
        ).exists()
        logger.info(f"Completed payment found for property ID {instance.id}: {has_paid}")

    # Allow creation if user has free estate offers or a completed payment
    if offer and offer.free_estates_remaining > 0:
        logger.info(f"Allowing property creation for user {user.username} due to free estate offer")
        instance.is_available = True  # Set is_available=True for free offer
        return
    if has_paid:
        logger.info(f"Allowing property creation for user {user.username} due to completed payment")
        instance.is_available = True  # Set is_available=True for paid property
        return

    # Allow creation with is_available=False, to be activated via payment
    logger.info(f"Allowing property creation for user {user.username} with is_available=False, pending payment")
    instance.is_available = False

@receiver(post_save, sender=Property)
def process_property_video(sender, instance, created, **kwargs):
    logger.info(f"post_save signal triggered for Property ID {instance.id}, created={created}")
    if created:
        logger.info(f"Property ID {instance.id} is new. Video: {instance.video}, is_video_processing: {instance.is_video_processing}")
        if instance.video and not instance.is_video_processing:
            logger.info(f"Queuing video processing for Property ID {instance.id}")
            queue_video_processing(instance.id)
        else:
            logger.warning(f"Video processing not queued for Property ID {instance.id}. Video present: {bool(instance.video)}, is_video_processing: {instance.is_video_processing}")
    else:
        logger.info(f"Property ID {instance.id} is being updated, not created. Skipping video processing.")