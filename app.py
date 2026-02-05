import os
import re
import uuid
import yt_dlp
import random
from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Railway uses /tmp for writable storage
DOWNLOAD_FOLDER = Path("/tmp/downloads")
DOWNLOAD_FOLDER.mkdir(exist_ok=True)

# User agents to rotate (makes requests look like real browsers)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edg/120.0.0.0'
]

# HTML Template (same as before)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartTube Downloader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .content { padding: 25px; }
        .input-group { margin-bottom: 20px; }
        input[type="text"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
        }
        input:focus { outline: none; border-color: #667eea; }
        button {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 10px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-mp3 {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .video-info {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            display: none;
        }
        .video-info.active { display: block; }
        .thumbnail { width: 100%; border-radius: 8px; margin-bottom: 15px; }
        .title { font-size: 18px; font-weight: 600; margin-bottom: 10px; }
        .qualities { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }
        .quality-btn {
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            background: white;
            cursor: pointer;
            text-align: center;
        }
        .quality-btn.selected {
            border-color: #667eea;
            background: #667eea;
            color: white;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        .success {
            background: #e8f5e9;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-top: 20px;
            display: none;
        }
        .success.active { display: block; }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 12px;
            border-radius: 8px;
            margin-top: 15px;
            display: none;
        }
        .error.active { display: block; }
        .tip {
            background: #fff3e0;
            color: #e65100;
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📺 SmartTube</h1>
            <p>YouTube Downloader</p>
        </div>
        
        <div class="content">
            <div class="input-group">
                <input type="text" id="url" placeholder="Paste YouTube URL here...">
            </div>
            
            <button class="btn-primary" onclick="analyze()">🔍 Analyze Video</button>
            
            <div class="error" id="error"></div>
            <div class="loading" id="loading" style="display:none;">⏳ Loading...</div>
            
            <div class="video-info" id="info">
                <img class="thumbnail" id="thumb" src="">
                <div class="title" id="title"></div>
                <div class="qualities" id="qualities"></div>
                <button class="btn-primary" id="downloadBtn" onclick="download()" disabled>⬇️ Download MP4</button>
                <button class="btn-mp3" onclick="downloadMp3()">🎵 Download MP3</button>
            </div>
            
            <div class="success" id="success">
                <h3>✅ Ready!</h3>
                <p id="filename"></p>
                <button class="btn-primary" onclick="getFile()">📥 Download File</button>
            </div>
            
            <div class="tip" id="tip" style="display:none;">
                💡 If download fails, try a different video. Some videos have restrictions.
            </div>
        </div>
    </div>

    <script>
        let currentData = null;
        let selectedFormat = null;
        let downloadId = null;

        async function analyze() {
            const url = document.getElementById('url').value.trim();
            if (!url) return showError('Enter a YouTube URL');
            
            // Remove tracking parameters
            const cleanUrl = url.split('&')[0].split('?si=')[0];
            
            showLoading(true);
            hideError();
            document.getElementById('tip').style.display = 'none';
            
            try {
                const res = await fetch('/api/info', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: cleanUrl})
                });
                const data = await res.json();
                
                if (data.error) throw new Error(data.error);
                
                currentData = data;
                showInfo(data);
            } catch (e) {
                showError(e.message);
                if (e.message.includes('bot') || e.message.includes('sign in')) {
                    document.getElementById('tip').style.display = 'block';
                }
            }
            showLoading(false);
        }

        function showInfo(data) {
            document.getElementById('info').classList.add('active');
            document.getElementById('thumb').src = data.thumbnail;
            document.getElementById('title').textContent = data.title;
            
            const grid = document.getElementById('qualities');
            grid.innerHTML = '';
            
            if (!data.formats || data.formats.length === 0) {
                grid.innerHTML = '<p style="grid-column: 2; color: #666;">No formats available. Try MP3 only.</p>';
                return;
            }
            
            data.formats.forEach(f => {
                const btn = document.createElement('div');
                btn.className = 'quality-btn';
                btn.innerHTML = `<div><b>${f.quality}</b></div><small>${f.size}</small>`;
                btn.onclick = () => selectFormat(f, btn);
                grid.appendChild(btn);
            });
        }

        function selectFormat(fmt, btn) {
            document.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            selectedFormat = fmt;
            document.getElementById('downloadBtn').disabled = false;
        }

        async function download() {
            if (!selectedFormat) return showError('Select a quality first');
            await startDownload(selectedFormat.id, 'mp4');
        }

        async function downloadMp3() {
            const audioFmt = currentData.audio_formats && currentData.audio_formats[0];
            if (!audioFmt) return showError('No audio available');
            await startDownload(audioFmt.id, 'mp3');
        }

        async function startDownload(formatId, type) {
            showLoading(true);
            
            try {
                const res = await fetch('/api/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        url: currentData.url,
                        format_id: formatId,
                        type: type
                    })
                });
                const data = await res.json();
                
                if (data.error) throw new Error(data.error);
                
                downloadId = data.download_id;
                showSuccess(data.filename);
            } catch (e) {
                showError(e.message);
            }
            showLoading(false);
        }

        function getFile() {
            window.location.href = '/api/file/' + downloadId;
        }

        function showError(msg) {
            const el = document.getElementById('error');
            el.textContent = msg;
            el.classList.add('active');
        }
        function hideError() {
            document.getElementById('error').classList.remove('active');
        }
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }
        function showSuccess(filename) {
            document.getElementById('success').classList.add('active');
            document.getElementById('filename').textContent = filename;
        }
    </script>
