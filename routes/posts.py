from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
from models import User, Post, Like, Comment, Follow
from ml_algorithms import RecommendationEngine, ContentModerator, ImageProcessor
import os
from datetime import datetime
import uuid

posts_bp = Blueprint('posts', __name__)
content_moderator = ContentModerator()
image_processor = ImageProcessor()

@posts_bp.route('/', methods=['GET'])
def get_posts():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Get posts from followed users and own posts
        following_ids = db.session.query(Follow.followed_id).filter_by(follower_id=current_user_id).all()
        following_ids = [id[0] for id in following_ids] + [current_user_id]

        posts_query = Post.query.filter(
            Post.user_id.in_(following_ids),
            Post.is_active == True
        ).order_by(Post.created_at.desc())

        posts = posts_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        current_user = User.query.get(current_user_id)

        return jsonify({
            'posts': [post.to_dict(current_user) for post in posts.items],
            'has_next': posts.has_next,
            'has_prev': posts.has_prev,
            'page': page,
            'pages': posts.pages,
            'total': posts.total
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch posts', 'details': str(e)}), 500

@posts_bp.route('/', methods=['POST'])
def create_post():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        data = request.get_json()

        if not data.get('image_url'):
            return jsonify({'error': 'Image URL is required'}), 400

        caption = data.get('caption', '')
        location = data.get('location', '')
        image_url = data['image_url']

        # Moderate content
        if caption:
            moderation_result = content_moderator.moderate_text(caption)
            if not moderation_result['is_appropriate']:
                return jsonify({
                    'error': 'Content violates community guidelines',
                    'issues': moderation_result['issues']
                }), 400

        # Analyze image
        image_analysis = image_processor.analyze_image(image_url)
        if not image_analysis.get('is_valid', True):
            return jsonify({'error': 'Invalid image'}), 400

        # Create post
        new_post = Post(
            user_id=current_user_id,
            caption=caption[:2200],  # Limit caption length
            image_url=image_url,
            location=location
        )

        db.session.add(new_post)
        db.session.commit()

        # Get suggested hashtags
        suggested_hashtags = image_processor.suggest_hashtags(image_url, caption)

        current_user = User.query.get(current_user_id)

        return jsonify({
            'message': 'Post created successfully',
            'post': new_post.to_dict(current_user),
            'suggested_hashtags': suggested_hashtags,
            'image_analysis': image_analysis
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create post', 'details': str(e)}), 500

@posts_bp.route('/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        post = Post.query.filter_by(id=post_id, is_active=True).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        current_user = User.query.get(current_user_id)

        # Get comments
        comments = Comment.query.filter_by(
            post_id=post_id, is_active=True, parent_id=None
        ).order_by(Comment.created_at.desc()).limit(20).all()

        return jsonify({
            'post': post.to_dict(current_user),
            'comments': [comment.to_dict() for comment in comments]
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch post', 'details': str(e)}), 500

@posts_bp.route('/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        post = Post.query.filter_by(id=post_id, is_active=True).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        # Check if already liked
        existing_like = Like.query.filter_by(
            user_id=current_user_id, post_id=post_id
        ).first()

        if existing_like:
            # Unlike
            db.session.delete(existing_like)
            action = 'unliked'
        else:
            # Like
            new_like = Like(user_id=current_user_id, post_id=post_id)
            db.session.add(new_like)
            action = 'liked'

            # Create notification for post author (if not liking own post)
            if post.user_id != current_user_id:
                from models import Notification
                current_user = User.query.get(current_user_id)
                notification = Notification(
                    user_id=post.user_id,
                    type='like',
                    title='New Like',
                    message=f'{current_user.username} liked your post',
                    action_user_id=current_user_id,
                    related_post_id=post_id
                )
                db.session.add(notification)

        db.session.commit()

        return jsonify({
            'message': f'Post {action} successfully',
            'likes_count': post.get_likes_count(),
            'is_liked': action == 'liked'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to {action if "action" in locals() else "like"} post'}), 500

@posts_bp.route('/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        data = request.get_json()
        text = data.get('text', '').strip()
        parent_id = data.get('parent_id')

        if not text:
            return jsonify({'error': 'Comment text is required'}), 400

        post = Post.query.filter_by(id=post_id, is_active=True).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        # Moderate comment
        moderation_result = content_moderator.moderate_text(text)
        if not moderation_result['is_appropriate']:
            return jsonify({
                'error': 'Comment violates community guidelines',
                'issues': moderation_result['issues']
            }), 400

        # Check if parent comment exists (for replies)
        if parent_id:
            parent_comment = Comment.query.filter_by(
                id=parent_id, post_id=post_id, is_active=True
            ).first()
            if not parent_comment:
                return jsonify({'error': 'Parent comment not found'}), 404

        # Create comment
        new_comment = Comment(
            user_id=current_user_id,
            post_id=post_id,
            text=text[:500],  # Limit comment length
            parent_id=parent_id
        )

        db.session.add(new_comment)

        # Create notification for post author (if not commenting on own post)
        if post.user_id != current_user_id:
            from models import Notification
            current_user = User.query.get(current_user_id)
            notification = Notification(
                user_id=post.user_id,
                type='comment',
                title='New Comment',
                message=f'{current_user.username} commented on your post',
                action_user_id=current_user_id,
                related_post_id=post_id
            )
            db.session.add(notification)

        db.session.commit()

        return jsonify({
            'message': 'Comment added successfully',
            'comment': new_comment.to_dict(),
            'comments_count': post.get_comments_count()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add comment', 'details': str(e)}), 500

@posts_bp.route('/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    try:
        verify_jwt_in_request()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        post = Post.query.filter_by(id=post_id, is_active=True).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        comments_query = Comment.query.filter_by(
            post_id=post_id, is_active=True, parent_id=None
        ).order_by(Comment.created_at.desc())

        comments = comments_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'comments': [comment.to_dict() for comment in comments.items],
            'has_next': comments.has_next,
            'has_prev': comments.has_prev,
            'page': page,
            'pages': comments.pages,
            'total': comments.total
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch comments', 'details': str(e)}), 500

@posts_bp.route('/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        post = Post.query.filter_by(
            id=post_id, user_id=current_user_id, is_active=True
        ).first()

        if not post:
            return jsonify({'error': 'Post not found or unauthorized'}), 404

        # Soft delete
        post.is_active = False
        db.session.commit()

        return jsonify({'message': 'Post deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete post', 'details': str(e)}), 500

@posts_bp.route('/explore', methods=['GET'])
def explore_posts():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Get posts from users not followed by current user
        following_ids = db.session.query(Follow.followed_id).filter_by(follower_id=current_user_id).all()
        following_ids = [id[0] for id in following_ids] + [current_user_id]

        posts_query = Post.query.filter(
            ~Post.user_id.in_(following_ids),
            Post.is_active == True
        ).order_by(Post.created_at.desc())

        posts = posts_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        current_user = User.query.get(current_user_id)

        return jsonify({
            'posts': [post.to_dict(current_user) for post in posts.items],
            'has_next': posts.has_next,
            'has_prev': posts.has_prev,
            'page': page,
            'pages': posts.pages,
            'total': posts.total
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch explore posts', 'details': str(e)}), 500
