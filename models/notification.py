from app import db
from datetime import datetime

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Notification types
    NOTIFICATION_TYPES = {
        'like': 'liked your post',
        'comment': 'commented on your post',
        'follow': 'started following you',
        'mention': 'mentioned you in a post'
    }
    
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    
    # Optional reference to related objects
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    post = db.relationship('Post', backref='notifications')
    comment = db.relationship('Comment', backref='notifications')
    
    @staticmethod
    def create_notification(sender, recipient, type, post=None, comment=None):
        if sender == recipient:
            return None  # Don't notify yourself
        
        message = f"{sender.username} {Notification.NOTIFICATION_TYPES.get(type, 'interacted with you')}"
        
        notification = Notification(
            sender_id=sender.id,
            recipient_id=recipient.id,
            type=type,
            message=message,
            post_id=post.id if post else None,
            comment_id=comment.id if comment else None
        )
        
        db.session.add(notification)
        return notification
    
    def mark_as_read(self):
        self.is_read = True
    
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
    
    def get_url(self):
        if self.post_id:
            return f"/post/{self.post_id}"
        elif self.type == 'follow':
            return f"/user/{self.sender.username}"
        return "/"
    
    def __repr__(self):
        return f'<Notification {self.type} from {self.sender.username} to {self.recipient.username}>'
