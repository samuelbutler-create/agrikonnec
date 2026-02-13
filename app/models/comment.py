from ..extensions import db
from .base import BaseModel

class Comment(BaseModel):
    __tablename__ = 'comments'

    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=True, index=True)

    # Associations and relationships
    author = db.relationship('User', foreign_keys=[author_id], overlaps="comments")
    post = db.relationship('Post', foreign_keys=[post_id], overlaps="comments")
    community = db.relationship('Community', foreign_keys=[community_id], backref='community_messages')

    # Constraints and indexes for performance and data integrity
    __table_args__ = (
        db.CheckConstraint("length(content) >= 1", name='comment_content_not_empty'),
        db.Index('idx_comment_post_author', 'post_id', 'author_id'),
    )

    def to_dict(self):
        base_dict = super().to_dict()
        return {
            **base_dict,
            'content': self.content,
            'post_id': self.post_id,
            'author_id': self.author_id,
            'author': {
                'id': self.author.id,
                'first_name': self.author.first_name,
                'last_name': self.author.last_name,
                'name': f"{self.author.first_name} {self.author.last_name}".strip(),
                'profile_image': self.author.profile_image,
            } if self.author else None,
        }

    # String representation for debugging
    def __repr__(self):
        return f'<Comment {self.content[:30]}...>'