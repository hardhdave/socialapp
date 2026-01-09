from app import db
from datetime import datetime
from sqlalchemy import func

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # Media files
    image_filename = db.Column(db.String(200), nullable=True)
    video_filename = db.Column(db.String(200), nullable=True)
    
    # Metadata
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    location = db.Column(db.String(200), nullable=True)
    
    # Engagement metrics
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def get_image_url(self):
        if self.image_filename:
            return f'/static/uploads/posts/{self.image_filename}'
        return None

    def get_video_url(self):
        if self.video_filename:
            return f'/static/uploads/posts/{self.video_filename}'
        return None

    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def set_tags(self, tags_list):
        if tags_list:
            self.tags = ', '.join(tags_list)
        else:
            self.tags = None

    def is_liked_by(self, user):
        if user.is_anonymous:
            return False
        return self.likes.filter_by(user_id=user.id).first() is not None

    def get_like_by_user(self, user):
        return self.likes.filter_by(user_id=user.id).first()

    def update_likes_count(self):
        self.likes_count = self.likes.count()

    def update_comments_count(self):
        self.comments_count = self.comments.count()

    def increment_views(self):
        self.views_count = Post.views_count + 1

    def time_ago(self):
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"

    @staticmethod
    def get_trending_posts(limit=10):
        # Simple trending algorithm based on recent engagement
        from datetime import datetime, timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)
        
        return Post.query.filter(Post.created_at >= recent_date)\
                        .order_by((Post.likes_count + Post.comments_count).desc())\
                        .limit(limit).all()

    @staticmethod
    def get_trending_tags(limit=10):
        # Get most used tags from recent posts
        from datetime import datetime, timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)
        
        posts = Post.query.filter(Post.created_at >= recent_date, Post.tags.isnot(None)).all()
        tag_count = {}
        
        for post in posts:
            tags = post.get_tags_list()
            for tag in tags:
                tag_lower = tag.lower()
                tag_count[tag_lower] = tag_count.get(tag_lower, 0) + 1
        
        return sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:limit]

    def __repr__(self):
        return f'<Post {self.id} by {self.author.username}>'
