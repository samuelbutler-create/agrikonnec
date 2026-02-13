from flask import request, Blueprint, jsonify, current_app
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_cors import cross_origin
from app.models.user import User
from app.models.message import Message
from app.extensions import db
from flask_restx import Namespace
import os

message_ns = Namespace('messages', description='User messages')

# Get CORS origins from environment
CORS_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000,http://localhost:5174,https://agrikonnect-frontend.vercel.app').split(',')]


@message_ns.route('/')
class SendMessage(Resource):
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        receiver_id = data.get('receiver_id')
        content = data.get('content')

        if not receiver_id or not content:
            return {'error': 'receiver_id and content required'}, 400

        if receiver_id == user_id:
            return {'error': 'Cannot send message to yourself'}, 400

        receiver = User.query.get(receiver_id)
        if not receiver:
            return {'error': 'Receiver not found'}, 404

        message = Message(sender_id=user_id, receiver_id=receiver_id, content=content)
        db.session.add(message)
        db.session.commit()

        return message.to_dict(), 201


@message_ns.route('/inbox')
class Inbox(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        messages = Message.query.filter_by(receiver_id=user_id).order_by(Message.created_at.desc()).all()
        return [m.to_dict() for m in messages], 200


@message_ns.route('/sent')
class SentMessages(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        messages = Message.query.filter_by(sender_id=user_id).order_by(Message.created_at.desc()).all()
        return [m.to_dict() for m in messages], 200


@message_ns.route('/<int:message_id>/read')
class MarkAsRead(Resource):
    @jwt_required()
    def patch(self, message_id):
        user_id = get_jwt_identity()
        message = Message.query.get_or_404(message_id)

        if message.receiver_id != user_id:
            return {'error': 'Forbidden'}, 403

        message.mark_as_read()
        db.session.commit()
        return message.to_dict(), 200


# Legacy Blueprint to support clients expecting /messages/* (non-API path)
messages_bp = Blueprint('messages', __name__, url_prefix='/messages')


@messages_bp.route('/', methods=['POST', 'OPTIONS'], strict_slashes=False)
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True)
def legacy_send_message():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        receiver_id = data.get('receiver_id')
        content = data.get('content')

        if not receiver_id or not content:
            return jsonify({'error': 'receiver_id and content required'}), 400

        if receiver_id == user_id:
            return jsonify({'error': 'Cannot send message to yourself'}), 400

        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({'error': 'Receiver not found'}), 404

        message = Message(sender_id=user_id, receiver_id=receiver_id, content=content)
        db.session.add(message)
        db.session.commit()
        
        # Create notification
        from app.models.notification import Notification
        sender = User.query.get(user_id)
        if sender:
            notification = Notification(
                user_id=receiver_id,
                type='message',
                title='New Message',
                message=f'{sender.first_name} {sender.last_name} sent you a message',
                link=f'/messages/{user_id}'
            )
            db.session.add(notification)
            db.session.commit()

        return jsonify(message.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 401


@messages_bp.route('/inbox', methods=['GET', 'OPTIONS'], strict_slashes=False)
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True)
def legacy_inbox():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        
        messages = Message.query.filter(
            db.or_(Message.sender_id == user_id, Message.receiver_id == user_id)
        ).order_by(Message.created_at.desc()).all()
        
        conversations = {}
        for msg in messages:
            other_user_id = msg.sender_id if msg.sender_id != user_id else msg.receiver_id
            if other_user_id not in conversations:
                conversations[other_user_id] = msg
        
        result = []
        for other_user_id, msg in conversations.items():
            if other_user_id == user_id:
                continue
                
            other_user = User.query.get(other_user_id)
            if other_user:
                result.append({
                    'user_id': other_user.id,
                    'username': f"{other_user.first_name} {other_user.last_name}",
                    'first_name': other_user.first_name,
                    'last_name': other_user.last_name,
                    'role': other_user.role,
                    'profile_image': other_user.profile_image,
                    'last_message': msg.content,
                    'last_message_time': msg.created_at.isoformat()
                })
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 401


@messages_bp.route('/sent', methods=['GET', 'OPTIONS'], strict_slashes=False)
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True)
@jwt_required()
def legacy_sent_messages():
    user_id = get_jwt_identity()
    messages = Message.query.filter_by(sender_id=user_id).order_by(Message.created_at.desc()).all()
    return jsonify([m.to_dict() for m in messages]), 200


