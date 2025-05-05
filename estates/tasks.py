from celery import shared_task
from django.conf import settings
import os
import subprocess
import json

@shared_task(bind=True)
def process_video_task(self, video_id):
    try:
        # Import models inside the function to avoid circular imports
        from .models import Video
        video = Video.objects.get(id=video_id)
        
        # Update video status
        video.status = Video.PROCESSING
        video.is_running = True
        video.error_message = ''
        video.save()
        
        input_path = video.video.path
        output_dir = os.path.join(settings.MEDIA_ROOT, 'properties/videos/hls', str(video.id))
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get video metadata
        metadata = get_video_metadata(input_path)
        video.duration = float(metadata.get('duration', 0))
        video.save()
        
        # Generate HLS playlist
        hls_playlist = generate_hls(input_path, output_dir)
        video.hls_playlist = os.path.relpath(hls_playlist, settings.MEDIA_ROOT)
        
        # Generate thumbnail
        thumbnail_path = generate_thumbnail(input_path, output_dir)
        if thumbnail_path:
            video.thumbnail.name = os.path.relpath(thumbnail_path, settings.MEDIA_ROOT)
        
        # Mark as completed
        video.status = Video.COMPLETED
        video.is_running = False
        video.save()
        
        return {'status': 'COMPLETED', 'video_id': video.id}
        
    except Exception as e:
        if video:
            video.status = Video.FAILED
            video.error_message = str(e)
            video.is_running = False
            video.save()
        raise self.retry(exc=e, countdown=60)

def get_video_metadata(input_path):
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
    
    return json.loads(result.stdout)

def generate_hls(input_path, output_dir):
    """Convert video to HLS format"""
    playlist_path = os.path.join(output_dir, 'playlist.m3u8')
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-profile:v', 'baseline',
        '-level', '3.0',
        '-start_number', '0',
        '-hls_time', '10',
        '-hls_list_size', '0',
        '-f', 'hls',
        '-hls_segment_filename', os.path.join(output_dir, 'segment_%03d.ts'),
        '-hls_flags', 'independent_segments',
        '-hls_playlist_type', 'vod',
        '-movflags', '+faststart',
        '-y',
        playlist_path
    ]
    
    result = subprocess.run(cmd, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(f"FFmpeg HLS conversion failed: {result.stderr.decode()}")
    
    return playlist_path

def generate_thumbnail(input_path, output_dir):
    """Generate a thumbnail from the video"""
    thumbnail_path = os.path.join(output_dir, 'thumbnail.jpg')
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-ss', '00:00:02',
        '-vframes', '1',
        '-q:v', '2',
        '-y',
        thumbnail_path
    ]
    
    result = subprocess.run(cmd, stderr=subprocess.PIPE)
    if result.returncode != 0:
        return None
    
    return thumbnail_path