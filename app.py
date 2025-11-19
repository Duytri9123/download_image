from flask import Flask, render_template_string, request, send_file, jsonify
from urllib.parse import urlparse, parse_qs
from PIL import Image
from io import BytesIO
import requests

app = Flask(__name__)

def get_video_id(url):
    """Trích xuất video ID từ URL YouTube"""
    parsed_url = urlparse(url)

    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]

    return None

def get_thumbnail_url(video_url, quality='maxresdefault'):
    """Lấy URL thumbnail YouTube"""
    video_id = get_video_id(video_url)
    if not video_id:
        raise ValueError("URL YouTube không hợp lệ")

    return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"

def process_thumbnail(video_url, target_width=1920, target_height=1080, quality='maxresdefault'):
    """Xử lý và resize thumbnail"""
    try:
        thumbnail_url = get_thumbnail_url(video_url, quality)

        response = requests.get(thumbnail_url)
        response.raise_for_status()

        # Kiểm tra nếu maxresdefault không tồn tại
        if quality == 'maxresdefault' and len(response.content) < 5000:
            thumbnail_url = get_thumbnail_url(video_url, 'sddefault')
            response = requests.get(thumbnail_url)
            response.raise_for_status()

        # Mở và resize ảnh
        img = Image.open(BytesIO(response.content))
        original_size = img.size

        target_size = (target_width, target_height)
        img_resized = img.resize(target_size, Image.LANCZOS)

        # Lưu vào BytesIO để gửi về client
        img_io = BytesIO()
        img_resized.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)

        return img_io, original_size, target_size, thumbnail_url

    except Exception as e:
        return None, None, None, str(e)

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Thumbnail Downloader</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
            font-size: 14px;
        }
        
        input[type="text"],
        input[type="number"],
        select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus,
        input[type="number"]:focus,
        select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .size-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-top: 10px;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        
        .result.show {
            display: block;
        }
        
        .result img {
            width: 100%;
            border-radius: 10px;
            margin-bottom: 15px;
        }
        
        .info {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        
        .info p {
            margin: 5px 0;
            color: #555;
            font-size: 14px;
        }
        
        .download-btn {
            background: #28a745;
        }
        
        .download-btn:hover {
            box-shadow: 0 10px 20px rgba(40, 167, 69, 0.4);
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        
        .error.show {
            display: block;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube Thumbnail</h1>
        <p class="subtitle">Tải thumbnail YouTube với kích thước tùy chỉnh</p>
        
        <form id="thumbnailForm">
            <div class="input-group">
                <label for="videoUrl">URL Video YouTube</label>
                <input type="text" id="videoUrl" name="videoUrl" 
                       placeholder="https://www.youtube.com/watch?v=..." required>
            </div>
            
            <div class="input-group">
                <label for="quality">Chất lượng gốc</label>
                <select id="quality" name="quality">
                    <option value="maxresdefault">Max (1920x1080)</option>
                    <option value="sddefault">SD (640x480)</option>
                    <option value="hqdefault">HQ (480x360)</option>
                    <option value="mqdefault">MQ (320x180)</option>
                </select>
            </div>
            
            <div class="size-group">
                <div class="input-group">
                    <label for="width">Chiều rộng (px)</label>
                    <input type="number" id="width" name="width" value="1920" min="1" required>
                </div>
                <div class="input-group">
                    <label for="height">Chiều cao (px)</label>
                    <input type="number" id="height" name="height" value="1080" min="1" required>
                </div>
            </div>
            
            <button type="submit">🚀 Tạo Thumbnail</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top: 10px; color: #667eea;">Đang xử lý...</p>
        </div>
        
        <div class="error" id="error"></div>
        
        <div class="result" id="result">
            <img id="thumbnailPreview" src="" alt="Thumbnail">
            <div class="info" id="info"></div>
            <button class="download-btn" id="downloadBtn">⬇️ Tải xuống</button>
        </div>
    </div>
    
    <script>
        const form = document.getElementById('thumbnailForm');
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const result = document.getElementById('result');
        const thumbnailPreview = document.getElementById('thumbnailPreview');
        const info = document.getElementById('info');
        const downloadBtn = document.getElementById('downloadBtn');
        
        let currentImageUrl = '';
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Reset
            loading.classList.add('show');
            error.classList.remove('show');
            result.classList.remove('show');
            
            const formData = new FormData(form);
            const params = new URLSearchParams(formData);
            
            try {
                const response = await fetch('/process?' + params.toString());
                const data = await response.json();
                
                loading.classList.remove('show');
                
                if (data.success) {
                    thumbnailPreview.src = data.preview_url;
                    info.innerHTML = `
                        <p><strong>Kích thước gốc:</strong> ${data.original_size}</p>
                        <p><strong>Kích thước mới:</strong> ${data.new_size}</p>
                        <p><strong>URL gốc:</strong> <a href="${data.thumbnail_url}" target="_blank">Xem</a></p>
                    `;
                    currentImageUrl = data.download_url;
                    result.classList.add('show');
                } else {
                    error.textContent = '❌ ' + data.error;
                    error.classList.add('show');
                }
            } catch (err) {
                loading.classList.remove('show');
                error.textContent = '❌ Lỗi kết nối: ' + err.message;
                error.classList.add('show');
            }
        });
        
        downloadBtn.addEventListener('click', () => {
            if (currentImageUrl) {
                window.location.href = currentImageUrl;
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process')
def process():
    video_url = request.args.get('videoUrl')
    width = int(request.args.get('width', 1920))
    height = int(request.args.get('height', 1080))
    quality = request.args.get('quality', 'maxresdefault')

    if not video_url:
        return jsonify({'success': False, 'error': 'Thiếu URL video'})

    img_io, original_size, new_size, result = process_thumbnail(video_url, width, height, quality)

    if img_io is None:
        return jsonify({'success': False, 'error': result})

    # Tạo URL để preview và download
    video_id = get_video_id(video_url)

    # Lưu tạm vào session (trong thực tế nên dùng cache hoặc storage)
    # Ở đây trả về base64 để hiển thị
    import base64
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.read()).decode()

    return jsonify({
        'success': True,
        'preview_url': f'data:image/jpeg;base64,{img_base64}',
        'download_url': f'/download?videoUrl={video_url}&width={width}&height={height}&quality={quality}',
        'original_size': f'{original_size[0]}x{original_size[1]}',
        'new_size': f'{new_size[0]}x{new_size[1]}',
        'thumbnail_url': result
    })

@app.route('/download')
def download():
    video_url = request.args.get('videoUrl')
    width = int(request.args.get('width', 1920))
    height = int(request.args.get('height', 1080))
    quality = request.args.get('quality', 'maxresdefault')

    img_io, _, _, _ = process_thumbnail(video_url, width, height, quality)

    if img_io is None:
        return "Error processing thumbnail", 400

    video_id = get_video_id(video_url)
    filename = f'thumbnail_{video_id}_{width}x{height}.jpg'

    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True)