from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Notification
import os
from datetime import datetime, timedelta

app = Flask(__name__)
# Use SQLite for local development, PostgreSQL for production
db_url = os.getenv('DATABASE_URL', 'sqlite:///notifications.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'notifications'}

@app.route('/api/notifications', methods=['POST'])
def create_notification():
    """Create a new notification"""
    data = request.json
    
    notification = Notification(
        user_id=data['user_id'],
        type=data['type'],
        title=data['title'],
        message=data['message'],
        link=data.get('link'),
        actor_id=data.get('actor_id'),
        actor_name=data.get('actor_name'),
        actor_avatar=data.get('actor_avatar')
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return jsonify(notification.to_dict()), 201

@app.route('/api/notifications/<int:user_id>', methods=['GET'])
def get_notifications(user_id):
    """Get notifications for a user"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = Notification.query.filter_by(user_id=user_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    query = query.order_by(Notification.created_at.desc())
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'notifications': [n.to_dict() for n in paginated.items],
        'total': paginated.total,
        'page': page,
        'pages': paginated.pages,
        'unread_count': Notification.query.filter_by(user_id=user_id, is_read=False).count()
    })

@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_as_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    notification.is_read = True
    db.session.commit()
    
    return jsonify(notification.to_dict())

@app.route('/api/notifications/<int:user_id>/read-all', methods=['PUT'])
def mark_all_as_read(user_id):
    """Mark all notifications as read for a user"""
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'message': 'All notifications marked as read'})

@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a notification"""
    notification = Notification.query.get_or_404(notification_id)
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification deleted'})

@app.route('/api/notifications/<int:user_id>/unread-count', methods=['GET'])
def get_unread_count(user_id):
    """Get unread notification count"""
    count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({'count': count})

@app.route('/api/notifications/<int:user_id>/clear-old', methods=['DELETE'])
def clear_old_notifications(user_id):
    """Clear notifications older than 30 days"""
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    deleted = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.created_at < thirty_days_ago,
        Notification.is_read == True
    ).delete()
    db.session.commit()
    
    return jsonify({'message': f'{deleted} old notifications cleared'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
