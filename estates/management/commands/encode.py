import subprocess
import os
import json
import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from estates.models import Video

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process pending videos to HLS format and generate thumbnails'

    def handle(self, *args, **options):
        try:
            # Get the oldest pending video that isn't already being processed
            video = Video.objects.filter(status=Video.PENDING, is_running=False).first()
            
            if not video:
                logger.info("No pending videos found for processing")
                return

            logger.info(f"Processing video: {video.id} - {video.name}")
            
            # Mark video as processing
            video.status = Video.PROCESSING
            video.is_running = True
            video.save()

            input_path = video.video.path
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = os.path.join(os.path.dirname(input_path), 'hls')
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Get video metadata
            metadata = self.get_video_metadata(input_path)
            video.duration = float(metadata.get('duration', 0))
            video.save()

            # Generate HLS playlist
            hls_playlist = self.generate_hls(input_path, output_dir, base_name)
            video.hls_playlist = os.path.relpath(hls_playlist, settings.MEDIA_ROOT)

            # Generate thumbnail
            thumbnail_path = self.generate_thumbnail(input_path, output_dir, base_name)
            if thumbnail_path:
                video.thumbnail.name = os.path.relpath(thumbnail_path, settings.MEDIA_ROOT)

            # Mark as completed
            video.status = Video.COMPLETED
            video.is_running = False
            video.save()
            
            logger.info(f"Successfully processed video {video.id}")

        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            if video:
                video.status = Video.FAILED
                video.error_message = str(e)
                video.is_running = False
                video.save()

    def get_video_metadata(self, input_path):
        """Extract video metadata using ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            input_path
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise Exception(f"FFprobe error: {result.stderr.decode()}")

        metadata = json.loads(result.stdout)
        
        # Extract duration from format or video stream
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

    def generate_hls(self, input_path, output_dir, base_name):
        """Convert video to HLS format"""
        playlist_path = os.path.join(output_dir, f"{base_name}.m3u8")
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-profile:v', 'baseline',  # Broad device compatibility
            '-level', '3.0',
            '-start_number', '0',
            '-hls_time', '10',  # 10-second segments
            '-hls_list_size', '0',  # Keep all segments in playlist
            '-f', 'hls',
            '-hls_segment_filename', os.path.join(output_dir, f"{base_name}_%03d.ts"),
            '-hls_flags', 'independent_segments',
            '-hls_playlist_type', 'vod',  # Video on demand
            '-movflags', '+faststart',
            '-y',  # Overwrite without asking
            playlist_path
        ]
        
        result = subprocess.run(cmd, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise Exception(f"FFmpeg HLS conversion failed: {result.stderr.decode()}")
        
        return playlist_path

    def generate_thumbnail(self, input_path, output_dir, base_name):
        """Generate a thumbnail from the video"""
        thumbnail_path = os.path.join(output_dir, f"{base_name}.jpg")
        
        # Try to get thumbnail at 10% of video duration
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', '00:00:02',  # Capture at 2 seconds
            '-vframes', '1',
            '-q:v', '2',  # Quality level (2-31, lower is better)
            '-y',
            thumbnail_path
        ]
        
        result = subprocess.run(cmd, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logger.warning(f"Thumbnail generation failed: {result.stderr.decode()}")
            return None
        
        return thumbnail_path