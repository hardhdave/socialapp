import os
import secrets
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename
import smtplib
import ssl
from email.message import EmailMessage

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def allowed_image_file(filename):
    allowed = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed

def allowed_video_file(filename):
    allowed = {'mp4', 'mov', 'avi'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed

def save_picture(form_picture, folder, prefix, is_video=False):
    """Save uploaded file and return filename"""
    try:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = f"{prefix}_{random_hex}{f_ext}"
        
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        
        picture_path = os.path.join(upload_path, picture_fn)
        
        if is_video:
            # For videos, save directly without processing
            form_picture.save(picture_path)
        else:
            # For images, resize and optimize
            img = Image.open(form_picture)
            
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize image if too large
            max_size = (1200, 1200)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(picture_path, optimize=True, quality=85)
        
        return picture_fn
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

def format_datetime(dt):
    """Format datetime for display"""
    from datetime import datetime
    
    if not dt:
        return ""
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "Just now"

def truncate_text(text, length=100):
    """Truncate text to specified length"""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'

def extract_mentions(text):
    """Extract @mentions from text"""
    import re
    mentions = re.findall(r'@(\w+)', text)
    return list(set(mentions))  # Remove duplicates

def extract_hashtags(text):
    """Extract #hashtags from text"""
    import re
    hashtags = re.findall(r'#(\w+)', text)
    return list(set(hashtags))  # Remove duplicates

def format_number(num):
    """Format numbers for display (1K, 1M, etc.)"""
    if num < 1000:
        return str(num)
    elif num < 1000000:
        return f"{num/1000:.1f}K"
    elif num < 1000000000:
        return f"{num/1000000:.1f}M"
    else:
        return f"{num/1000000000:.1f}B"

def send_email(subject, recipient_email, body):
    """Send a plain text email using SMTP settings from config"""
    try:
        mail_server = current_app.config.get('MAIL_SERVER')
        mail_port = current_app.config.get('MAIL_PORT', 587)
        use_tls = current_app.config.get('MAIL_USE_TLS', True)
        use_ssl = current_app.config.get('MAIL_USE_SSL', False)
        username = current_app.config.get('MAIL_USERNAME')
        password = current_app.config.get('MAIL_PASSWORD')

        if not (mail_server and username and password and recipient_email):
            print(f"Mail settings missing. Server: {bool(mail_server)}, Username: {bool(username)}, Password: {bool(password)}, Recipient: {bool(recipient_email)}")
            return False, "Mail settings not fully configured"

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = username
        msg['To'] = recipient_email
        msg.set_content(body)

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        if use_ssl:
            print(f"Connecting to {mail_server}:{mail_port} using SSL")
            with smtplib.SMTP_SSL(mail_server, mail_port, context=context) as server:
                server.login(username, password)
                server.send_message(msg)
        else:
            print(f"Connecting to {mail_server}:{mail_port} using TLS")
            with smtplib.SMTP(mail_server, mail_port) as server:
                server.ehlo()
                if use_tls:
                    server.starttls(context=context)
                    server.ehlo()
                server.login(username, password)
                server.send_message(msg)
        print(f"Email sent successfully to {recipient_email}")
        return True, None
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        return False, f"Authentication failed. Check your email credentials. Error: {str(e)}"
    except smtplib.SMTPRecipientsRefused as e:
        print(f"SMTP Recipients Refused: {e}")
        return False, f"Recipient email address rejected. Error: {str(e)}"
    except smtplib.SMTPServerDisconnected as e:
        print(f"SMTP Server Disconnected: {e}")
        return False, f"Connection to mail server failed. Error: {str(e)}"
    except ssl.SSLError as e:
        print(f"SSL Error: {e}")
        return False, f"SSL connection failed. Error: {str(e)}"
    except Exception as e:
        print(f"Unexpected error sending email: {e}")
        return False, f"Unexpected error occurred: {str(e)}"
