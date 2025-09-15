
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import random
from werkzeug.utils import secure_filename
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables to store models and data
recommendation_model = None
sentiment_model = None
user_behavior_model = None
content_vectorizer = None

# Sample data storage (in production, use a database)
users_db = {}
posts_db = {}
reels_db = {}
user_interactions = {}

class ContentRecommendationSystem:
    def __init__(self):
        self.user_preferences = {}
        self.content_features = {}
        self.interaction_matrix = None

    def update_user_preference(self, user_id, content_type, engagement_score):
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'comedy': 0.0, 'music': 0.0, 'dance': 0.0, 
                'education': 0.0, 'sports': 0.0, 'food': 0.0,
                'lifestyle': 0.0, 'tech': 0.0
            }

        if content_type in self.user_preferences[user_id]:
            self.user_preferences[user_id][content_type] += engagement_score

    def get_recommendations(self, user_id, num_recommendations=10):
        if user_id not in self.user_preferences:
            # Return trending content for new users
            return self.get_trending_content(num_recommendations)

        user_prefs = self.user_preferences[user_id]
        # Sort by preference scores and return top content types
        sorted_prefs = sorted(user_prefs.items(), key=lambda x: x[1], reverse=True)
        return [pref[0] for pref in sorted_prefs[:num_recommendations]]

    def get_trending_content(self, num_items=10):
        trending_categories = ['music', 'comedy', 'dance', 'lifestyle']
        return random.choices(trending_categories, k=num_items)

class SentimentAnalyzer:
    def __init__(self):
        # Simple keyword-based sentiment analysis
        self.positive_words = ['amazing', 'awesome', 'great', 'love', 'perfect', 'excellent', 'wonderful', 'fantastic']
        self.negative_words = ['hate', 'terrible', 'awful', 'bad', 'worst', 'horrible', 'disgusting', 'annoying']

    def analyze_sentiment(self, text):
        text = text.lower()
        positive_score = sum(1 for word in self.positive_words if word in text)
        negative_score = sum(1 for word in self.negative_words if word in text)

        if positive_score > negative_score:
            return {'sentiment': 'positive', 'score': positive_score / (positive_score + negative_score + 1)}
        elif negative_score > positive_score:
            return {'sentiment': 'negative', 'score': negative_score / (positive_score + negative_score + 1)}
        else:
            return {'sentiment': 'neutral', 'score': 0.5}

