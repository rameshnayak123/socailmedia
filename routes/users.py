from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app import db
from models import User, Post, Follow, Notification
import re

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
def get_current_user_profile():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get user's posts
        posts = Post.query.filter_by(
            user_id=current_user_id, is_active=True
        ).order_by(Post.created_at.desc()).limit(12).all()

        return jsonify({
            'user': user.to_dict(include_email=True),
            'posts': [post.to_dict(user) for post in posts]
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch profile', 'details': str(e)}), 500

@users_bp.route('/profile', methods=['PUT'])
def update_profile():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name'][:100]

        if 'bio' in data:
            user.bio = data['bio'][:150]

        if 'website' in data:
            website = data['website']
            if website and not website.startswith(('http://', 'https://')):
                website = 'https://' + website
            user.website = website[:200] if website else None

        if 'phone_number' in data:
            user.phone_number = data['phone_number'][:20]

        if 'is_private' in data:
            user.is_private = bool(data['is_private'])

        if 'profile_picture' in data:
            user.profile_picture = data['profile_picture']

        db.session.commit()

        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict(include_email=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@users_bp.route('/<username>', methods=['GET'])
def get_user_profile(username):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        user = User.query.filter_by(username=username.lower(), is_active=True).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        current_user = User.query.get(current_user_id)
        is_following = current_user.is_following(user) if current_user else False
        is_own_profile = user.id == current_user_id

        # Check if profile is private and user is not following
        if user.is_private and not is_following and not is_own_profile:
            return jsonify({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'profile_picture': user.profile_picture,
                    'is_private': True,
                    'followers_count': user.get_follower_count(),
                    'following_count': user.get_following_count(),
                    'posts_count': user.get_posts_count(),
                    'is_verified': user.is_verified
                },
                'posts': [],
                'is_following': is_following,
                'is_own_profile': is_own_profile
            }), 200

        # Get user's posts
        posts = Post.query.filter_by(
            user_id=user.id, is_active=True
        ).order_by(Post.created_at.desc()).limit(12).all()

        return jsonify({
            'user': user.to_dict(),
            'posts': [post.to_dict(current_user) for post in posts],
            'is_following': is_following,
            'is_own_profile': is_own_profile
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch user profile', 'details': str(e)}), 500

@users_bp.route('/<int:user_id>/follow', methods=['POST'])
def follow_user(user_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        if current_user_id == user_id:
            return jsonify({'error': 'Cannot follow yourself'}), 400

        user_to_follow = User.query.filter_by(id=user_id, is_active=True).first()
        if not user_to_follow:
            return jsonify({'error': 'User not found'}), 404

        current_user = User.query.get(current_user_id)

        if current_user.is_following(user_to_follow):
            return jsonify({'error': 'Already following this user'}), 400

        current_user.follow(user_to_follow)

        # Create notification
        notification = Notification(
            user_id=user_id,
            type='follow',
            title='New Follower',
            message=f'{current_user.username} started following you',
            action_user_id=current_user_id
        )
        db.session.add(notification)

        db.session.commit()

        return jsonify({
            'message': 'Successfully followed user',
            'is_following': True,
            'followers_count': user_to_follow.get_follower_count()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to follow user', 'details': str(e)}), 500

@users_bp.route('/<int:user_id>/unfollow', methods=['POST'])
def unfollow_user(user_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        if current_user_id == user_id:
            return jsonify({'error': 'Cannot unfollow yourself'}), 400

        user_to_unfollow = User.query.filter_by(id=user_id, is_active=True).first()
        if not user_to_unfollow:
            return jsonify({'error': 'User not found'}), 404

        current_user = User.query.get(current_user_id)

        if not current_user.is_following(user_to_unfollow):
            return jsonify({'error': 'Not following this user'}), 400

        current_user.unfollow(user_to_unfollow)
        db.session.commit()

        return jsonify({
            'message': 'Successfully unfollowed user',
            'is_following': False,
            'followers_count': user_to_unfollow.get_follower_count()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to unfollow user', 'details': str(e)}), 500

@users_bp.route('/search', methods=['GET'])
def search_users():
    try:
        verify_jwt_in_request()

        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        if not query or len(query) < 2:
            return jsonify({'error': 'Query must be at least 2 characters long'}), 400

        # Search by username and full name
        users_query = User.query.filter(
            (User.username.ilike(f'%{query}%')) | 
            (User.full_name.ilike(f'%{query}%')),
            User.is_active == True
        ).order_by(User.username)

        users = users_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'has_next': users.has_next,
            'has_prev': users.has_prev,
            'page': page,
            'pages': users.pages,
            'total': users.total,
            'query': query
        }), 200

    except Exception as e:
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500

@users_bp.route('/suggestions', methods=['GET'])
def get_user_suggestions():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # Maximum 50 suggestions

        # Get users not followed by current user
        following_ids = db.session.query(Follow.followed_id).filter_by(follower_id=current_user_id).all()
        following_ids = [id[0] for id in following_ids] + [current_user_id]

        # Get suggested users (users with most followers not currently followed)
        suggested_users = User.query.filter(
            ~User.id.in_(following_ids),
            User.is_active == True
        ).order_by(User.created_at.desc()).limit(limit).all()

        return jsonify({
            'suggestions': [user.to_dict() for user in suggested_users]
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch suggestions', 'details': str(e)}), 500

@users_bp.route('/<int:user_id>/followers', methods=['GET'])
def get_followers(user_id):
    try:
        verify_jwt_in_request()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        user = User.query.filter_by(id=user_id, is_active=True).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        followers_query = db.session.query(User).join(
            Follow, User.id == Follow.follower_id
        ).filter(Follow.followed_id == user_id).order_by(Follow.created_at.desc())

        followers = followers_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'followers': [user.to_dict() for user in followers.items],
            'has_next': followers.has_next,
            'has_prev': followers.has_prev,
            'page': page,
            'pages': followers.pages,
            'total': followers.total
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch followers', 'details': str(e)}), 500

@users_bp.route('/<int:user_id>/following', methods=['GET'])
def get_following(user_id):
    try:
        verify_jwt_in_request()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        user = User.query.filter_by(id=user_id, is_active=True).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        following_query = db.session.query(User).join(
            Follow, User.id == Follow.followed_id
        ).filter(Follow.follower_id == user_id).order_by(Follow.created_at.desc())

        following = following_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'following': [user.to_dict() for user in following.items],
            'has_next': following.has_next,
            'has_prev': following.has_prev,
            'page': page,
            'pages': following.pages,
            'total': following.total
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch following', 'details': str(e)}), 500
