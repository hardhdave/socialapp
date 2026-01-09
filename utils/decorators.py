from functools import wraps
from flask import abort, request, jsonify
from flask_login import current_user

def admin_required(f):
    """Require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def ajax_required(f):
    """Require AJAX request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'AJAX request required'}), 400
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests=100, per_seconds=3600):
    """Simple rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple rate limiting could be implemented here
            # For production, consider using Flask-Limiter
            return f(*args, **kwargs)
        return decorated_function
    return decorator
