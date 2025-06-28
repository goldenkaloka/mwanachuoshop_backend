import base64
import logging
import time
import requests
import cloudflare
from datetime import datetime
from django.conf import settings
from django.core.files.storage import default_storage
from cloudflare import Cloudflare, DefaultHttpxClient
from httpx import Timeout

from .models import Property

logger = logging.getLogger(__name__)

def wait_for_video_ready(cf, video_uid, max_attempts=30, delay=10):
    """Polls Cloudflare until the video is ready for streaming."""
    for attempt in range(max_attempts):
        try:
            video = cf.stream.get(identifier=video_uid, account_id=settings.CLOUDFLARE_ACCOUNT_ID)
            status_state = video.status.state
            logger.debug(f"Video {video_uid} status: {status_state}. Attempt {attempt + 1}/{max_attempts}.")
            if status_state == 'ready':
                return video
            elif status_state in ['error', 'deleted']:
                logger.error(f"Video {video_uid} entered a failed state: {status_state}")
                return None
            time.sleep(delay)
        except cloudflare.APIStatusError as e:
            logger.error(f"API Error checking video {video_uid} status: Status={e.status_code}, Response={e.response.text}")
            return None
    logger.warning(f"Video {video_uid} not ready after {max_attempts} attempts.")
    return None

def process_property_video(property_id, temp_video_path, video_name, video_description):
    """
    Background task to upload a video to Cloudflare Stream and update the Property model.
    """
    prop = None
    try:
        prop = Property.objects.get(id=property_id)
        prop.video_processing_status = Property.VideoProcessingStatus.PROCESSING
        prop.save()

        cf = Cloudflare(
            api_token=settings.CLOUDFLARE_STREAM_API_TOKEN,
            http_client=DefaultHttpxClient(timeout=Timeout(30.0, read=10.0, write=15.0, connect=5.0))
        )

        # If updating an existing property with a new video, delete the old one first
        if prop.stream_video_id:
            try:
                cf.stream.delete(identifier=prop.stream_video_id, account_id=settings.CLOUDFLARE_ACCOUNT_ID)
                logger.info(f"Deleted old video from Cloudflare Stream: {prop.stream_video_id}")
            except Exception as e:
                logger.warning(f"Failed to delete old video {prop.stream_video_id}: {e}")

        upload_response = cf.stream.direct_upload.create(
            account_id=settings.CLOUDFLARE_ACCOUNT_ID,
            max_duration_seconds=3600,
            meta={'name': video_name, 'description': video_description}
        )
        upload_url = upload_response.uploadURL
        stream_video_id = upload_response.uid

        with default_storage.open(temp_video_path, 'rb') as f:
            response = requests.post(upload_url, files={'file': (video_name, f)})
            response.raise_for_status()

        ready_video = wait_for_video_ready(cf, stream_video_id)

        if not ready_video:
            raise Exception(f"Video {stream_video_id} failed to become ready.")

        # Update property with video details
        prop.stream_video_id = ready_video.uid
        prop.thumbnail_url = ready_video.thumbnail
        prop.duration = ready_video.duration
        prop.video_processing_status = Property.VideoProcessingStatus.READY
        prop.save()
        logger.info(f"Successfully processed video for Property {prop.id}. Cloudflare UID: {ready_video.uid}")

    except Property.DoesNotExist:
        logger.error(f"Property with id {property_id} not found for video processing.")
    except Exception as e:
        logger.error(f"Video processing failed for property {property_id}: {e}")
        if prop:
            prop.video_processing_status = Property.VideoProcessingStatus.FAILED
            prop.save()
    finally:
        # Clean up the temporary file
        if default_storage.exists(temp_video_path):
            default_storage.delete(temp_video_path)
            logger.info(f"Deleted temporary video file: {temp_video_path}")