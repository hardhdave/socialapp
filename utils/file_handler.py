import os
import mimetypes
from flask import current_app

class FileHandler:
    @staticmethod
    def get_file_type(filename):
        """Determine file type based on extension"""
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            if mime_type.startswith('image/'):
                return 'image'
            elif mime_type.startswith('video/'):
                return 'video'
            elif mime_type.startswith('audio/'):
                return 'audio'
        return 'other'
    
    @staticmethod
    def get_file_size(file_path):
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    @staticmethod
    def format_file_size(size_bytes):
        """Format file size for display"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024.0 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"
    
    @staticmethod
    def delete_file(file_path):
        """Safely delete a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except OSError:
            pass
        return False
    
    @staticmethod
    def create_thumbnail(image_path, thumbnail_path, size=(300, 300)):
        """Create thumbnail for images"""
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, optimize=True, quality=85)
                return True
        except Exception:
            return False