</body>
</html>
"""

def get_ydl_opts():
    """Get yt-dlp options with anti-bot measures"""
    return {
        'quiet': True,
        'no_warnings': True,
        'user_agent': random.choice(USER_AGENTS),
        'headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        },
        # Bypass age restriction and login
        'age_limit': None,
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        # Don't use cookies file (causes issues on Railway)
        'cookiefile': None,
        'nocheckcertificate': True,
        # Extractor options
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],  # Use android client (less restrictive)
                'player_skip': ['webpage', 'config', 'js'],
            }
        }
    }

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/info', methods=['POST'])
def get_info():
    url = request.json.get('url', '')
    if not url or 'youtube.com' not in url and 'youtu.be' not in url:
        return jsonify({'error': 'Valid YouTube URL required'}), 400
    
    try:
        ydl_opts = get_ydl_opts()
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({'error': 'Could not fetch video info'}), 400
            
            formats = []
            seen_qualities = set()
            
            # Get video formats
            for f in info.get('formats', []):
                # Skip storyboard/images
                if f.get('acodec') == 'none' and f.get('vcodec') != 'none':
                    height = f.get('height', 0)
                    if height and height not in seen_qualities:
                        filesize = f.get('filesize') or f.get('filesize_approx', 0)
                        if filesize:
                            seen_qualities.add(height)
                            formats.append({
                                'id': f['format_id'],
                                'quality': f"{height}p",
                                'size': format_size(filesize)
                            })
            
            # Get audio formats
            audio_formats = []
            seen_audio = set()
            for f in info.get('formats', []):
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    abr = f.get('abr', 0)
                    if abr and abr not in seen_audio:
                        seen_audio.add(abr)
                        filesize = f.get('filesize') or f.get('filesize_approx', 0)
                        audio_formats.append({
                            'id': f['format_id'],
                            'quality': f"{int(abr)}kbps",
                            'size': format_size(filesize)
                        })
            
            # Sort by quality
            formats.sort(key=lambda x: int(x['quality'][:-1]), reverse=True)
            audio_formats.sort(key=lambda x: x['quality'], reverse=True)
            
            return jsonify({
                'url': url,
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'formats': formats[:8],  # Limit to top 8
                'audio_formats': audio_formats[:3]
            })
            
    except Exception as e:
        error_msg = str(e)
        # Make error user-friendly
        if 'sign in' in error_msg.lower() or 'bot' in error_msg.lower():
            error_msg = 'YouTube blocked this request. Try a different video or check if the video is age-restricted/private.'
        elif 'unavailable' in error_msg.lower():
            error_msg = 'Video is unavailable, private, or region-blocked.'
        return jsonify({'error': error_msg}), 400

def format_size(bytes_val):
    """Format bytes to human readable"""
    if not bytes_val:
        return 'Unknown size'
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_id = data.get('format_id')
    file_type = data.get('type', 'mp4')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    download_id = str(uuid.uuid4())[:8]
    
    try:
        ydl_opts = get_ydl_opts()
        ydl_opts['format'] = format_id
        ydl_opts['outtmpl'] = str(DOWNLOAD_FOLDER / f'{download_id}_%(title)s.%(ext)s')
        
        # Add postprocessor for MP3
        if file_type == 'mp3':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            ydl_opts['format'] = 'bestaudio/best'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Find the downloaded file
            files = list(DOWNLOAD_FOLDER.glob(f"{download_id}_*"))
            if not files:
                return jsonify({'error': 'Download failed - file not created'}), 500
            
            actual_file = files[0]
            ext = '.mp3' if file_type == 'mp3' else '.mp4'
            clean_name = sanitize_filename(info.get('title', 'video')) + ext
            
            # Rename for clean download
            new_path = actual_file.parent / f"{download_id}_{clean_name}"
            actual_file.rename(new_path)
            
            return jsonify({
                'success': True,
                'download_id': download_id,
                'filename': clean_name
            })
            
    except Exception as e:
        error_msg = str(e)
        if 'sign in' in error_msg.lower():
            error_msg = 'YouTube blocked this download. The video may have restrictions.'
        return jsonify({'error': error_msg}), 400

def sanitize_filename(title):
    """Clean filename for safe usage"""
    if not title:
        title = 'video'
    # Remove invalid characters
    clean = re.sub(r'[<>:"/\\|?*]', '', title)
    # Limit length
    return clean[:80]

@app.route('/api/file/<download_id>')
def serve_file(download_id):
    """Serve the downloaded file"""
    try:
        files = list(DOWNLOAD_FOLDER.glob(f"{download_id}_*"))
        if not files:
            return jsonify({'error': 'File not found or expired'}), 404
        
        file_path = files[0]
        
        # Determine mime type
        mime = 'audio/mpeg' if file_path.suffix == '.mp3' else 'video/mp4'
        
        return send_file(
            file_path,
            mimetype=mime,
            as_attachment=True,
            download_name=file_path.name.replace(f"{download_id}_", "")
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
