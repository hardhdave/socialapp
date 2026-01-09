from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models.post import Post
from models.comment import Comment
from models.like import Like
from models.notification import Notification
from utils.helpers import allowed_file, allowed_image_file, allowed_video_file, save_picture
import bleach
import os

post_bp = Blueprint('post', __name__)

@post_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        tags = request.form.get('tags', '').strip()
        location = request.form.get('location', '').strip()
        
        if not content:
            flash('Post content cannot be empty.', 'error')
            return render_template('post/create.html')
        
        # Clean the content
        content = bleach.clean(content, tags=['p', 'br', 'strong', 'em', 'u'], strip=True)
        
        # Create new post
        post = Post(
            content=content,
            location=location if location else None,
            user_id=current_user.id
        )
        
        # Handle tags
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            post.set_tags(tags_list)
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                if allowed_image_file(file.filename):
                    filename = save_picture(file, 'posts', f"post_{current_user.id}")
                    if filename:
                        post.image_filename = filename
                else:
                    flash('Invalid image file type. Allowed: png, jpg, jpeg, gif', 'error')
                    return render_template('post/create.html')
        
        # Handle video upload
        if 'video' in request.files:
            file = request.files['video']
            if file and file.filename:
                if allowed_video_file(file.filename):
                    filename = save_picture(file, 'posts', f"video_{current_user.id}", is_video=True)
                    if filename:
                        post.video_filename = filename
                else:
                    flash('Invalid video file type. Allowed: mp4, mov, avi', 'error')
                    return render_template('post/create.html')
        
        db.session.add(post)
        db.session.commit()
        
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('post/create.html')

@post_bp.route('/<int:post_id>')
def detail(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Increment views
    from sqlalchemy import text
    db.session.execute(text('UPDATE post SET views_count = views_count + 1 WHERE id = :post_id'), 
                      {'post_id': post_id})
    db.session.commit()
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['COMMENTS_PER_PAGE']
    
    comments = post.comments.filter_by(parent_id=None)\
                           .order_by(Comment.created_at.desc())\
                           .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('post/detail.html', post=post, comments=comments)

@post_bp.route('/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    post = Post.query.get_or_404(post_id)
    
    existing_like = post.get_like_by_user(current_user)
    
    if existing_like:
        # Unlike the post
        db.session.delete(existing_like)
        liked = False
        message = 'Post unliked'
    else:
        # Like the post
        like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        liked = True
        message = 'Post liked'
        
        # Create notification (only for likes, not unlikes)
        if post.author != current_user:
            Notification.create_notification(current_user, post.author, 'like', post=post)
    
    # Update likes count
    post.likes_count = post.likes.count()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'liked': liked,
        'likes_count': post.likes_count,
        'message': message
    })

@post_bp.route('/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    
    if not content:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400
    
    # Clean the content
    content = bleach.clean(content, tags=[], strip=True)
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post.id,
        parent_id=parent_id if parent_id else None
    )
    
    db.session.add(comment)
    
    # Update comments count
    post.comments_count = post.comments.count() + 1  # Add 1 for the new comment
    
    # Create notification
    if post.author != current_user:
        Notification.create_notification(current_user, post.author, 'comment', post=post, comment=comment)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Comment added successfully',
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'author': comment.author.username,
            'author_avatar': comment.author.get_profile_picture_url(),
            'time_ago': comment.time_ago(),
            'is_reply': comment.is_reply()
        },
        'comments_count': post.comments_count
    })

@post_bp.route('/<int:post_id>/delete', methods=['POST'])
@login_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.author != current_user:
        flash('You can only delete your own posts.', 'error')
        return redirect(url_for('post.detail', post_id=post_id))
    
    # Delete associated files
    if post.image_filename:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', post.image_filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
    
    if post.video_filename:
        video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', post.video_filename)
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except OSError:
            pass
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Your post has been deleted.', 'success')
    return redirect(url_for('main.index'))

@post_bp.route('/tag/<tag_name>')
def posts_by_tag(tag_name):
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']
    
    posts = Post.query.filter(Post.tags.contains(tag_name))\
                     .order_by(Post.created_at.desc())\
                     .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('main/index.html', posts=posts, tag=tag_name)