@messages_bp.route('/<int:message_id>/read', methods=['PATCH', 'OPTIONS'], strict_slashes=False)
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True)
@jwt_required()
def legacy_mark_as_read(message_id):
    user_id = get_jwt_identity()
    message = Message.query.get_or_404(message_id)

    if message.receiver_id != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    message.mark_as_read()
    db.session.commit()
    return jsonify(message.to_dict()), 200


@messages_bp.route('/<int:other_user_id>', methods=['GET', 'OPTIONS'], strict_slashes=False)
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True)
def get_conversation_short(other_user_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        messages = Message.query.filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
            ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
        ).order_by(Message.created_at.asc()).all()
        
        result = []
        for msg in messages:
            msg_dict = msg.to_dict()
            msg_dict['is_own'] = msg.sender_id == user_id
            msg_dict['timestamp'] = msg.created_at.isoformat() if msg.created_at else None
            
            # Add sender name
            sender = User.query.get(msg.sender_id)
            if sender:
                msg_dict['sender_name'] = f"{sender.first_name} {sender.last_name}"
            
            result.append(msg_dict)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 401


@messages_bp.route('/conversation/<int:other_user_id>', methods=['GET', 'OPTIONS'], strict_slashes=False)
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True)
@jwt_required()
def get_conversation(other_user_id):
    user_id = get_jwt_identity()
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
    ).order_by(Message.created_at.asc()).all()
    return jsonify([m.to_dict() for m in messages]), 200


@messages_bp.route('/reply', methods=['POST', 'OPTIONS'], strict_slashes=False)
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True)
@jwt_required()
def reply_message():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    receiver_id = data.get('receiver_id')
    content = data.get('content')

    if not receiver_id or not content:
        return jsonify({'error': 'receiver_id and content required'}), 400

    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({'error': 'Receiver not found'}), 404

    message = Message(sender_id=user_id, receiver_id=receiver_id, content=content)
    db.session.add(message)
    db.session.commit()

    return jsonify(message.to_dict()), 201


@messages_bp.route('/typing', methods=['POST', 'OPTIONS'], strict_slashes=False)
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True)
def legacy_typing():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        other = data.get('other_user_id')
        # For now, just accept and return ok — frontend can poll for typing status or integrate websockets later
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 401


@messages_bp.route('/mark-read', methods=['POST', 'OPTIONS'], strict_slashes=False)
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True)
@jwt_required()
def legacy_mark_conversation_read():
    data = request.get_json() or {}
    other_user_id = data.get('other_user_id')
    user_id = get_jwt_identity()
    if not other_user_id:
        return jsonify({'error': 'other_user_id required'}), 400
    messages = Message.query.filter(
        ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
    ).all()
    for m in messages:
        if not m.is_read:
            m.is_read = True
    db.session.commit()
    return jsonify({'status': 'ok'}), 200


@messages_bp.route('/search-users', methods=['GET', 'OPTIONS'], strict_slashes=False)
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True)
@jwt_required()
def search_users():
    try:
        query = request.args.get('q', '').strip()
        user_id = get_jwt_identity()
        
        if not query:
            users = User.query.filter(User.id != user_id).limit(20).all()
        else:
            users = User.query.filter(
                db.or_(
                    User.first_name.ilike(f'%{query}%'),
                    User.last_name.ilike(f'%{query}%'),
                    User.email.ilike(f'%{query}%')
                )
            ).filter(User.id != user_id).limit(10).all()
        
        return jsonify([{
            'id': u.id,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'email': u.email,
            'role': u.role
        } for u in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
