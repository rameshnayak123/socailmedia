
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import joblib
from datetime import datetime, timedelta
import random

class AdvancedRecommendationSystem:
    """Advanced ML-based content recommendation system"""

    def __init__(self):
        self.content_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.user_item_matrix = None
        self.content_similarity_matrix = None
        self.trained = False

    def prepare_training_data(self, interactions_data, content_data):
        """Prepare data for training the recommendation model"""
        # Create user-item interaction matrix
        users = list(set([i['user_id'] for i in interactions_data]))
        items = list(set([i['content_id'] for i in interactions_data]))

        interaction_matrix = np.zeros((len(users), len(items)))
        user_idx = {user: idx for idx, user in enumerate(users)}
        item_idx = {item: idx for idx, item in enumerate(items)}

        # Fill interaction matrix with engagement scores
        for interaction in interactions_data:
            u_idx = user_idx[interaction['user_id']]
            i_idx = item_idx[interaction['content_id']]
            interaction_matrix[u_idx][i_idx] = interaction['engagement_score']

        self.user_item_matrix = interaction_matrix
        self.user_idx = user_idx
        self.item_idx = item_idx

        # Create content similarity matrix
        content_texts = [content['text'] for content in content_data]
        content_vectors = self.content_vectorizer.fit_transform(content_texts)
        self.content_similarity_matrix = cosine_similarity(content_vectors)

        self.trained = True

    def collaborative_filtering_recommendations(self, user_id, n_recommendations=10):
        """Generate recommendations using collaborative filtering"""
        if not self.trained or user_id not in self.user_idx:
            return []

        user_index = self.user_idx[user_id]
        user_similarities = cosine_similarity([self.user_item_matrix[user_index]], self.user_item_matrix)[0]

        # Find similar users
        similar_users = np.argsort(user_similarities)[::-1][1:6]  # Top 5 similar users

        # Recommend items liked by similar users
        recommendations = []
        user_interactions = self.user_item_matrix[user_index]

        for item_idx in range(len(user_interactions)):
            if user_interactions[item_idx] == 0:  # User hasn't interacted with this item
                score = sum(self.user_item_matrix[similar_user][item_idx] * user_similarities[similar_user] 
                           for similar_user in similar_users)
                recommendations.append((item_idx, score))

        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]

    def content_based_recommendations(self, content_id, n_recommendations=10):
        """Generate recommendations using content-based filtering"""
        if not self.trained or content_id not in self.item_idx:
            return []

        content_index = self.item_idx[content_id]
        similarities = self.content_similarity_matrix[content_index]
        similar_items = np.argsort(similarities)[::-1][1:n_recommendations+1]

        return [(idx, similarities[idx]) for idx in similar_items]

    def hybrid_recommendations(self, user_id, content_ids, n_recommendations=10):
        """Combine collaborative and content-based recommendations"""
        collab_recs = self.collaborative_filtering_recommendations(user_id, n_recommendations)

        content_recs = []
        for content_id in content_ids:
            content_recs.extend(self.content_based_recommendations(content_id, 3))

        # Combine and weight recommendations
        combined_scores = {}

        for item_idx, score in collab_recs:
            combined_scores[item_idx] = score * 0.6  # 60% weight for collaborative

        for item_idx, score in content_recs:
            if item_idx in combined_scores:
                combined_scores[item_idx] += score * 0.4  # 40% weight for content-based
            else:
                combined_scores[item_idx] = score * 0.4

        recommendations = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]

