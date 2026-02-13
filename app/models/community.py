from ..extensions import db
from .base import BaseModel
from .follower import community_members

class Community(BaseModel):
    __tablename__ = 'communities'

    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    category = db.Column(db.String(50), index=True)
    
    # Relationships
    members = db.relationship('User', secondary=community_members, backref='communities', lazy='dynamic')

    # Constraints
    __table_args__ = (
        db.CheckConstraint("length(name) >= 1", name='community_name_not_empty'),
        db.CheckConstraint("length(name) <= 100", name='community_name_max_length'),
    )

    def to_dict(self, current_user_id=None, include_counts=True):
        base_dict = super().to_dict()
        data = {
            **base_dict,
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'category': self.category
        }
        
        # Include member counts and membership status if requested
        if include_counts:
            data['members_count'] = self.members.count()
            if current_user_id:
                data['is_member'] = self.members.filter_by(id=current_user_id).count() > 0
        
        return data

    def __repr__(self):
        return f'<Community {self.name}>'
