
import os
from datetime import timedelta

class Config:
    """Base configuration class"""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///social_media.db'

    # File upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))  # 50MB

    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_EXPIRES_HOURS', 24)))

    # ML Model settings
    MODEL_PATH = os.environ.get('MODEL_PATH') or 'models/'
    RETRAIN_INTERVAL_HOURS = int(os.environ.get('RETRAIN_INTERVAL_HOURS', 24))
    MIN_TRAINING_DATA_SIZE = int(os.environ.get('MIN_TRAINING_DATA_SIZE', 100))

    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT') or '100 per hour'

    # Content moderation
    ENABLE_CONTENT_MODERATION = os.environ.get('ENABLE_CONTENT_MODERATION', 'True').lower() == 'true'
    TOXICITY_THRESHOLD = float(os.environ.get('TOXICITY_THRESHOLD', 0.7))

    # Media processing
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    MAX_VIDEO_DURATION_SECONDS = int(os.environ.get('MAX_VIDEO_DURATION', 300))  # 5 minutes
    VIDEO_QUALITY_LEVELS = ['720p', '1080p']

    # Recommendation system
    RECOMMENDATION_BATCH_SIZE = int(os.environ.get('RECOMMENDATION_BATCH_SIZE', 20))
    CONTENT_SIMILARITY_THRESHOLD = float(os.environ.get('SIMILARITY_THRESHOLD', 0.3))
    USER_COLD_START_THRESHOLD = int(os.environ.get('COLD_START_THRESHOLD', 5))  # Min interactions

    # Analytics
    ANALYTICS_RETENTION_DAYS = int(os.environ.get('ANALYTICS_RETENTION_DAYS', 90))
    ENABLE_REAL_TIME_ANALYTICS = os.environ.get('ENABLE_REAL_TIME_ANALYTICS', 'True').lower() == 'true'

    # Social features
    MAX_FOLLOWERS_PER_REQUEST = int(os.environ.get('MAX_FOLLOWERS_PER_REQUEST', 100))
    MAX_HASHTAGS_PER_POST = int(os.environ.get('MAX_HASHTAGS_PER_POST', 10))
    MAX_POST_LENGTH = int(os.environ.get('MAX_POST_LENGTH', 2200))

    # Trending algorithm
    TRENDING_DECAY_FACTOR = float(os.environ.get('TRENDING_DECAY_FACTOR', 0.95))
    TRENDING_TIME_WINDOW_HOURS = int(os.environ.get('TRENDING_TIME_WINDOW_HOURS', 24))
    MIN_INTERACTIONS_FOR_TRENDING = int(os.environ.get('MIN_INTERACTIONS_FOR_TRENDING', 10))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    DATABASE_URL = 'sqlite:///social_media_dev.db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Use environment variables for production settings

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'  # In-memory database for tests
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