class VideoContentAnalyzer:
    """ML model for analyzing video content (simulated)"""

    def __init__(self):
        # Simulated pre-trained models
        self.object_detection_model = None
        self.scene_classification_model = None
        self.audio_analysis_model = None

    def analyze_video_content(self, video_path):
        """Analyze video content and extract features"""
        # Simulated video analysis results
        analysis_results = {
            'detected_objects': random.choices(['person', 'car', 'dog', 'cat', 'food', 'music_instrument'], k=3),
            'scene_type': random.choice(['indoor', 'outdoor', 'studio', 'nature', 'urban']),
            'dominant_colors': ['#FF5733', '#33FF57', '#3357FF'],
            'motion_intensity': random.uniform(0.1, 1.0),
            'audio_features': {
                'has_music': random.choice([True, False]),
                'has_speech': random.choice([True, False]),
                'audio_quality': random.uniform(0.5, 1.0),
                'volume_level': random.uniform(0.3, 1.0)
            },
            'quality_score': random.uniform(0.4, 1.0),
            'duration': random.randint(15, 60),  # seconds
            'resolution': random.choice(['720p', '1080p', '4K']),
            'frame_rate': random.choice([24, 30, 60])
        }

        return analysis_results

    def predict_video_virality(self, video_features, user_features):
        """Predict the viral potential of a video"""
        # Simulated ML prediction
        base_score = 0.3

        # Video quality factors
        if video_features['quality_score'] > 0.8:
            base_score += 0.2

        if video_features['motion_intensity'] > 0.7:
            base_score += 0.15

        if video_features['audio_features']['has_music']:
            base_score += 0.1

        # User factors
        if user_features.get('follower_count', 0) > 1000:
            base_score += 0.1

        if user_features.get('engagement_rate', 0) > 0.05:
            base_score += 0.15

        viral_score = min(base_score + random.uniform(-0.1, 0.2), 1.0)

        return {
            'viral_probability': viral_score,
            'predicted_views': int(viral_score * 10000),
            'predicted_engagement_rate': viral_score * 0.08,
            'optimization_suggestions': [
                'Add trending music',
                'Include popular hashtags',
                'Optimize for mobile viewing',
                'Post during peak hours'
            ]
        }

class UserBehaviorMLModel:
    """Machine learning model for user behavior prediction"""

    def __init__(self):
        self.engagement_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.churn_predictor = LogisticRegression(random_state=42)
        self.scaler = StandardScaler()
        self.trained = False

    def prepare_user_features(self, user_data, activity_data):
        """Prepare feature vectors for ML models"""
        features = []
        labels = []

        for user_id, user_info in user_data.items():
            if user_id not in activity_data:
                continue

            activities = activity_data[user_id]

            # Feature engineering
            feature_vector = [
                len(activities.get('actions', [])),  # Total actions
                len(set([a['action'] for a in activities.get('actions', [])])),  # Action variety
                user_info.get('followers', 0),  # Follower count
                user_info.get('following', 0),  # Following count
                user_info.get('posts_count', 0),  # Posts count
                len(user_info.get('preferences', {}).get('content_types', [])),  # Interest diversity
                (datetime.now() - datetime.fromisoformat(user_info['created_at'])).days,  # Account age
            ]

            # Engagement level (high/medium/low)
            total_actions = len(activities.get('actions', []))
            if total_actions > 100:
                engagement_level = 2  # High
            elif total_actions > 20:
                engagement_level = 1  # Medium
            else:
                engagement_level = 0  # Low

            features.append(feature_vector)
            labels.append(engagement_level)

        return np.array(features), np.array(labels)

    def train_models(self, user_data, activity_data):
        """Train the ML models"""
        features, labels = self.prepare_user_features(user_data, activity_data)

        if len(features) == 0:
            return False

        # Scale features
        features_scaled = self.scaler.fit_transform(features)

        # Train engagement classifier
        self.engagement_classifier.fit(features_scaled, labels)

        # Generate churn labels (simulated)
        churn_labels = np.random.choice([0, 1], size=len(features), p=[0.8, 0.2])
        self.churn_predictor.fit(features_scaled, churn_labels)

        self.trained = True
        return True

    def predict_user_engagement(self, user_data, activity_data):
        """Predict user engagement level"""
        if not self.trained:
            return {'engagement_level': 'unknown', 'confidence': 0.0}

        features, _ = self.prepare_user_features({user_data['user_id']: user_data}, {user_data['user_id']: activity_data})

        if len(features) == 0:
            return {'engagement_level': 'low', 'confidence': 0.5}

        features_scaled = self.scaler.transform(features)

        engagement_pred = self.engagement_classifier.predict(features_scaled)[0]
        engagement_prob = self.engagement_classifier.predict_proba(features_scaled)[0]

        engagement_levels = ['low', 'medium', 'high']

        return {
            'engagement_level': engagement_levels[engagement_pred],
            'confidence': max(engagement_prob),
            'probabilities': dict(zip(engagement_levels, engagement_prob))
        }

    def predict_churn_risk(self, user_data, activity_data):
        """Predict user churn risk"""
        if not self.trained:
            return {'churn_risk': 'unknown', 'probability': 0.5}

        features, _ = self.prepare_user_features({user_data['user_id']: user_data}, {user_data['user_id']: activity_data})

        if len(features) == 0:
            return {'churn_risk': 'medium', 'probability': 0.5}

        features_scaled = self.scaler.transform(features)

        churn_pred = self.churn_predictor.predict(features_scaled)[0]
        churn_prob = self.churn_predictor.predict_proba(features_scaled)[0][1]  # Probability of churn

        risk_level = 'high' if churn_prob > 0.7 else 'medium' if churn_prob > 0.3 else 'low'

        return {
            'churn_risk': risk_level,
            'probability': churn_prob,
            'retention_suggestions': [
                'Send personalized content recommendations',
                'Engage with trending topics',
                'Offer exclusive features',
                'Improve content quality'
            ] if churn_prob > 0.5 else []
        }

