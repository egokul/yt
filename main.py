from flask import Flask, render_template, request, send_from_directory
import yt_dlp
from pathlib import Path
import os
import humanize

app = Flask(__name__)

def get_format_options():
    return {
        'video': {
            'best': 'bestvideo*+bestaudio/best',
            'balanced': 'bestvideo[height<=1080]+bestaudio/best',
            'mobile': 'bestvideo[height<=720]+bestaudio/best',
        },
        'audio': {
            'best': '320',
            'balanced': '192',
            'mobile': '128',
        }
    }

def download_from_youtube(url, output_path="downloads", download_audio=False, quality="best"):
    try:
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        format_options = get_format_options()
        
        ydl_opts = {
            'progress_hooks': [lambda d: print(f"Downloading: {humanize.naturalsize(d.get('downloaded_bytes', 0))}")],
            'merge_output_format': 'mp4',
            'ignoreerrors': True,
            'no_warnings': True,
        }

        if download_audio:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'outtmpl': f'{output_path}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': format_options['audio'][quality],
                }],
            })
        else:
            ydl_opts.update({
                'format': format_options['video'][quality],
                'outtmpl': f'{output_path}/%(title)s.%(ext)s',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if download_audio:
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            return {
                'title': info['title'],
                'filename': os.path.basename(filename),
                'duration': info['duration'],
                'views': info['view_count']
            }
            
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    message = ''
    error = False
    download_links = []
    
    try:
        url = request.form['url']
        download_type = request.form['type']
        quality = request.form['quality']
        
        result = download_from_youtube(
            url,
            download_audio=(download_type == 'audio'),
            quality=quality
        )
        
        # Create download link
        filename = result['filename']
        file_path = os.path.join('downloads', filename)
        if os.path.exists(file_path):
            download_links.append({
                'url': f'/downloads/{filename}',
                'name': filename
            })
            message = f"Successfully downloaded: {result['title']}"
        else:
            message = "Download completed but file not found"
            error = True
    except Exception as e:
        message = str(e)
        error = True
    
    return render_template('index.html', message=message, error=error, download_links=download_links)

@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory('downloads', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
