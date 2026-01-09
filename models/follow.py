from app import db
from datetime import datetime

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Unique constraint to prevent duplicate follows
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='unique_follower_followed'),)
    
    def __repr__(self):
        return f'<Follow {self.follower.username} -> {self.followed.username}>'
