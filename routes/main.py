from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models.post import Post
from models.user import User
from models.notification import Notification
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']
    
    # Always show global recent posts (Public Timeline)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get trending tags for sidebar
    trending_tags = Post.get_trending_tags(limit=5)
    
    return render_template('main/index.html', 
                         posts=posts, 
                         trending_tags=trending_tags)

@main_bp.route('/explore')
def explore():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']
    filter_type = request.args.get('filter')
    
    query = Post.query
    
    # Apply filters
    if filter_type == 'videos':
        query = query.filter(Post.video_filename.isnot(None))
    elif filter_type == 'photos':
        query = query.filter(Post.image_filename.isnot(None))
        
    # Apply sorting
    if filter_type == 'recent':
        query = query.order_by(Post.created_at.desc())
    elif filter_type == 'popular':
        query = query.order_by(Post.likes_count.desc())
    else:
        # Default trending
        query = query.order_by((Post.likes_count + Post.comments_count).desc())
        
    posts = query.paginate(page=page, per_page=per_page, error_out=False)
    
    trending_tags = Post.get_trending_tags(limit=10)
    suggested_users = []
    
    if current_user.is_authenticated:
        # Get users not followed by current user
        suggested_users = User.query.filter(
            ~User.id.in_([f.followed_id for f in current_user.following.all()]),
            User.id != current_user.id
        ).limit(5).all()
    
    return render_template('main/explore.html', 
                         posts=posts, 
                         trending_tags=trending_tags,
                         suggested_users=suggested_users)

@main_bp.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']
    
    posts = Post.query.filter(
        or_(
            Post.content.contains(query),
            Post.tags.contains(query)
        )
    ).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    users = User.query.filter(
        or_(
            User.username.contains(query),
            User.full_name.contains(query)
        )
    ).limit(10).all()
    
    return render_template('main/search.html', 
                         posts=posts, 
                         users=users, 
                         query=query)

@main_bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifications = current_user.notifications_received.order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    # Mark notifications as read
    unread_notifications = current_user.notifications_received.filter_by(is_read=False).all()
    for notification in unread_notifications:
        notification.mark_as_read()
    db.session.commit()
    
    return render_template('main/notifications.html', notifications=notifications)

@main_bp.before_request
def before_request():
    if current_user.is_authenticated:
        from datetime import datetime
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
