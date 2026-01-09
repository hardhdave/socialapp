from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from models.user import User
from models.post import Post
from models.follow import Follow
from models.notification import Notification
from utils.helpers import allowed_file, save_picture

user_bp = Blueprint('user', __name__)

@user_bp.route('/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']
    
    posts = user.posts.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Check if current user can view this profile
    can_view = True
    if user.is_private and current_user != user:
        if current_user.is_anonymous or not current_user.is_following(user):
            can_view = False
    
    return render_template('user/profile.html', 
                         user=user, 
                         posts=posts, 
                         can_view=can_view)

@user_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', '')
        current_user.bio = request.form.get('bio', '')
        current_user.location = request.form.get('location', '')
        current_user.website = request.form.get('website', '')
        current_user.is_private = bool(request.form.get('is_private'))
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename and allowed_file(file.filename):
                filename = save_picture(file, 'profiles', current_user.username)
                if filename:
                    current_user.profile_picture = filename
        
        # Handle cover photo upload
        if 'cover_photo' in request.files:
            file = request.files['cover_photo']
            if file and file.filename and allowed_file(file.filename):
                filename = save_picture(file, 'profiles', f"{current_user.username}_cover")
                if filename:
                    current_user.cover_photo = filename
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('user.profile', username=current_user.username))
    
    return render_template('user/edit_profile.html')

@user_bp.route('/<username>/followers')
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['USERS_PER_PAGE']
    
    followers_query = User.query.join(Follow, Follow.follower_id == User.id)\
                                .filter(Follow.followed_id == user.id)\
                                .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('user/followers.html', 
                         user=user, 
                         users=followers_query, 
                         title='Followers')

@user_bp.route('/<username>/following')
def following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['USERS_PER_PAGE']
    
    following_query = User.query.join(Follow, Follow.followed_id == User.id)\
                                .filter(Follow.follower_id == user.id)\
                                .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('user/followers.html', 
                         user=user, 
                         users=following_query, 
                         title='Following')

@user_bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    if user == current_user:
        return jsonify({'success': False, 'message': 'You cannot follow yourself'}), 400
    
    if current_user.is_following(user):
        return jsonify({'success': False, 'message': 'Already following this user'}), 400
    
    follow_obj = current_user.follow(user)
    if follow_obj:
        # Create notification
        Notification.create_notification(current_user, user, 'follow')
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'You are now following {username}',
            'followers_count': user.followers_count()
        })
    
    return jsonify({'success': False, 'message': 'Failed to follow user'}), 500

@user_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    if user == current_user:
        return jsonify({'success': False, 'message': 'You cannot unfollow yourself'}), 400
    
    if not current_user.is_following(user):
        return jsonify({'success': False, 'message': 'You are not following this user'}), 400
    
    if current_user.unfollow(user):
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'You unfollowed {username}',
            'followers_count': user.followers_count()
        })
    
    return jsonify({'success': False, 'message': 'Failed to unfollow user'}), 500