class TrendDetectionModel:
    """Model for detecting trending content and hashtags"""

    def __init__(self):
        self.hashtag_popularity = {}
        self.content_trends = {}
        self.time_decay_factor = 0.95

    def update_hashtag_trend(self, hashtag, engagement_score, timestamp=None):
        """Update hashtag trend score"""
        if timestamp is None:
            timestamp = datetime.now()

        if hashtag not in self.hashtag_popularity:
            self.hashtag_popularity[hashtag] = {'score': 0.0, 'last_updated': timestamp, 'mentions': 0}

        # Apply time decay
        time_diff = (timestamp - self.hashtag_popularity[hashtag]['last_updated']).total_seconds() / 3600
        decay = self.time_decay_factor ** time_diff

        self.hashtag_popularity[hashtag]['score'] = (self.hashtag_popularity[hashtag]['score'] * decay + 
                                                    engagement_score)
        self.hashtag_popularity[hashtag]['last_updated'] = timestamp
        self.hashtag_popularity[hashtag]['mentions'] += 1

    def get_trending_hashtags(self, limit=10):
        """Get current trending hashtags"""
        # Apply time decay to all hashtags
        current_time = datetime.now()

        for hashtag in self.hashtag_popularity:
            time_diff = (current_time - self.hashtag_popularity[hashtag]['last_updated']).total_seconds() / 3600
            decay = self.time_decay_factor ** time_diff
            self.hashtag_popularity[hashtag]['score'] *= decay

        # Sort by trending score
        trending = sorted(self.hashtag_popularity.items(), 
                         key=lambda x: x[1]['score'], reverse=True)

        return [(hashtag, data['score'], data['mentions']) for hashtag, data in trending[:limit]]

    def detect_content_trends(self, content_data, time_window_hours=24):
        """Detect trending content categories and topics"""
        current_time = datetime.now()
        recent_content = []

        for content in content_data:
            content_time = datetime.fromisoformat(content['created_at'])
            if (current_time - content_time).total_seconds() / 3600 <= time_window_hours:
                recent_content.append(content)

        # Analyze categories
        category_engagement = {}
        for content in recent_content:
            category = content.get('category', 'other')
            engagement = content.get('likes', 0) + content.get('comments', 0) * 2 + content.get('shares', 0) * 3

            if category not in category_engagement:
                category_engagement[category] = {'total_engagement': 0, 'content_count': 0}

            category_engagement[category]['total_engagement'] += engagement
            category_engagement[category]['content_count'] += 1

        # Calculate trend scores
        trending_categories = []
        for category, data in category_engagement.items():
            avg_engagement = data['total_engagement'] / max(data['content_count'], 1)
            trend_score = avg_engagement * data['content_count']  # Engagement * Volume
            trending_categories.append({
                'category': category,
                'trend_score': trend_score,
                'avg_engagement': avg_engagement,
                'content_count': data['content_count']
            })

        trending_categories.sort(key=lambda x: x['trend_score'], reverse=True)

        return trending_categories

# Save models to files for persistence
def save_models(models_dict, filepath='models.pkl'):
    """Save ML models to file"""
    with open(filepath, 'wb') as f:
        pickle.dump(models_dict, f)

def load_models(filepath='models.pkl'):
    """Load ML models from file"""
    try:
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None
