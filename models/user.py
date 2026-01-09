from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile information
    full_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True, default='default-avatar.png')
    cover_photo = db.Column(db.String(200), nullable=True)
    
    # Account settings
    is_private = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # Added for decorators
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Following relationships - Fixed foreign_keys references
    following = db.relationship('Follow', 
                              foreign_keys='Follow.follower_id',
                              backref='follower', 
                              lazy='dynamic',
                              cascade='all, delete-orphan')
    followers = db.relationship('Follow', 
                               foreign_keys='Follow.followed_id',
                               backref='followed', 
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    
    # Notifications - Fixed foreign_keys references
    notifications_sent = db.relationship('Notification', 
                                       foreign_keys='Notification.sender_id',
                                       backref='sender', 
                                       lazy='dynamic',
                                       cascade='all, delete-orphan')
    notifications_received = db.relationship('Notification', 
                                           foreign_keys='Notification.recipient_id',
                                           backref='recipient', 
                                           lazy='dynamic',
                                           cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def follow(self, user):
        if not self.is_following(user) and user != self:
            from models.follow import Follow  # Import here to avoid circular import
            follow = Follow(follower_id=self.id, followed_id=user.id)
            db.session.add(follow)
            return follow
        return None

    def unfollow(self, user):
        follow = self.following.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            return True
        return False

    def is_following(self, user):
        return self.following.filter_by(followed_id=user.id).first() is not None

    def followers_count(self):
        return self.followers.count()

    def following_count(self):
        return self.following.count()

    def posts_count(self):
        return self.posts.count()

    def get_profile_picture_url(self):
        if self.profile_picture and self.profile_picture != 'default-avatar.png':
            return f'/static/uploads/profiles/{self.profile_picture}'
        return '/static/images/default-avatar.png'

    def get_followed_posts(self):
        from models.post import Post  # Import here to avoid circular import
        from models.follow import Follow
        followed = Post.query.join(Follow, Follow.followed_id == Post.user_id)\
                           .filter(Follow.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.created_at.desc())

    def unread_notifications_count(self):
        return self.notifications_received.filter_by(is_read=False).count()

    def __repr__(self):
        return f'<User {self.username}>'

