import re
import requests
from urllib.parse import urlparse, parse_qs
from PIL import Image
from io import BytesIO


def get_video_id(url):
    """Trích xuất video ID từ URL YouTube"""
    # Các dạng URL YouTube phổ biến:
    # https://www.youtube.com/watch?v=VIDEO_ID
    # https://youtu.be/VIDEO_ID
    # https://www.youtube.com/embed/VIDEO_ID

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
    """
    Lấy URL thumbnail YouTube

    Các options quality:
    - maxresdefault: 1920x1080 (không phải video nào cũng có)
    - sddefault: 640x480
    - hqdefault: 480x360
    - mqdefault: 320x180
    - default: 120x90
    """
    video_id = get_video_id(video_url)
    if not video_id:
        raise ValueError("URL YouTube không hợp lệ")

    return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"


def download_thumbnail(video_url, output_path='thumbnail.jpg', target_size=(1920, 1080), quality='maxresdefault'):
    """
    Download thumbnail YouTube, resize về kích thước mong muốn và lưu vào file

    Args:
        video_url: URL video YouTube
        output_path: Đường dẫn file output
        target_size: Kích thước mục tiêu (width, height), mặc định 1920x1080
        quality: Chất lượng thumbnail gốc
    """
    try:
        thumbnail_url = get_thumbnail_url(video_url, quality)

        response = requests.get(thumbnail_url)
        response.raise_for_status()

        # Kiểm tra nếu maxresdefault không tồn tại (trả về ảnh nhỏ mặc định)
        if quality == 'maxresdefault' and len(response.content) < 5000:
            print("Thumbnail 1920x1080 không có sẵn, thử với sddefault (640x480)...")
            thumbnail_url = get_thumbnail_url(video_url, 'sddefault')
            response = requests.get(thumbnail_url)
            response.raise_for_status()

        # Mở ảnh từ response
        img = Image.open(BytesIO(response.content))
        original_size = img.size
        print(f"Kích thước gốc: {original_size[0]}x{original_size[1]}")

        # Resize về kích thước mong muốn
        # Sử dụng LANCZOS để có chất lượng tốt nhất
        img_resized = img.resize(target_size, Image.LANCZOS)

        # Lưu ảnh
        img_resized.save(output_path, quality=100, optimize=True)

        print(f"✓ Đã tải và resize thumbnail: {output_path}")
        print(f"Kích thước mới: {target_size[0]}x{target_size[1]}")
        print(f"URL: {thumbnail_url}")
        return thumbnail_url

    except Exception as e:
        print(f"✗ Lỗi: {e}")
        return None


# Ví dụ sử dụng
if __name__ == "__main__":
    # Thay URL này bằng video YouTube của bạn
    video_url = "https://www.youtube.com/watch?v=IiN4t59uA-E"

    # Lấy thumbnail và resize về 1920x1080
    download_thumbnail(video_url, "vad_1920x1080.jpg", target_size=(1920, 1080))

    # Hoặc resize về kích thước khác
    # download_thumbnail(video_url, "thumbnail_custom.jpg", target_size=(1280, 720))

    # Hoặc chỉ lấy URL không download
    thumbnail_url = get_thumbnail_url(video_url, quality='maxresdefault')
    print(f"\nURL thumbnail: {thumbnail_url}")