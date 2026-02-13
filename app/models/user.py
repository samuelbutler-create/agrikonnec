from datetime import datetime
from ..extensions import db
from .base import BaseModel
from .follower import followers

class User(BaseModel):
    __tablename__ = 'users'

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='farmer',
                     server_default='farmer')
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    profile_image = db.Column(db.String(255))
    cover_image = db.Column(db.String(255))
    farm_size = db.Column(db.String(50))
    crops = db.Column(db.String(255))
    is_public = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False,
                          server_default='true')
    
    # Expert-specific fields
    title = db.Column(db.String(100))  # e.g., "Agricultural Specialist"
    specialties = db.Column(db.JSON)  # List of specialties
    is_verified = db.Column(db.Boolean, default=False)

    # Password reset fields
    password_reset_token = db.Column(db.String(255), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)

    # Constraints
    __table_args__ = (
        db.CheckConstraint("role IN ('farmer', 'expert')", name='valid_role'),
        db.CheckConstraint("length(first_name) >= 1", name='first_name_not_empty'),
        db.CheckConstraint("length(last_name) >= 1", name='last_name_not_empty'),
        db.CheckConstraint("length(email) >= 3", name='email_min_length'),
    )

    # Relationships
    posts = db.relationship('Post', foreign_keys='Post.author_id', lazy=True,
                        cascade='all, delete-orphan', overlaps="authored_posts")
    comments = db.relationship('Comment', foreign_keys='Comment.author_id', lazy=True,
                            cascade='all, delete-orphan')
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id',
                                   backref='sender', lazy=True,
                                   cascade='all, delete-orphan')
    messages_received = db.relationship('Message', foreign_keys='Message.receiver_id',
                                       backref='receiver', lazy=True,
                                       cascade='all, delete-orphan')
    
    # Follower relationships
    following = db.relationship(
        'User', secondary=followers,
        primaryjoin='User.id == followers.c.follower_id',
        secondaryjoin='User.id == followers.c.followed_id',
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    def to_dict(self, include_stats=False, current_user_id=None):
        base_dict = super().to_dict()
        
        # Helper to construct full URL for images
        def get_full_url(path):
            if not path:
                return None
            if path.startswith('http'):
                return path
            # Return path as-is, frontend will handle it
            return path
        
        data = {
            **base_dict,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'bio': self.bio,
            'location': self.location,
            'phone': self.phone,
            'profile_image': get_full_url(self.profile_image),
            'cover_image': get_full_url(self.cover_image),
            'farm_size': self.farm_size,
            'crops': self.crops,
            'is_public': self.is_public,
            'is_active': self.is_active,
            'posts_count': len(self.posts) if hasattr(self, 'posts') else 0,
            'communities_count': 0,
        }
        
        if self.role == 'expert':
            data.update({
                'title': self.title,
                'specialties': self.specialties or [],
                'is_verified': self.is_verified
            })
        
        if include_stats:
            from sqlalchemy import select, func
            data.update({
                'followers_count': db.session.scalar(
                    select(func.count()).select_from(followers).where(followers.c.followed_id == self.id)
                ) or 0,
                'following_count': db.session.scalar(
                    select(func.count()).select_from(followers).where(followers.c.follower_id == self.id)
                ) or 0,
                'posts_count': len(self.posts)
            })
        
        if current_user_id:
            from sqlalchemy import select, func
            data['is_following'] = db.session.scalar(
                select(func.count()).select_from(followers).where(
                    followers.c.followed_id == self.id,
                    followers.c.follower_id == current_user_id
                )
            ) > 0
        
        return data
    
    def to_expert_dict(self, current_user_id=None):
        """Convert expert user to frontend-compatible format"""
        from sqlalchemy import select, func
        
        followers_count = db.session.scalar(
            select(func.count()).select_from(followers).where(followers.c.followed_id == self.id)
        ) or 0
        
        is_following = False
        if current_user_id:
            is_following = db.session.scalar(
                select(func.count()).select_from(followers).where(
                    followers.c.followed_id == self.id,
                    followers.c.follower_id == current_user_id
                )
            ) > 0
        
        return {
            'id': self.id,
            'name': self.full_name,
            'avatar_url': self.profile_image,
            'title': self.title or 'Agricultural Expert',
            'location': self.location,
            'specialties': self.specialties or [],
            'followers': followers_count,
            'posts': len(self.posts),
            'isVerified': self.is_verified,
            'is_following': is_following,
            'bio': self.bio
        }

    @property
    def full_name(self):
        """Return the user's full name"""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<User {self.email}>'
