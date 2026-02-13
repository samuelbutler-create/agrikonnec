from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db

notification_ns = Namespace('notifications', description='Notification operations')

@notification_ns.route('')
class NotificationList(Resource):
    @jwt_required()
    def get(self):
        """Get notifications for current user"""
        from ..models.notification import Notification
        user_id = int(get_jwt_identity())
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false')
        
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only == 'true':
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(Notification.created_at.desc()).limit(per_page).offset((page - 1) * per_page).all()
        total = query.count()
        unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        
        return {
            'notifications': [n.to_dict() for n in notifications],
            'total': total,
            'unread_count': unread_count
        }, 200

# Specific routes must come first (before parameterized routes)
@notification_ns.route('/read-all')
class NotificationReadAll(Resource):
    @jwt_required()
    def put(self):
        """Mark all notifications as read"""
        from ..models.notification import Notification
        user_id = int(get_jwt_identity())
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return {'message': 'All notifications marked as read'}, 200

@notification_ns.route('/unread-count')
class NotificationUnreadCount(Resource):
    @jwt_required(optional=True)
    def get(self):
        """Get unread notification count (returns 0 if unauthenticated)"""
        from ..models.notification import Notification
        user_identity = get_jwt_identity()
        if not user_identity:
            return {'count': 0}, 200
        user_id = int(user_identity)
        count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        return {'count': count}, 200

# Parameterized routes come after specific routes
@notification_ns.route('/<int:notification_id>/read')
class NotificationRead(Resource):
    @jwt_required()
    def put(self, notification_id):
        """Mark notification as read"""
        from ..models.notification import Notification
        notification = Notification.query.get_or_404(notification_id)
        notification.is_read = True
        db.session.commit()
        return {'message': 'Marked as read'}, 200

@notification_ns.route('/<int:notification_id>')
class NotificationDelete(Resource):
    @jwt_required()
    def delete(self, notification_id):
        """Delete a notification"""
        from ..models.notification import Notification
        notification = Notification.query.get_or_404(notification_id)
        db.session.delete(notification)
        db.session.commit()
        return {'message': 'Notification deleted'}, 200