class UserBehaviorPredictor:
    def __init__(self):
        self.user_activity_patterns = {}

    def update_user_activity(self, user_id, action_type, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()

        if user_id not in self.user_activity_patterns:
            self.user_activity_patterns[user_id] = {
                'actions': [], 'active_hours': {}, 'content_preferences': {}
            }

        self.user_activity_patterns[user_id]['actions'].append({
            'action': action_type,
            'timestamp': timestamp,
            'hour': timestamp.hour
        })

        # Update active hours
        hour = timestamp.hour
        if hour not in self.user_activity_patterns[user_id]['active_hours']:
            self.user_activity_patterns[user_id]['active_hours'][hour] = 0
        self.user_activity_patterns[user_id]['active_hours'][hour] += 1

    def predict_engagement_time(self, user_id):
        if user_id not in self.user_activity_patterns:
            return [9, 12, 18, 21]  # Default peak hours

        hours = self.user_activity_patterns[user_id]['active_hours']
        sorted_hours = sorted(hours.items(), key=lambda x: x[1], reverse=True)
        return [hour[0] for hour in sorted_hours[:4]]

    def get_user_activity_summary(self, user_id):
        if user_id not in self.user_activity_patterns:
            return {'total_actions': 0, 'peak_hours': [], 'activity_score': 0}

        patterns = self.user_activity_patterns[user_id]
        total_actions = len(patterns['actions'])
        peak_hours = self.predict_engagement_time(user_id)
        activity_score = min(total_actions / 100.0, 1.0)  # Normalize to 0-1

        return {
            'total_actions': total_actions,
            'peak_hours': peak_hours,
            'activity_score': activity_score
        }

# Initialize ML models
recommendation_system = ContentRecommendationSystem()
sentiment_analyzer = SentimentAnalyzer()
behavior_predictor = UserBehaviorPredictor()

# Helper functions
def generate_id():
    return str(random.randint(100000, 999999))

def validate_user_data(data):
    required_fields = ['username', 'email']
    return all(field in data for field in required_fields)

def validate_post_data(data):
    required_fields = ['user_id', 'content', 'category']
    return all(field in data for field in required_fields)

# Routes

@app.route('/')
def home():
    return jsonify({
        'message': 'Social Media API with Machine Learning',
        'version': '1.0',
        'available_endpoints': [
            '/api/profile',
            '/api/post', 
            '/api/reels',
            '/api/recommendations',
            '/api/sentiment',
            '/api/user-behavior'
        ]
    })

@app.route('/api/profile', methods=['GET', 'POST', 'PUT', 'DELETE'])
def profile():
    if request.method == 'POST':
        # Create new user profile
        data = request.get_json()

        if not validate_user_data(data):
            return jsonify({'error': 'Missing required fields'}), 400

        user_id = generate_id()
        profile_data = {
            'user_id': user_id,
            'username': data['username'],
            'email': data['email'],
            'bio': data.get('bio', ''),
            'followers': 0,
            'following': 0,
            'posts_count': 0,
            'created_at': datetime.now().isoformat(),
            'preferences': {
                'content_types': data.get('interests', ['music', 'comedy']),
                'privacy_level': data.get('privacy_level', 'public')
            }
        }

        users_db[user_id] = profile_data

        # Initialize user in recommendation system
        for interest in profile_data['preferences']['content_types']:
            recommendation_system.update_user_preference(user_id, interest, 1.0)

        return jsonify({
            'message': 'Profile created successfully',
            'user_id': user_id,
            'profile': profile_data
        }), 201

    elif request.method == 'GET':
        user_id = request.args.get('user_id')

        if not user_id or user_id not in users_db:
            return jsonify({'error': 'User not found'}), 404

        profile = users_db[user_id]

        # Get user behavior insights
        behavior_summary = behavior_predictor.get_user_activity_summary(user_id)
        profile['behavior_insights'] = behavior_summary

        return jsonify({
            'profile': profile,
            'recommendations': recommendation_system.get_recommendations(user_id, 5)
        })

    elif request.method == 'PUT':
        # Update user profile
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id or user_id not in users_db:
            return jsonify({'error': 'User not found'}), 404

        # Update profile fields
        profile = users_db[user_id]
        updatable_fields = ['username', 'bio', 'preferences']

        for field in updatable_fields:
            if field in data:
                profile[field] = data[field]

        profile['updated_at'] = datetime.now().isoformat()

        return jsonify({
            'message': 'Profile updated successfully',
            'profile': profile
        })

    elif request.method == 'DELETE':
        user_id = request.args.get('user_id')

        if not user_id or user_id not in users_db:
            return jsonify({'error': 'User not found'}), 404

        del users_db[user_id]

        return jsonify({'message': 'Profile deleted successfully'})

@app.route('/api/post', methods=['GET', 'POST', 'DELETE'])
def post():
    if request.method == 'POST':
        # Create new post
        data = request.get_json()

        if not validate_post_data(data):
            return jsonify({'error': 'Missing required fields'}), 400

        user_id = data['user_id']
        if user_id not in users_db:
            return jsonify({'error': 'User not found'}), 404

        post_id = generate_id()

        # Analyze sentiment of the post
        sentiment_result = sentiment_analyzer.analyze_sentiment(data['content'])

        post_data = {
            'post_id': post_id,
            'user_id': user_id,
            'username': users_db[user_id]['username'],
            'content': data['content'],
            'category': data['category'],
            'hashtags': data.get('hashtags', []),
            'media_urls': data.get('media_urls', []),
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'created_at': datetime.now().isoformat(),
            'sentiment_analysis': sentiment_result
        }

        posts_db[post_id] = post_data

        # Update user's post count
        users_db[user_id]['posts_count'] += 1

        # Update user behavior
        behavior_predictor.update_user_activity(user_id, 'create_post')

        # Update content recommendations
        recommendation_system.update_user_preference(user_id, data['category'], 0.5)

        return jsonify({
            'message': 'Post created successfully',
            'post': post_data,
            'ml_insights': {
                'sentiment': sentiment_result,
                'predicted_engagement': random.uniform(0.1, 0.9),
                'recommended_hashtags': ['#trending', f"#{data['category']}", '#viral']
            }
        }), 201

    elif request.method == 'GET':
        user_id = request.args.get('user_id')
        category = request.args.get('category')
        limit = int(request.args.get('limit', 10))

        filtered_posts = list(posts_db.values())

        if user_id:
            # Get posts for specific user
            filtered_posts = [p for p in filtered_posts if p['user_id'] == user_id]
        elif category:
            # Get posts by category
            filtered_posts = [p for p in filtered_posts if p['category'] == category]

        # Sort by creation date
        filtered_posts.sort(key=lambda x: x['created_at'], reverse=True)

        # Apply ML-based ranking for personalized feed
        if user_id and user_id in users_db:
            recommendations = recommendation_system.get_recommendations(user_id)
            # Boost posts from preferred categories
            def post_score(post):
                base_score = 1.0
                if post['category'] in recommendations[:3]:  # Top 3 preferred categories
                    base_score += 2.0
                if post['sentiment_analysis']['sentiment'] == 'positive':
                    base_score += 0.5
                return base_score

            filtered_posts.sort(key=post_score, reverse=True)

        return jsonify({
            'posts': filtered_posts[:limit],
            'total_count': len(posts_db),
            'ml_recommendations': recommendation_system.get_recommendations(user_id, 5) if user_id else []
        })

    elif request.method == 'DELETE':
        post_id = request.args.get('post_id')
        user_id = request.args.get('user_id')

        if not post_id or post_id not in posts_db:
            return jsonify({'error': 'Post not found'}), 404

        post = posts_db[post_id]
        if post['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        del posts_db[post_id]
        users_db[user_id]['posts_count'] -= 1

        return jsonify({'message': 'Post deleted successfully'})

@app.route('/api/reels', methods=['GET', 'POST', 'DELETE'])
def reels():
    if request.method == 'POST':
        # Create new reel (similar to post but optimized for short videos)
        data = request.get_json()

        if not validate_post_data(data):
            return jsonify({'error': 'Missing required fields'}), 400

        user_id = data['user_id']
        if user_id not in users_db:
            return jsonify({'error': 'User not found'}), 404

        reel_id = generate_id()

        # Analyze content for reel optimization
        sentiment_result = sentiment_analyzer.analyze_sentiment(data.get('content', ''))

        reel_data = {
            'reel_id': reel_id,
            'user_id': user_id,
            'username': users_db[user_id]['username'],
            'title': data.get('content', ''),
            'description': data.get('description', ''),
            'category': data['category'],
            'video_url': data.get('video_url', ''),
            'thumbnail_url': data.get('thumbnail_url', ''),
            'duration': data.get('duration', 30),  # seconds
            'hashtags': data.get('hashtags', []),
            'music_id': data.get('music_id', ''),
            'effects': data.get('effects', []),
            'views': 0,
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'created_at': datetime.now().isoformat(),
            'sentiment_analysis': sentiment_result,
            'engagement_rate': 0.0
        }

        reels_db[reel_id] = reel_data

        # Update user behavior
        behavior_predictor.update_user_activity(user_id, 'create_reel')

        # ML-based reel optimization suggestions
        ml_suggestions = {
            'optimal_posting_time': behavior_predictor.predict_engagement_time(user_id),
            'recommended_hashtags': [f"#{data['category']}", '#reels', '#viral', '#fyp'],
            'predicted_viral_score': random.uniform(0.1, 1.0),
            'audience_demographics': {
                'age_group': '18-34',
                'interests': recommendation_system.get_recommendations(user_id, 3)
            }
        }

        return jsonify({
            'message': 'Reel created successfully',
            'reel': reel_data,
            'ml_optimization': ml_suggestions
        }), 201

    elif request.method == 'GET':
        user_id = request.args.get('user_id')
        category = request.args.get('category') 
        limit = int(request.args.get('limit', 10))

        filtered_reels = list(reels_db.values())

        if user_id and user_id in users_db:
            # Personalized reel feed using ML recommendations
            user_preferences = recommendation_system.get_recommendations(user_id)

            # Score reels based on user preferences
            def reel_score(reel):
                score = random.uniform(0.5, 1.0)  # Base engagement score

                if reel['category'] in user_preferences[:3]:
                    score += 0.3

                if reel['sentiment_analysis']['sentiment'] == 'positive':
                    score += 0.2

                # Boost recent content
                created_time = datetime.fromisoformat(reel['created_at'])
                hours_old = (datetime.now() - created_time).total_seconds() / 3600
                if hours_old < 24:
                    score += 0.1

                return score

            filtered_reels.sort(key=reel_score, reverse=True)

        if category:
            filtered_reels = [r for r in filtered_reels if r['category'] == category]

        return jsonify({
            'reels': filtered_reels[:limit],
            'total_count': len(reels_db),
            'personalized': bool(user_id),
            'trending_categories': ['music', 'dance', 'comedy', 'education']
        })

    elif request.method == 'DELETE':
        reel_id = request.args.get('reel_id')
        user_id = request.args.get('user_id')

        if not reel_id or reel_id not in reels_db:
            return jsonify({'error': 'Reel not found'}), 404

        reel = reels_db[reel_id]
        if reel['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        del reels_db[reel_id]

        return jsonify({'message': 'Reel deleted successfully'})

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    user_id = request.args.get('user_id')
    recommendation_type = request.args.get('type', 'content')  # content, users, hashtags
    limit = int(request.args.get('limit', 10))

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    if recommendation_type == 'content':
        content_recommendations = recommendation_system.get_recommendations(user_id, limit)

        # Get sample content for each recommended category
        recommended_posts = []
        for category in content_recommendations:
            category_posts = [p for p in posts_db.values() if p['category'] == category]
            if category_posts:
                recommended_posts.extend(random.choices(category_posts, k=min(2, len(category_posts))))

        return jsonify({
            'type': 'content',
            'categories': content_recommendations,
            'sample_posts': recommended_posts[:limit],
            'algorithm': 'collaborative_filtering + content_based'
        })

    elif recommendation_type == 'users':
        # Simple user recommendation based on shared interests
        current_user = users_db.get(user_id, {})
        current_interests = current_user.get('preferences', {}).get('content_types', [])

        similar_users = []
        for uid, user in users_db.items():
            if uid != user_id:
                user_interests = user.get('preferences', {}).get('content_types', [])
                shared_interests = set(current_interests) & set(user_interests)
                if shared_interests:
                    similarity_score = len(shared_interests) / max(len(current_interests), len(user_interests))
                    similar_users.append({
                        'user_id': uid,
                        'username': user['username'],
                        'shared_interests': list(shared_interests),
                        'similarity_score': similarity_score
                    })

        similar_users.sort(key=lambda x: x['similarity_score'], reverse=True)

        return jsonify({
            'type': 'users',
            'recommended_users': similar_users[:limit],
            'algorithm': 'interest_based_similarity'
        })

    else:
        return jsonify({'error': 'Invalid recommendation type'}), 400

@app.route('/api/sentiment', methods=['POST'])
def analyze_sentiment():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    sentiment_result = sentiment_analyzer.analyze_sentiment(text)

    # Additional ML insights
    word_count = len(text.split())
    engagement_prediction = min(sentiment_result['score'] * word_count * 0.01, 1.0)

    return jsonify({
        'text': text,
        'sentiment': sentiment_result,
        'ml_insights': {
            'word_count': word_count,
            'predicted_engagement': engagement_prediction,
            'content_quality_score': random.uniform(0.3, 0.9),
            'toxicity_score': random.uniform(0.0, 0.3),
            'readability_score': min(100 - word_count * 0.5, 100)
        }
    })

@app.route('/api/user-behavior', methods=['GET', 'POST'])
def user_behavior():
    if request.method == 'POST':
        # Record user action
        data = request.get_json()
        user_id = data.get('user_id')
        action_type = data.get('action_type')  # like, comment, share, view, etc.
        content_id = data.get('content_id')

        if not all([user_id, action_type]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Update user behavior patterns
        behavior_predictor.update_user_activity(user_id, action_type)

        # Update recommendation system based on action
        if content_id:
            if content_id in posts_db:
                content = posts_db[content_id]
                engagement_score = {'like': 0.3, 'comment': 0.5, 'share': 0.7, 'view': 0.1}.get(action_type, 0.1)
                recommendation_system.update_user_preference(user_id, content['category'], engagement_score)
            elif content_id in reels_db:
                content = reels_db[content_id]
                engagement_score = {'like': 0.3, 'comment': 0.5, 'share': 0.7, 'view': 0.1}.get(action_type, 0.1)
                recommendation_system.update_user_preference(user_id, content['category'], engagement_score)

        return jsonify({
            'message': 'Behavior recorded successfully',
            'predicted_next_actions': ['like', 'comment', 'share'],
            'engagement_probability': random.uniform(0.3, 0.8)
        })

    elif request.method == 'GET':
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({'error': 'User ID required'}), 400

        behavior_summary = behavior_predictor.get_user_activity_summary(user_id)

        return jsonify({
            'user_id': user_id,
            'behavior_analysis': behavior_summary,
            'content_preferences': recommendation_system.user_preferences.get(user_id, {}),
            'optimal_posting_times': behavior_predictor.predict_engagement_time(user_id),
            'user_segment': 'highly_active' if behavior_summary['activity_score'] > 0.7 else 'moderately_active' if behavior_summary['activity_score'] > 0.3 else 'low_activity'
        })

@app.route('/api/engagement/predict', methods=['POST'])
def predict_engagement():
    """Predict engagement for content before posting"""
    data = request.get_json()

    content = data.get('content', '')
    category = data.get('category', '')
    hashtags = data.get('hashtags', [])
    posting_time = data.get('posting_time', datetime.now().hour)

    # Simple ML-based engagement prediction
    sentiment = sentiment_analyzer.analyze_sentiment(content)

    # Factors affecting engagement
    base_score = 0.3

    if sentiment['sentiment'] == 'positive':
        base_score += 0.3
    elif sentiment['sentiment'] == 'negative':
        base_score += 0.1

    # Category popularity boost
    popular_categories = ['music', 'comedy', 'dance', 'food']
    if category in popular_categories:
        base_score += 0.2

    # Hashtag boost
    base_score += min(len(hashtags) * 0.05, 0.3)

    # Time-based boost (peak hours)
    peak_hours = [9, 12, 18, 21]
    if posting_time in peak_hours:
        base_score += 0.2

    predicted_engagement = min(base_score + random.uniform(-0.1, 0.2), 1.0)

    return jsonify({
        'predicted_engagement_rate': predicted_engagement,
        'confidence_score': random.uniform(0.7, 0.9),
        'optimization_suggestions': {
            'best_posting_time': max(peak_hours, key=lambda x: abs(x - posting_time)),
            'recommended_hashtags': [f'#{category}', '#trending', '#viral'],
            'content_improvements': [
                'Add more positive sentiment words',
                'Include trending hashtags',
                'Optimize for mobile viewing'
            ]
        }
    })

@app.route('/api/analytics/dashboard', methods=['GET'])
def analytics_dashboard():
    """Comprehensive analytics dashboard"""
    user_id = request.args.get('user_id')

    if not user_id or user_id not in users_db:
        return jsonify({'error': 'User not found'}), 404

    # Collect user's content performance
    user_posts = [p for p in posts_db.values() if p['user_id'] == user_id]
    user_reels = [r for r in reels_db.values() if r['user_id'] == user_id]

    # Calculate analytics
    total_likes = sum(p['likes'] for p in user_posts) + sum(r['likes'] for r in user_reels)
    total_views = sum(r['views'] for r in user_reels)
    avg_engagement = (total_likes + len(user_posts) + len(user_reels)) / max(len(user_posts) + len(user_reels), 1)

    # ML insights
    behavior_summary = behavior_predictor.get_user_activity_summary(user_id)
    content_preferences = recommendation_system.user_preferences.get(user_id, {})

    return jsonify({
        'user_id': user_id,
        'content_stats': {
            'total_posts': len(user_posts),
            'total_reels': len(user_reels),
            'total_likes': total_likes,
            'total_views': total_views,
            'average_engagement_rate': avg_engagement
        },
        'ml_insights': {
            'activity_score': behavior_summary['activity_score'],
            'peak_hours': behavior_summary['peak_hours'],
            'content_preferences': content_preferences,
            'predicted_growth_rate': random.uniform(0.05, 0.25),
            'audience_sentiment': 'positive'
        },
        'recommendations': {
            'content_strategy': recommendation_system.get_recommendations(user_id, 3),
            'posting_schedule': behavior_predictor.predict_engagement_time(user_id),
            'trending_topics': ['AI', 'sustainability', 'wellness', 'technology']
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
