import os
from datetime import timedelta

class Config:
    """Configuration class for the Instagram Clone application"""

    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    # Server configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))

    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/instagram_clone')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }

    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # File upload configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your-app-password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'your-email@gmail.com')

    # Redis configuration for caching and sessions
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL

    # AWS S3 configuration for file storage
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET', 'instagram-clone-media')
    AWS_S3_REGION = os.environ.get('AWS_S3_REGION', 'us-west-2')

    # Social media API keys for integration
    FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # Machine Learning configuration
    ML_MODEL_PATH = os.environ.get('ML_MODEL_PATH', 'ml_models')
    RECOMMENDATION_BATCH_SIZE = int(os.environ.get('RECOMMENDATION_BATCH_SIZE', 50))
    CONTENT_MODERATION_THRESHOLD = float(os.environ.get('CONTENT_MODERATION_THRESHOLD', 0.7))

    # Rate limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "100 per hour"

    # Pagination
    POSTS_PER_PAGE = int(os.environ.get('POSTS_PER_PAGE', 20))
    USERS_PER_PAGE = int(os.environ.get('USERS_PER_PAGE', 20))
    MESSAGES_PER_PAGE = int(os.environ.get('MESSAGES_PER_PAGE', 50))

    # Feature flags
    ENABLE_STORIES = os.environ.get('ENABLE_STORIES', 'True').lower() == 'true'
    ENABLE_DIRECT_MESSAGES = os.environ.get('ENABLE_DIRECT_MESSAGES', 'True').lower() == 'true'
    ENABLE_PUSH_NOTIFICATIONS = os.environ.get('ENABLE_PUSH_NOTIFICATIONS', 'True').lower() == 'true'
    ENABLE_ML_RECOMMENDATIONS = os.environ.get('ENABLE_ML_RECOMMENDATIONS', 'True').lower() == 'true'

    # Security settings
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS', 12))
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))

    # Content settings
    MAX_CAPTION_LENGTH = int(os.environ.get('MAX_CAPTION_LENGTH', 2200))
    MAX_BIO_LENGTH = int(os.environ.get('MAX_BIO_LENGTH', 150))
    STORY_EXPIRY_HOURS = int(os.environ.get('STORY_EXPIRY_HOURS', 24))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instagram_clone_dev.db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instagram_clone_test.db'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
