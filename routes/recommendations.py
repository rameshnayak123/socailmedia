from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app import db
from models import User, Post, Like, Comment, Follow
from ml_algorithms import RecommendationEngine, EngagementPredictor
import logging

recommendations_bp = Blueprint('recommendations', __name__)
logger = logging.getLogger(__name__)

recommendation_engine = RecommendationEngine()
engagement_predictor = EngagementPredictor()

@recommendations_bp.route('/posts', methods=['GET'])
def get_post_recommendations():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        num_recommendations = request.args.get('count', 10, type=int)
        num_recommendations = min(num_recommendations, 50)  # Limit to 50

        # Get user data
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # Get all posts data
        posts = Post.query.filter(Post.is_active == True).all()
        posts_data = []

        for post in posts:
            posts_data.append({
                'id': post.id,
                'user_id': post.user_id,
                'caption': post.caption or '',
                'location': post.location or '',
                'likes_count': post.get_likes_count(),
                'comments_count': post.get_comments_count(),
                'created_at': post.created_at.isoformat()
            })

        # Get interaction data
        interactions_data = []

        # Add likes as interactions
        likes = Like.query.all()
        for like in likes:
            interactions_data.append({
                'user_id': like.user_id,
                'post_id': like.post_id,
                'rating': 1,
                'type': 'like'
            })

        # Add comments as interactions (higher weight)
        comments = Comment.query.filter(Comment.is_active == True).all()
        for comment in comments:
            interactions_data.append({
                'user_id': comment.user_id,
                'post_id': comment.post_id,
                'rating': 2,
                'type': 'comment'
            })

        # Get user preferences
        user_preferences = {
            'bio': current_user.bio or '',
            'interests': [],  # Could be extracted from bio or user behavior
            'location': '',  # Could be derived from posts location data
        }

        # Generate recommendations using hybrid approach
        recommended_post_ids = recommendation_engine.hybrid_recommendations(
            user_id=current_user_id,
            posts_data=posts_data,
            interactions_data=interactions_data,
            user_preferences=user_preferences,
            num_recommendations=num_recommendations
        )

        # Get the actual post objects
        recommended_posts = []
        for post_id in recommended_post_ids:
            post = Post.query.get(post_id)
            if post and post.is_active:
                recommended_posts.append(post.to_dict(current_user))

        # If not enough recommendations, fill with trending posts
        if len(recommended_posts) < num_recommendations:
            trending_ids = recommendation_engine.get_trending_posts(
                posts_data, num_recommendations - len(recommended_posts)
            )

            for post_id in trending_ids:
                if post_id not in recommended_post_ids:
                    post = Post.query.get(post_id)
                    if post and post.is_active:
                        recommended_posts.append(post.to_dict(current_user))

        logger.info(f'Generated {len(recommended_posts)} recommendations for user {current_user_id}')

        return jsonify({
            'recommendations': recommended_posts[:num_recommendations],
            'algorithm': 'hybrid',
            'count': len(recommended_posts[:num_recommendations])
        }), 200

    except Exception as e:
        logger.error(f'Error generating post recommendations: {str(e)}')
        return jsonify({'error': 'Failed to generate recommendations', 'details': str(e)}), 500

@recommendations_bp.route('/users', methods=['GET'])
def get_user_recommendations():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        num_recommendations = request.args.get('count', 10, type=int)
        num_recommendations = min(num_recommendations, 50)  # Limit to 50

        # Get users not followed by current user
        following_ids = db.session.query(Follow.followed_id).filter_by(follower_id=current_user_id).all()
        following_ids = [id[0] for id in following_ids] + [current_user_id]

        # Get all users data for clustering
        all_users = User.query.filter(User.is_active == True).all()
        users_data = []

        for user in all_users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'bio': user.bio or '',
                'followers_count': user.get_follower_count(),
                'following_count': user.get_following_count(),
                'posts_count': user.get_posts_count()
            })

        # Get interaction data for clustering
        interactions_data = []
        likes = Like.query.all()
        for like in likes:
            interactions_data.append({
                'user_id': like.user_id,
                'post_id': like.post_id,
                'type': 'like'
            })

        # Perform user clustering
        user_clusters = recommendation_engine.user_clustering(users_data, interactions_data)
        current_user_cluster = user_clusters.get(current_user_id, 0)

        # Get users in the same cluster who are not followed
        similar_users = []
        for user_id, cluster in user_clusters.items():
            if (cluster == current_user_cluster and 
                user_id not in following_ids and 
                user_id != current_user_id):
                user = User.query.get(user_id)
                if user and user.is_active:
                    similar_users.append(user)

        # Sort by follower count (popular users first)
        similar_users.sort(key=lambda u: u.get_follower_count(), reverse=True)

        # If not enough similar users, add popular users
        if len(similar_users) < num_recommendations:
            popular_users = User.query.filter(
                ~User.id.in_(following_ids),
                User.is_active == True
            ).order_by(User.created_at.desc()).limit(num_recommendations).all()

            for user in popular_users:
                if user not in similar_users:
                    similar_users.append(user)

        recommended_users = similar_users[:num_recommendations]

        logger.info(f'Generated {len(recommended_users)} user recommendations for user {current_user_id}')

        return jsonify({
            'recommendations': [user.to_dict() for user in recommended_users],
            'algorithm': 'clustering',
            'count': len(recommended_users)
        }), 200

    except Exception as e:
        logger.error(f'Error generating user recommendations: {str(e)}')
        return jsonify({'error': 'Failed to generate user recommendations', 'details': str(e)}), 500

