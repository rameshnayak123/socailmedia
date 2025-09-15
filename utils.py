
import hashlib
import jwt
import bcrypt
from datetime import datetime, timedelta
import re
import string
import random
from PIL import Image
import cv2
import numpy as np

class SecurityUtils:
    """Security utilities for the social media app"""

    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)

    @staticmethod
    def verify_password(password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)

    @staticmethod
    def generate_jwt_token(user_id, secret_key, expires_in_hours=24):
        """Generate JWT token for user authentication"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')

    @staticmethod
    def verify_jwt_token(token, secret_key):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

class ContentUtils:
    """Utilities for content processing"""

    @staticmethod
    def extract_hashtags(text):
        """Extract hashtags from text"""
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, text)
        return [tag[1:].lower() for tag in hashtags]  # Remove # and convert to lowercase

    @staticmethod
    def extract_mentions(text):
        """Extract user mentions from text"""
        mention_pattern = r'@\w+'
        mentions = re.findall(mention_pattern, text)
        return [mention[1:].lower() for mention in mentions]  # Remove @ and convert to lowercase

    @staticmethod
    def clean_text(text):
        """Clean text for analysis"""
        # Remove special characters and extra whitespace
        cleaned = re.sub(r'[^\w\s#@]', '', text)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    @staticmethod
    def generate_content_id():
        """Generate unique content ID"""
        timestamp = str(int(datetime.now().timestamp()))
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        return f"{timestamp}_{random_str}"

    @staticmethod
    def calculate_readability_score(text):
        """Calculate simple readability score"""
        words = text.split()
        sentences = text.split('.')

        if len(sentences) == 0 or len(words) == 0:
            return 0

        avg_words_per_sentence = len(words) / len(sentences)
        avg_characters_per_word = sum(len(word) for word in words) / len(words)

        # Simple readability formula
        score = max(0, 100 - (avg_words_per_sentence * 1.5 + avg_characters_per_word * 2))
        return min(score, 100)

class MediaUtils:
    """Utilities for media processing"""

    @staticmethod
    def generate_thumbnail(video_path, output_path, timestamp=1.0):
        """Generate thumbnail from video"""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()

            if ret:
                cv2.imwrite(output_path, frame)
                return True
            return False
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return False

    @staticmethod
    def compress_image(image_path, output_path, quality=85, max_size=(1920, 1080)):
        """Compress and resize image"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Resize if too large
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save with compression
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                return True
        except Exception as e:
            print(f"Error compressing image: {e}")
            return False

    @staticmethod
    def get_video_duration(video_path):
        """Get video duration in seconds"""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps
            cap.release()
            return duration
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0

    @staticmethod
    def validate_video_format(video_path):
        """Validate video format and properties"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False, "Cannot open video file"

            # Check basic properties
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            cap.release()

            # Validation rules
            if duration > 300:  # Max 5 minutes
                return False, "Video too long (max 5 minutes)"

            if duration < 1:  # Min 1 second
                return False, "Video too short (min 1 second)"

            if width < 480 or height < 480:
                return False, "Video resolution too low (min 480px)"

            if width > 4096 or height > 4096:
                return False, "Video resolution too high (max 4K)"

            return True, "Valid video"

        except Exception as e:
            return False, f"Error validating video: {e}"

class AnalyticsUtils:
    """Utilities for analytics and metrics"""

    @staticmethod
    def calculate_engagement_rate(likes, comments, shares, views):
        """Calculate engagement rate"""
        if views == 0:
            return 0

        total_engagement = likes + comments * 2 + shares * 3
        return (total_engagement / views) * 100

    @staticmethod
    def calculate_growth_rate(current_value, previous_value):
        """Calculate growth rate percentage"""
        if previous_value == 0:
            return 100 if current_value > 0 else 0

        return ((current_value - previous_value) / previous_value) * 100

    @staticmethod
    def get_time_periods():
        """Get common time periods for analytics"""
        now = datetime.now()
        return {
            'today': (now.replace(hour=0, minute=0, second=0, microsecond=0), now),
            'yesterday': (
                now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1),
                now.replace(hour=0, minute=0, second=0, microsecond=0)
            ),
            'this_week': (now - timedelta(days=now.weekday()), now),
            'last_week': (
                now - timedelta(days=now.weekday() + 7),
                now - timedelta(days=now.weekday())
            ),
            'this_month': (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now),
            'last_30_days': (now - timedelta(days=30), now)
        }

    @staticmethod
    def generate_analytics_report(data, time_period):
        """Generate analytics report for given time period"""
        start_time, end_time = time_period

        filtered_data = [
            item for item in data 
            if start_time <= datetime.fromisoformat(item['created_at']) <= end_time
        ]

        if not filtered_data:
            return {
                'total_items': 0,
                'total_engagement': 0,
                'avg_engagement': 0,
                'top_performers': []
            }

        total_engagement = sum(
            item.get('likes', 0) + item.get('comments', 0) + item.get('shares', 0)
            for item in filtered_data
        )

        avg_engagement = total_engagement / len(filtered_data)

        # Sort by engagement
        top_performers = sorted(
            filtered_data,
            key=lambda x: x.get('likes', 0) + x.get('comments', 0) + x.get('shares', 0),
            reverse=True
        )[:5]

        return {
            'total_items': len(filtered_data),
            'total_engagement': total_engagement,
            'avg_engagement': avg_engagement,
            'top_performers': top_performers
        }

class ValidationUtils:
    """Input validation utilities"""

    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_username(username):
        """Validate username format"""
        if len(username) < 3 or len(username) > 30:
            return False, "Username must be 3-30 characters long"

        if not re.match(r'^[a-zA-Z0-9._-]+$', username):
            return False, "Username can only contain letters, numbers, dots, underscores, and hyphens"

        return True, "Valid username"

    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"

        return True, "Valid password"

    @staticmethod
    def sanitize_input(text, max_length=1000):
        """Sanitize user input"""
        if not text:
            return ""

        # Remove potentially harmful characters
        sanitized = re.sub(r'[<>"\']', '', str(text))

        # Limit length
        sanitized = sanitized[:max_length]

        # Remove extra whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        return sanitized

# Configuration utilities
class ConfigUtils:
    """Configuration and environment utilities"""

    DEFAULT_CONFIG = {
        'MAX_FILE_SIZE': 50 * 1024 * 1024,  # 50MB
        'ALLOWED_VIDEO_FORMATS': ['.mp4', '.avi', '.mov', '.mkv'],
        'ALLOWED_IMAGE_FORMATS': ['.jpg', '.jpeg', '.png', '.gif'],
        'MAX_VIDEO_DURATION': 300,  # 5 minutes
        'MAX_HASHTAGS_PER_POST': 10,
        'MAX_POST_LENGTH': 2200,
        'JWT_EXPIRY_HOURS': 24,
        'RATE_LIMIT_PER_HOUR': 100
    }

    @staticmethod
    def get_config(key, default=None):
        """Get configuration value"""
        return ConfigUtils.DEFAULT_CONFIG.get(key, default)

    @staticmethod
    def validate_file_upload(file, file_type='image'):
        """Validate file upload"""
        if file_type == 'image':
            allowed_formats = ConfigUtils.get_config('ALLOWED_IMAGE_FORMATS')
        elif file_type == 'video':
            allowed_formats = ConfigUtils.get_config('ALLOWED_VIDEO_FORMATS')
        else:
            return False, "Unknown file type"

        # Check file extension
        filename = file.filename.lower()
        if not any(filename.endswith(fmt) for fmt in allowed_formats):
            return False, f"File format not allowed. Allowed: {', '.join(allowed_formats)}"

        # Check file size (this would need to be implemented based on the file object)
        max_size = ConfigUtils.get_config('MAX_FILE_SIZE')
        # Note: Actual file size checking would depend on the specific file object implementation

        return True, "Valid file"
