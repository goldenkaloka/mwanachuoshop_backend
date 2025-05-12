import subprocess
import os
import json
import logging
from django.conf import settings
from django_q.tasks import async_task
from estates.models import Property

logger = logging.getLogger(__name__)

class PropertyVideoProcessor:
    @staticmethod
    def process_video(property_id):
        """Process video for a Property, generating HLS playlist and thumbnail."""
        try:
            property_instance = Property.objects.get(id=property_id)
            logger.info(f"Starting processing for Property ID {property_id}: {property_instance.title}")
            
            if property_instance.video_status != Property.PENDING:
                logger.warning(f"Property ID {property_id} video_status is {property_instance.video_status}, skipping")
                return False

            property_instance.video_status = Property.PROCESSING
            property_instance.is_video_processing = True
            property_instance.video_error_message = ''
            property_instance.save()
            logger.info(f"Set video_status to PROCESSING for Property ID {property_id}")

            # Process video
            metadata = PropertyVideoProcessor.get_metadata(property_instance.video.path)
            hls_path = PropertyVideoProcessor.convert_to_hls(property_instance)
            thumbnail_path = PropertyVideoProcessor.generate_thumbnail(property_instance)
            
            # Update property record
            property_instance.duration = float(metadata.get('duration', 0))
            property_instance.hls_playlist = os.path.relpath(hls_path, settings.MEDIA_ROOT)
            if thumbnail_path:
                property_instance.thumbnail.name = os.path.relpath(thumbnail_path, settings.MEDIA_ROOT)
            property_instance.video_status = Property.COMPLETED
            property_instance.is_video_processing = False
            property_instance.save()
            logger.info(f"Completed processing for Property ID {property_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed processing Property ID {property_id}: {str(e)}", exc_info=True)
            if 'property_instance' in locals():
                property_instance.video_status = Property.FAILED
                property_instance.is_video_processing = False
                property_instance.video_error_message = str(e)
                property_instance.save()
            raise Exception(f"Video processing failed: {str(e)}")

    @staticmethod
    def get_metadata(video_path):
        """Extract video metadata using ffprobe."""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_format', '-show_streams',
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"FFprobe failed for {video_path}: {result.stderr}")
            raise Exception(f"FFprobe error: {result.stderr}")
        
        metadata = json.loads(result.stdout)
        duration = None
        
        if 'format' in metadata and 'duration' in metadata['format']:
            duration = float(metadata['format']['duration'])
        else:
            for stream in metadata.get('streams', []):
                if stream.get('codec_type') == 'video' and 'duration' in stream:
                    duration = float(stream['duration'])
                    break
        
        if duration is None:
            raise Exception("Could not determine video duration")
        
        return {'duration': duration}

    @staticmethod
    def convert_to_hls(property_instance):
        """Convert video to HLS format with dynamic segment URLs."""
        input_path = property_instance.video.path
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.join(settings.HLS_OUTPUT_DIR, f"property_{property_instance.id}")
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created HLS output directory: {output_dir}")
        except Exception as e:
            logger.error(f"Failed to create HLS output directory {output_dir}: {str(e)}")
            raise Exception(f"Failed to create HLS output directory: {str(e)}")

        playlist_path = os.path.join(output_dir, f"{base_name}.m3u8")
        segment_pattern = os.path.join(output_dir, f"{base_name}_%03d.ts")
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-profile:v', 'baseline',
            '-level', '3.0',
            '-start_number', '0',
            '-hls_time', '10',
            '-hls_list_size', '0',
            '-f', 'hls',
            '-hls_segment_filename', segment_pattern,
            '-hls_flags', 'independent_segments',
            '-hls_playlist_type', 'vod',
            '-movflags', '+faststart',
            '-y', playlist_path
        ]
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"HLS conversion failed for Property ID {property_instance.id}: {result.stderr}")
            raise Exception(f"HLS conversion failed: {result.stderr}")
        
        # Verify .ts files exist
        ts_files = [f for f in os.listdir(output_dir) if f.endswith('.ts')]
        if not ts_files:
            logger.error(f"No .ts files found in {output_dir} after FFmpeg processing")
            raise Exception("No HLS segment files generated")
        logger.info(f"Generated {len(ts_files)} .ts files in {output_dir}")

        # Update .m3u8 file with dynamic URLs
        segment_url_prefix = f"/api/estates/properties/{property_instance.id}/segments/"
        with open(playlist_path, 'r') as f:
            m3u8_content = f.read()
        m3u8_content = m3u8_content.replace(f"{base_name}_", segment_url_prefix + f"{base_name}_")
        with open(playlist_path, 'w') as f:
            f.write(m3u8_content)
        
        logger.info(f"Updated .m3u8 file with segment URLs starting with {segment_url_prefix}")
        return playlist_path

    @staticmethod
    def generate_thumbnail(property_instance):
        """Generate thumbnail for the property video."""
        input_path = property_instance.video.path
        output_dir = os.path.join(settings.THUMBNAIL_DIR, f"property_{property_instance.id}")
        os.makedirs(output_dir, exist_ok=True)
        
        thumbnail_path = os.path.join(output_dir, 'thumbnail.jpg')
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ss', '00:00:02',
            '-vframes', '1',
            '-q:v', '2',
            '-y', thumbnail_path
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.warning(f"Thumbnail generation failed for Property ID {property_instance.id}: {result.stderr}")
            return None
        
        return thumbnail_path

def queue_video_processing(property_id):
    """Queue a property video for processing."""
    logger.info(f"Queueing video processing for Property ID {property_id}")
    async_task(
        PropertyVideoProcessor.process_video,
        property_id,
        group=f'property_video_{property_id}'
    )