@recommendations_bp.route('/trending', methods=['GET'])
def get_trending_posts():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        num_posts = request.args.get('count', 20, type=int)
        num_posts = min(num_posts, 50)  # Limit to 50

        current_user = User.query.get(current_user_id)

        # Get all posts with engagement data
        posts = Post.query.filter(Post.is_active == True).all()
        posts_data = []

        for post in posts:
            posts_data.append({
                'id': post.id,
                'user_id': post.user_id,
                'likes_count': post.get_likes_count(),
                'comments_count': post.get_comments_count(),
                'created_at': post.created_at.isoformat()
            })

        # Get trending post IDs
        trending_ids = recommendation_engine.get_trending_posts(posts_data, num_posts)

        # Get the actual post objects
        trending_posts = []
        for post_id in trending_ids:
            post = Post.query.get(post_id)
            if post and post.is_active:
                trending_posts.append(post.to_dict(current_user))

        logger.info(f'Retrieved {len(trending_posts)} trending posts')

        return jsonify({
            'trending_posts': trending_posts,
            'count': len(trending_posts)
        }), 200

    except Exception as e:
        logger.error(f'Error fetching trending posts: {str(e)}')
        return jsonify({'error': 'Failed to fetch trending posts', 'details': str(e)}), 500

@recommendations_bp.route('/engagement-prediction', methods=['POST'])
def predict_post_engagement():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        data = request.get_json()

        # Get user data
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # Prepare post data for prediction
        post_data = {
            'caption': data.get('caption', ''),
            'created_at': data.get('created_at', datetime.utcnow().isoformat()),
            'location': data.get('location', '')
        }

        # Prepare user data for prediction
        user_posts = Post.query.filter_by(user_id=current_user_id, is_active=True).all()
        avg_likes = sum(post.get_likes_count() for post in user_posts) / max(len(user_posts), 1)

        user_data = {
            'followers_count': current_user.get_follower_count(),
            'avg_likes_per_post': avg_likes,
            'posts_per_week': len(user_posts) / max(1, (datetime.utcnow() - current_user.created_at).days / 7)
        }

        # Predict engagement
        prediction = engagement_predictor.predict_engagement(post_data, user_data)

        logger.info(f'Generated engagement prediction for user {current_user_id}')

        return jsonify(prediction), 200

    except Exception as e:
        logger.error(f'Error predicting engagement: {str(e)}')
        return jsonify({'error': 'Failed to predict engagement', 'details': str(e)}), 500

@recommendations_bp.route('/hashtags', methods=['POST'])
def suggest_hashtags():
    try:
        verify_jwt_in_request()

        data = request.get_json()
        image_url = data.get('image_url', '')
        caption = data.get('caption', '')

        if not image_url and not caption:
            return jsonify({'error': 'Either image_url or caption is required'}), 400

        from ml_algorithms import ImageProcessor
        image_processor = ImageProcessor()

        # Suggest hashtags
        suggested_hashtags = image_processor.suggest_hashtags(image_url, caption)

        logger.info(f'Generated {len(suggested_hashtags)} hashtag suggestions')

        return jsonify({
            'suggested_hashtags': suggested_hashtags,
            'count': len(suggested_hashtags)
        }), 200

    except Exception as e:
        logger.error(f'Error suggesting hashtags: {str(e)}')
        return jsonify({'error': 'Failed to suggest hashtags', 'details': str(e)}), 500
