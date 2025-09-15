from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app import db
from models import User, Message
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/conversations', methods=['GET'])
def get_conversations():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Get latest message for each conversation
        subquery = db.session.query(
            db.func.greatest(Message.sender_id, Message.recipient_id).label('user1'),
            db.func.least(Message.sender_id, Message.recipient_id).label('user2'),
            db.func.max(Message.id).label('latest_message_id')
        ).filter(
            (Message.sender_id == current_user_id) | (Message.recipient_id == current_user_id)
        ).group_by('user1', 'user2').subquery()

        conversations_query = db.session.query(Message).join(
            subquery, Message.id == subquery.c.latest_message_id
        ).order_by(Message.created_at.desc())

        conversations = conversations_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        result = []
        for message in conversations.items:
            # Determine the other user in the conversation
            other_user_id = message.recipient_id if message.sender_id == current_user_id else message.sender_id
            other_user = User.query.get(other_user_id)

            # Count unread messages
            unread_count = Message.query.filter_by(
                sender_id=other_user_id,
                recipient_id=current_user_id,
                is_read=False
            ).count()

            result.append({
                'conversation_id': f"{min(current_user_id, other_user_id)}_{max(current_user_id, other_user_id)}",
                'other_user': other_user.to_dict(),
                'last_message': message.to_dict(),
                'unread_count': unread_count
            })

        return jsonify({
            'conversations': result,
            'has_next': conversations.has_next,
            'has_prev': conversations.has_prev,
            'page': page,
            'pages': conversations.pages,
            'total': conversations.total
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch conversations', 'details': str(e)}), 500

@messages_bp.route('/conversation/<int:user_id>', methods=['GET'])
def get_conversation_messages(user_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        # Check if the other user exists
        other_user = User.query.filter_by(id=user_id, is_active=True).first()
        if not other_user:
            return jsonify({'error': 'User not found'}), 404

        # Get messages between the two users
        messages_query = Message.query.filter(
            ((Message.sender_id == current_user_id) & (Message.recipient_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.recipient_id == current_user_id))
        ).order_by(Message.created_at.desc())

        messages = messages_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Mark messages as read
        Message.query.filter_by(
            sender_id=user_id,
            recipient_id=current_user_id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()

        # Reverse the messages list to show chronological order
        messages_list = [message.to_dict() for message in reversed(messages.items)]

        return jsonify({
            'messages': messages_list,
            'other_user': other_user.to_dict(),
            'has_next': messages.has_next,
            'has_prev': messages.has_prev,
            'page': page,
            'pages': messages.pages,
            'total': messages.total
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch messages', 'details': str(e)}), 500

@messages_bp.route('/send', methods=['POST'])
def send_message():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        data = request.get_json()
        recipient_id = data.get('recipient_id')
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')

        if not recipient_id or not content:
            return jsonify({'error': 'Recipient ID and content are required'}), 400

        if current_user_id == recipient_id:
            return jsonify({'error': 'Cannot send message to yourself'}), 400

        # Check if recipient exists
        recipient = User.query.filter_by(id=recipient_id, is_active=True).first()
        if not recipient:
            return jsonify({'error': 'Recipient not found'}), 404

        # Create message
        new_message = Message(
            sender_id=current_user_id,
            recipient_id=recipient_id,
            content=content[:1000],  # Limit message length
            message_type=message_type
        )

        db.session.add(new_message)
        db.session.commit()

        return jsonify({
            'message': 'Message sent successfully',
            'message_data': new_message.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to send message', 'details': str(e)}), 500

@messages_bp.route('/<int:message_id>/read', methods=['PUT'])
def mark_message_read(message_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        message = Message.query.filter_by(
            id=message_id, recipient_id=current_user_id
        ).first()

        if not message:
            return jsonify({'error': 'Message not found'}), 404

        message.is_read = True
        db.session.commit()

        return jsonify({'message': 'Message marked as read'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to mark message as read', 'details': str(e)}), 500

@messages_bp.route('/unread-count', methods=['GET'])
def get_unread_count():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        unread_count = Message.query.filter_by(
            recipient_id=current_user_id, is_read=False
        ).count()

        return jsonify({'unread_count': unread_count}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch unread count', 'details': str(e)}), 500

@messages_bp.route('/conversation/<int:user_id>/delete', methods=['DELETE'])
def delete_conversation(user_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        # Delete all messages between the two users
        Message.query.filter(
            ((Message.sender_id == current_user_id) & (Message.recipient_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.recipient_id == current_user_id))
        ).delete()

        db.session.commit()

        return jsonify({'message': 'Conversation deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete conversation', 'details': str(e)}), 500
