# Alternative version using Piped (privacy-friendly YouTube API)
import requests
import os
import re
import uuid
from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = Path("/tmp/downloads")
DOWNLOAD_FOLDER.mkdir(exist_ok=True)

# Piped instances (YouTube alternatives that don't block)
PIPED_INSTANCES = [
    "https://api.piped.projectsegfault.com",
    "https://api.piped.privacydev.net",
    "https://api.piped.mha.fi",
    "https://pipedapi.moomoo.me"
]

HTML_TEMPLATE = """[same as above]"""

def get_piped_data(video_id):
    """Fetch data from Piped (YouTube proxy)"""
    for instance in PIPED_INSTANCES:
        try:
            url = f"{instance}/streams/{video_id}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except:
            continue
    return None

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/info', methods=['POST'])
def get_info():
    url = request.json.get('url', '')
    
    # Extract video ID
    video_id = None
    if 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[-1].split('?')[0]
    elif 'v=' in url:
        video_id = url.split('v=')[-1].split('&')[0]
    
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    # Try Piped first (no bot detection)
    data = get_piped_data(video_id)
    
    if data:
        formats = []
        # Video streams
        for stream in data.get('videoStreams', []):
            if stream.get('format') == 'MP4':
                quality = stream.get('quality', 'Unknown')
                formats.append({
                    'id': stream['url'],  # Direct URL
                    'quality': quality.replace('p', '') + 'p',
                    'size': 'Unknown'
                })
        
        # Audio streams
        audio_formats = []
        for stream in data.get('audioStreams', []):
            audio_formats.append({
                'id': stream['url'],
                'quality': stream.get('quality', 'Unknown'),
                'size': 'Unknown'
            })
        
        return jsonify({
            'url': url,
            'title': data.get('title', 'Unknown'),
            'thumbnail': data.get('thumbnailUrl', ''),
            'formats': formats[:6],
            'audio_formats': audio_formats[:3],
            'uploader': data.get('uploader', 'Unknown'),
            'duration': data.get('duration', 0)
        })
    
    # Fallback to yt-dlp with extra options
    return fallback_ytdlp(video_id, url)

def fallback_ytdlp(video_id, url):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['js', 'webpage'],
                }
            },
            'geo_bypass': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            for f in info.get('formats', []):
                if f.get('height'):
                    formats.append({
                        'id': f['format_id'],
                        'quality': f"{f['height']}p",
                        'size': 'Unknown'
                    })
            
            return jsonify({
                'url': url,
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'formats': formats[:6],
                'audio_formats': [],
                'uploader': info.get('uploader', 'Unknown')
            })
            
    except Exception as e:
        return jsonify({'error': f'Video unavailable: {str(e)}'}), 400

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_url = data.get('format_id')  # This is actually the direct URL for Piped
    file_type = data.get('type', 'mp4')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    download_id = str(uuid.uuid4())[:8]
    
    try:
        # If format_url is a direct HTTP URL (from Piped), download directly
        if format_url.startswith('http'):
            import requests
            r = requests.get(format_url, stream=True)
            
            ext = '.mp3' if file_type == 'mp3' else '.mp4'
            filename = f"{download_id}_video{ext}"
            filepath = DOWNLOAD_FOLDER / filename
            
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return jsonify({
                'success': True,
                'download_id': download_id,
                'filename': f"video{ext}"
            })
        
        # Otherwise use yt-dlp
        else:
            ydl_opts = {
                'format': format_url,
                'outtmpl': str(DOWNLOAD_FOLDER / f'{download_id}_%(title)s.%(ext)s'),
            }
            
            if file_type == 'mp3':
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                files = list(DOWNLOAD_FOLDER.glob(f"{download_id}_*"))
                
                if files:
                    ext = '.mp3' if file_type == 'mp3' else '.mp4'
                    clean_name = re.sub(r'[<>:"/\\|?*]', '', info.get('title', 'video')[:80]) + ext
                    
                    return jsonify({
                        'success': True,
                        'download_id': download_id,
                        'filename': clean_name
                    })
        
        return jsonify({'error': 'Download failed'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/file/<download_id>')
def serve_file(download_id):
    files = list(DOWNLOAD_FOLDER.glob(f"{download_id}_*"))
    if not files:
        return jsonify({'error': 'File not found'}), 404
    
    file_path = files[0]
    mime = 'audio/mpeg' if file_path.suffix == '.mp3' else 'video/mp4'
    
    return send_file(file_path, mimetype=mime, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
