import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
import pandas as pd
import pickle
import os
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Tuple
import re
import hashlib
from textblob import TextBlob

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Machine Learning based recommendation system for Instagram clone"""

    def __init__(self):
        self.user_item_matrix = None
        self.content_features = None
        self.svd_model = None
        self.content_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')

    def collaborative_filtering_recommendations(self, user_id: int, posts_data: List[Dict], 
                                               interactions_data: List[Dict], num_recommendations: int = 10) -> List[int]:
        """Generate recommendations using collaborative filtering"""
        try:
            # Create user-item interaction matrix
            user_posts = {}
            for interaction in interactions_data:
                user = interaction.get('user_id')
                post = interaction.get('post_id')
                rating = interaction.get('rating', 1)  # Like = 1, Comment = 2, Share = 3

                if user not in user_posts:
                    user_posts[user] = {}
                user_posts[user][post] = rating

            # Convert to matrix format
            all_users = list(user_posts.keys())
            all_posts = list(set([post['id'] for post in posts_data]))

            # Create matrix
            matrix = np.zeros((len(all_users), len(all_posts)))
            user_idx = {user: idx for idx, user in enumerate(all_users)}
            post_idx = {post: idx for idx, post in enumerate(all_posts)}

            for user, posts in user_posts.items():
                for post, rating in posts.items():
                    if post in post_idx:
                        matrix[user_idx[user]][post_idx[post]] = rating

            # Apply SVD for dimensionality reduction
            if self.svd_model is None:
                self.svd_model = TruncatedSVD(n_components=min(50, len(all_users)-1))
                self.svd_model.fit(matrix)

            # Generate recommendations for the user
            if user_id in user_idx:
                user_vector = matrix[user_idx[user_id]].reshape(1, -1)
                user_reduced = self.svd_model.transform(user_vector)

                # Calculate similarity with all posts
                all_posts_reduced = self.svd_model.transform(matrix)
                similarities = cosine_similarity(user_reduced, all_posts_reduced.T)[0]

                # Get top recommendations
                recommended_indices = np.argsort(similarities)[::-1][:num_recommendations]
                recommended_posts = [all_posts[idx] for idx in recommended_indices]

                return recommended_posts

            # For new users, return trending posts
            return self.get_trending_posts(posts_data, num_recommendations)

        except Exception as e:
            logger.error(f"Error in collaborative filtering: {str(e)}")
            return self.get_trending_posts(posts_data, num_recommendations)

    def content_based_recommendations(self, user_id: int, posts_data: List[Dict], 
                                    user_preferences: Dict, num_recommendations: int = 10) -> List[int]:
        """Generate recommendations using content-based filtering"""
        try:
            # Extract content features from posts
            post_features = []
            post_ids = []

            for post in posts_data:
                # Combine caption, location, and hashtags for content analysis
                content = f"{post.get('caption', '')} {post.get('location', '')}"
                post_features.append(content)
                post_ids.append(post['id'])

            # Vectorize post content
            if len(post_features) > 0:
                content_matrix = self.content_vectorizer.fit_transform(post_features)

                # Create user profile based on preferences
                user_content = f"{user_preferences.get('bio', '')} {' '.join(user_preferences.get('interests', []))}"
                user_vector = self.content_vectorizer.transform([user_content])

                # Calculate content similarity
                similarities = cosine_similarity(user_vector, content_matrix)[0]

                # Get top recommendations
                recommended_indices = np.argsort(similarities)[::-1][:num_recommendations]
                recommended_posts = [post_ids[idx] for idx in recommended_indices]

                return recommended_posts

            return self.get_trending_posts(posts_data, num_recommendations)

        except Exception as e:
            logger.error(f"Error in content-based filtering: {str(e)}")
            return self.get_trending_posts(posts_data, num_recommendations)

    def hybrid_recommendations(self, user_id: int, posts_data: List[Dict], 
                             interactions_data: List[Dict], user_preferences: Dict,
                             num_recommendations: int = 10) -> List[int]:
        """Generate hybrid recommendations combining collaborative and content-based filtering"""
        try:
            # Get recommendations from both methods
            collab_recs = self.collaborative_filtering_recommendations(
                user_id, posts_data, interactions_data, num_recommendations
            )
            content_recs = self.content_based_recommendations(
                user_id, posts_data, user_preferences, num_recommendations
            )

            # Combine recommendations with weights
            # 60% collaborative filtering, 40% content-based
            collab_weight = 0.6
            content_weight = 0.4

            # Score posts based on both methods
            post_scores = {}

            for idx, post_id in enumerate(collab_recs):
                post_scores[post_id] = post_scores.get(post_id, 0) + collab_weight * (1 - idx / len(collab_recs))

            for idx, post_id in enumerate(content_recs):
                post_scores[post_id] = post_scores.get(post_id, 0) + content_weight * (1 - idx / len(content_recs))

            # Sort by combined score
            sorted_posts = sorted(post_scores.items(), key=lambda x: x[1], reverse=True)
            recommended_posts = [post_id for post_id, score in sorted_posts[:num_recommendations]]

            return recommended_posts

        except Exception as e:
            logger.error(f"Error in hybrid recommendations: {str(e)}")
            return self.get_trending_posts(posts_data, num_recommendations)

    def get_trending_posts(self, posts_data: List[Dict], num_recommendations: int = 10) -> List[int]:
        """Get trending posts based on engagement metrics"""
        try:
            # Calculate engagement score for each post
            for post in posts_data:
                likes = post.get('likes_count', 0)
                comments = post.get('comments_count', 0)
                shares = post.get('shares_count', 0)

                # Time decay factor (newer posts get higher score)
                post_date = datetime.fromisoformat(post.get('created_at', datetime.utcnow().isoformat()))
                days_old = (datetime.utcnow() - post_date).days
                time_factor = max(0.1, 1 / (1 + days_old * 0.1))

                # Engagement score formula
                engagement_score = (likes + comments * 2 + shares * 3) * time_factor
                post['engagement_score'] = engagement_score

            # Sort by engagement score
            trending_posts = sorted(posts_data, key=lambda x: x.get('engagement_score', 0), reverse=True)

            return [post['id'] for post in trending_posts[:num_recommendations]]

        except Exception as e:
            logger.error(f"Error in trending posts: {str(e)}")
            return [post['id'] for post in posts_data[:num_recommendations]]

    def user_clustering(self, users_data: List[Dict], interactions_data: List[Dict]) -> Dict[int, int]:
        """Cluster users based on their interaction patterns"""
        try:
            # Create user feature vectors
            user_features = []
            user_ids = []

            for user in users_data:
                # Extract features from user profile and interactions
                features = [
                    len(user.get('bio', '')),
                    user.get('followers_count', 0),
                    user.get('following_count', 0),
                    user.get('posts_count', 0),
                    len([i for i in interactions_data if i.get('user_id') == user.get('id')])
                ]
                user_features.append(features)
                user_ids.append(user['id'])

            # Normalize features
            user_features = np.array(user_features)
            if user_features.shape[0] > 0:
                user_features = (user_features - np.mean(user_features, axis=0)) / (np.std(user_features, axis=0) + 1e-8)

                # Perform clustering
                n_clusters = min(5, len(user_ids))  # Max 5 clusters
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = kmeans.fit_predict(user_features)

                # Return user-cluster mapping
                return {user_ids[i]: cluster_labels[i] for i in range(len(user_ids))}

            return {}

        except Exception as e:
            logger.error(f"Error in user clustering: {str(e)}")
            return {}

class ContentModerator:
    """AI-powered content moderation system"""

    def __init__(self):
        self.inappropriate_keywords = [
            'spam', 'hate', 'abuse', 'violence', 'harassment', 'bullying',
            'discrimination', 'threat', 'dangerous', 'illegal'
        ]
        self.sentiment_threshold = -0.5

    def moderate_text(self, text: str) -> Dict[str, any]:
        """Moderate text content for inappropriate material"""
        try:
            moderation_result = {
                'is_appropriate': True,
                'confidence': 1.0,
                'issues': [],
                'suggested_action': 'approve'
            }

            if not text:
                return moderation_result

            text_lower = text.lower()

            # Check for inappropriate keywords
            found_keywords = [keyword for keyword in self.inappropriate_keywords if keyword in text_lower]
            if found_keywords:
                moderation_result['is_appropriate'] = False
                moderation_result['issues'].append('inappropriate_language')
                moderation_result['confidence'] = 0.8

            # Sentiment analysis
            try:
                blob = TextBlob(text)
                sentiment_score = blob.sentiment.polarity

                if sentiment_score < self.sentiment_threshold:
                    moderation_result['issues'].append('negative_sentiment')
                    moderation_result['confidence'] *= 0.9
            except:
                pass

            # Check for spam patterns
            if self._is_spam(text):
                moderation_result['is_appropriate'] = False
                moderation_result['issues'].append('spam')
                moderation_result['confidence'] = 0.7

            # Determine suggested action
            if not moderation_result['is_appropriate']:
                if moderation_result['confidence'] > 0.7:
                    moderation_result['suggested_action'] = 'block'
                else:
                    moderation_result['suggested_action'] = 'review'

            return moderation_result

        except Exception as e:
            logger.error(f"Error in text moderation: {str(e)}")
            return {
                'is_appropriate': True,
                'confidence': 0.5,
                'issues': ['moderation_error'],
                'suggested_action': 'review'
            }

    def _is_spam(self, text: str) -> bool:
        """Simple spam detection based on patterns"""
        spam_patterns = [
            r'(buy|sale|discount|offer|deal).*(now|today|urgent)',
            r'(click|visit).*(link|website|url)',
            r'(free|win|prize|lottery|money)',
            r'(urgent|limited|expires|hurry)',
        ]

        text_lower = text.lower()
        for pattern in spam_patterns:
            if re.search(pattern, text_lower):
                return True

        # Check for excessive repetition
        words = text_lower.split()
        if len(words) > 5:
            unique_words = set(words)
            repetition_ratio = len(words) / len(unique_words)
            if repetition_ratio > 3:
                return True

        return False

    def moderate_image(self, image_url: str) -> Dict[str, any]:
        """Basic image moderation (placeholder for actual image AI)"""
        try:
            # This would integrate with actual image recognition APIs like Google Vision, AWS Rekognition, etc.
            # For now, return a basic result

            moderation_result = {
                'is_appropriate': True,
                'confidence': 0.9,
                'issues': [],
                'suggested_action': 'approve',
                'detected_objects': [],
                'adult_content_score': 0.0,
                'violence_score': 0.0
            }

            # Placeholder logic - in real implementation, would call image recognition API
            image_hash = hashlib.md5(image_url.encode()).hexdigest()

            # Simulate random moderation for demo purposes
            if int(image_hash[-1], 16) > 14:  # Very small chance of flagging
                moderation_result['is_appropriate'] = False
                moderation_result['issues'].append('potential_inappropriate_content')
                moderation_result['confidence'] = 0.7
                moderation_result['suggested_action'] = 'review'

            return moderation_result

        except Exception as e:
            logger.error(f"Error in image moderation: {str(e)}")
            return {
                'is_appropriate': True,
                'confidence': 0.5,
                'issues': ['moderation_error'],
                'suggested_action': 'review'
            }

class ImageProcessor:
    """Image processing and analysis utilities"""

    def __init__(self):
        self.supported_formats = ['jpg', 'jpeg', 'png', 'gif']
        self.max_size = 16 * 1024 * 1024  # 16MB

    def analyze_image(self, image_url: str) -> Dict[str, any]:
        """Analyze image for various properties"""
        try:
            analysis_result = {
                'is_valid': True,
                'format': 'unknown',
                'estimated_size': 0,
                'dominant_colors': [],
                'suggested_filters': [],
                'quality_score': 0.8,
                'faces_detected': 0,
                'objects_detected': []
            }

            # Basic URL validation
            if not image_url or not isinstance(image_url, str):
                analysis_result['is_valid'] = False
                return analysis_result

            # Extract format from URL
            for fmt in self.supported_formats:
                if f'.{fmt}' in image_url.lower():
                    analysis_result['format'] = fmt
                    break

            # Simulate image analysis (in real implementation, would use computer vision libraries)
            url_hash = hashlib.md5(image_url.encode()).hexdigest()

            # Simulate dominant colors
            hash_int = int(url_hash[:6], 16)
            analysis_result['dominant_colors'] = [
                f"#{url_hash[0:6]}",
                f"#{url_hash[6:12]}",
                f"#{url_hash[12:18]}"
            ]

            # Simulate filter suggestions based on image characteristics
            filter_options = ['vintage', 'bright', 'contrast', 'warm', 'cool', 'dramatic']
            analysis_result['suggested_filters'] = [
                filter_options[hash_int % len(filter_options)],
                filter_options[(hash_int + 1) % len(filter_options)]
            ]

            # Simulate quality score
            analysis_result['quality_score'] = min(1.0, (hash_int % 100) / 100 + 0.3)

            return analysis_result

        except Exception as e:
            logger.error(f"Error in image analysis: {str(e)}")
            return {
                'is_valid': False,
                'error': str(e)
            }

    def suggest_hashtags(self, image_url: str, caption: str = '') -> List[str]:
        """Suggest hashtags based on image content and caption"""
        try:
            suggested_hashtags = []

            # Analyze caption for keywords
            if caption:
                # Extract words that could be hashtags
                words = re.findall(r'\w+', caption.lower())
                relevant_words = [word for word in words if len(word) > 3 and word.isalpha()]
                suggested_hashtags.extend([f"#{word}" for word in relevant_words[:3]])

            # Add popular general hashtags
            popular_hashtags = [
                '#photography', '#instagood', '#photooftheday', '#beautiful',
                '#love', '#nature', '#art', '#style', '#travel', '#life'
            ]

            # Select hashtags based on image URL (simulated)
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            hash_indices = [int(url_hash[i:i+2], 16) % len(popular_hashtags) for i in range(0, 6, 2)]

            for idx in hash_indices:
                if popular_hashtags[idx] not in suggested_hashtags:
                    suggested_hashtags.append(popular_hashtags[idx])

            return suggested_hashtags[:8]  # Limit to 8 suggestions

        except Exception as e:
            logger.error(f"Error in hashtag suggestion: {str(e)}")
            return ['#photo', '#instagram', '#share']

class EngagementPredictor:
    """Predict post engagement using machine learning"""

    def __init__(self):
        self.feature_columns = [
            'hour_posted', 'day_of_week', 'caption_length', 'hashtag_count',
            'user_follower_count', 'user_avg_likes', 'user_post_frequency'
        ]

    def predict_engagement(self, post_data: Dict, user_data: Dict) -> Dict[str, float]:
        """Predict expected engagement for a post"""
        try:
            # Extract features
            post_time = datetime.fromisoformat(post_data.get('created_at', datetime.utcnow().isoformat()))

            features = {
                'hour_posted': post_time.hour,
                'day_of_week': post_time.weekday(),
                'caption_length': len(post_data.get('caption', '')),
                'hashtag_count': post_data.get('caption', '').count('#'),
                'user_follower_count': user_data.get('followers_count', 0),
                'user_avg_likes': user_data.get('avg_likes_per_post', 0),
                'user_post_frequency': user_data.get('posts_per_week', 1)
            }

            # Simple prediction model (in real implementation, would use trained ML model)
            base_score = features['user_follower_count'] * 0.05

            # Time-based adjustments
            if 8 <= features['hour_posted'] <= 10 or 19 <= features['hour_posted'] <= 21:
                base_score *= 1.3  # Peak hours

            if features['day_of_week'] in [4, 5, 6]:  # Friday, Saturday, Sunday
                base_score *= 1.2

            # Content-based adjustments
            if 50 <= features['caption_length'] <= 200:
                base_score *= 1.1  # Optimal caption length

            if 3 <= features['hashtag_count'] <= 7:
                base_score *= 1.1  # Optimal hashtag count

            # Add some randomness to simulate real-world variability
            import random
            random.seed(hash(str(post_data)) % 2147483647)
            variability = random.uniform(0.8, 1.2)

            predicted_likes = int(base_score * variability)
            predicted_comments = int(predicted_likes * 0.1 * variability)
            predicted_shares = int(predicted_likes * 0.05 * variability)

            return {
                'predicted_likes': max(0, predicted_likes),
                'predicted_comments': max(0, predicted_comments),
                'predicted_shares': max(0, predicted_shares),
                'engagement_score': predicted_likes + predicted_comments * 2 + predicted_shares * 3,
                'confidence': min(1.0, features['user_follower_count'] / 1000 + 0.3)
            }

        except Exception as e:
            logger.error(f"Error in engagement prediction: {str(e)}")
            return {
                'predicted_likes': 0,
                'predicted_comments': 0,
                'predicted_shares': 0,
                'engagement_score': 0,
                'confidence': 0.1
            }
