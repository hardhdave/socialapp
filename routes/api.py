from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from models.user import User
from models.post import Post
from models.notification import Notification

api_bp = Blueprint('api', __name__)

@api_bp.route('/notifications/unread-count')
@login_required
def unread_notifications_count():
    count = current_user.unread_notifications_count()
    return jsonify({'count': count})

@api_bp.route('/users/search')
def search_users():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'users': []})
    
    users = User.query.filter(
        User.username.contains(query) | 
        User.full_name.contains(query)
    ).limit(10).all()
    
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'avatar': user.get_profile_picture_url(),
            'is_following': current_user.is_following(user) if current_user.is_authenticated else False
        })
    
    return jsonify({'users': result})

@api_bp.route('/posts/trending')
def trending_posts():
    posts = Post.get_trending_posts(limit=10)
    result = []
    
    for post in posts:
        result.append({
            'id': post.id,
            'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'author': post.author.username,
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'time_ago': post.time_ago(),
            'image_url': post.get_image_url()
        })
    
    return jsonify({'posts': result})

@api_bp.route('/stats')
@login_required
def user_stats():
    return jsonify({
        'posts_count': current_user.posts_count(),
        'followers_count': current_user.followers_count(),
        'following_count': current_user.following_count(),
        'notifications_count': current_user.unread_notifications_count()
    })
