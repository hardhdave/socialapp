import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///social_media.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

    # Pagination
    POSTS_PER_PAGE = 10
    USERS_PER_PAGE = 20
    COMMENTS_PER_PAGE = 5

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # ✅ Gmail SMTP settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'gambhirg756@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'gizt wmnq cxwf sdvc'
    MAIL_DEFAULT_SENDER = MAIL_USERNAME
