from ..extensions import db
from .base import BaseModel

class Post(BaseModel):
    __tablename__ = 'posts'

    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Constraints
    __table_args__ = (
        db.CheckConstraint("length(title) >= 1", name='post_title_not_empty'),
        db.CheckConstraint("length(content) >= 1", name='post_content_not_empty'),
        db.CheckConstraint("length(title) <= 200", name='post_title_max_length'),
    )

    # Relationships
    author = db.relationship('User', foreign_keys=[author_id], backref='authored_posts', overlaps="posts")
    comments = db.relationship('Comment', foreign_keys='Comment.post_id', lazy=True,
                            cascade='all, delete-orphan', overlaps="post")
    likes = db.relationship('Like', foreign_keys='Like.post_id', lazy=True,
                            cascade='all, delete-orphan')

    def to_dict(self, current_user_id=None):
        base_dict = super().to_dict()
        like_count = len(self.likes) if hasattr(self, 'likes') else 0
        is_liked = False
        
        if current_user_id and hasattr(self, 'likes'):
            is_liked = any(like.user_id == current_user_id for like in self.likes)
        
        return {
            **base_dict,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'author_id': self.author_id,
            'author': {
                'id': self.author.id,
                'first_name': getattr(self.author, 'first_name', None),
                'last_name': getattr(self.author, 'last_name', None),
                'name': f"{getattr(self.author, 'first_name', '')} {getattr(self.author, 'last_name', '')}".strip() or None
            } if getattr(self, 'author', None) else None,
            'likeCount': like_count,
            'commentCount': len(self.comments) if hasattr(self, 'comments') else 0,
            'isLiked': is_liked,
        }

    @property
    def comment_count(self):
        """Return the number of comments on this post"""
        return len(self.comments)

    def __repr__(self):
        return f'<Post {self.title[:30]}...>'
