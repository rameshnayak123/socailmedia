
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()

# Association tables for many-to-many relationships
user_followers = Table('user_followers', Base.metadata,
    Column('follower_id', String(50), ForeignKey('users.user_id')),
    Column('followed_id', String(50), ForeignKey('users.user_id'))
)

post_likes = Table('post_likes', Base.metadata,
    Column('user_id', String(50), ForeignKey('users.user_id')),
    Column('post_id', String(50), ForeignKey('posts.post_id'))
)

reel_likes = Table('reel_likes', Base.metadata,
    Column('user_id', String(50), ForeignKey('users.user_id')),
    Column('reel_id', String(50), ForeignKey('reels.reel_id'))
)

class User(Base):
    __tablename__ = 'users'

    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    bio = Column(Text, default='')
    profile_picture_url = Column(String(500), default='')
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    reels_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Relationships
    posts = relationship("Post", back_populates="user")
    reels = relationship("Reel", back_populates="user")
    comments = relationship("Comment", back_populates="user")

    # Many-to-many relationships
    followers = relationship("User", secondary=user_followers,
                           primaryjoin=user_id == user_followers.c.followed_id,
                           secondaryjoin=user_id == user_followers.c.follower_id,
                           back_populates="following")
    following = relationship("User", secondary=user_followers,
                           primaryjoin=user_id == user_followers.c.follower_id,
                           secondaryjoin=user_id == user_followers.c.followed_id,
                           back_populates="followers")

class Post(Base):
    __tablename__ = 'posts'

    post_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.user_id'), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    hashtags = Column(Text, default='')  # JSON string of hashtags
    media_urls = Column(Text, default='')  # JSON string of media URLs
    location = Column(String(255), default='')
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    sentiment_score = Column(Float, default=0.0)
    sentiment_label = Column(String(20), default='neutral')
    is_trending = Column(Boolean, default=False)
    is_promoted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

class Reel(Base):
    __tablename__ = 'reels'

    reel_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.user_id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default='')
    category = Column(String(50), nullable=False)
    video_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), default='')
    duration = Column(Integer, default=30)  # seconds
    hashtags = Column(Text, default='')  # JSON string
    music_id = Column(String(50), default='')
    effects = Column(Text, default='')  # JSON string
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)  # How much of the video users watch
    engagement_rate = Column(Float, default=0.0)
    viral_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    is_trending = Column(Boolean, default=False)
    is_promoted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reels")
    comments = relationship("Comment", back_populates="reel")

class Comment(Base):
    __tablename__ = 'comments'

    comment_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.user_id'), nullable=False)
    post_id = Column(String(50), ForeignKey('posts.post_id'), nullable=True)
    reel_id = Column(String(50), ForeignKey('reels.reel_id'), nullable=True)
    parent_comment_id = Column(String(50), ForeignKey('comments.comment_id'), nullable=True)
    content = Column(Text, nullable=False)
    likes_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    sentiment_score = Column(Float, default=0.0)
    sentiment_label = Column(String(20), default='neutral')
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    reel = relationship("Reel", back_populates="comments")
    parent = relationship("Comment", remote_side="Comment.comment_id")
    replies = relationship("Comment", back_populates="parent")

class UserInteraction(Base):
    __tablename__ = 'user_interactions'

    interaction_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.user_id'), nullable=False)
    content_id = Column(String(50), nullable=False)  # post_id or reel_id
    content_type = Column(String(20), nullable=False)  # 'post' or 'reel'
    interaction_type = Column(String(20), nullable=False)  # 'view', 'like', 'share', 'comment', 'save'
    duration = Column(Float, default=0.0)  # Time spent viewing (for analytics)
    device_type = Column(String(50), default='unknown')
    location = Column(String(255), default='')
    created_at = Column(DateTime, default=datetime.utcnow)

class UserPreference(Base):
    __tablename__ = 'user_preferences'

    preference_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.user_id'), nullable=False)
    category = Column(String(50), nullable=False)
    preference_score = Column(Float, default=0.0)  # Higher score = more interested
    interaction_count = Column(Integer, default=0)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TrendingTopic(Base):
    __tablename__ = 'trending_topics'

    trend_id = Column(String(50), primary_key=True)
    hashtag = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    mentions_count = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    growth_rate = Column(Float, default=0.0)  # Rate of growth in mentions
    location = Column(String(255), default='global')
    start_date = Column(DateTime, default=datetime.utcnow)
    peak_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MLModel(Base):
    __tablename__ = 'ml_models'

    model_id = Column(String(50), primary_key=True)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # 'recommendation', 'sentiment', 'trend_detection'
    version = Column(String(20), nullable=False)
    accuracy_score = Column(Float, default=0.0)
    training_data_size = Column(Integer, default=0)
    last_trained = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    model_parameters = Column(Text, default='')  # JSON string of parameters
    performance_metrics = Column(Text, default='')  # JSON string of metrics
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database utility functions
class DatabaseManager:
    def __init__(self, database_url='sqlite:///social_media.db'):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get database session"""
        return self.SessionLocal()

    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)

# Data Access Layer (DAL)
class UserDAL:
    def __init__(self, session):
        self.session = session

    def create_user(self, user_data):
        user = User(**user_data)
        self.session.add(user)
        self.session.commit()
        return user

    def get_user_by_id(self, user_id):
        return self.session.query(User).filter(User.user_id == user_id).first()

    def get_user_by_username(self, username):
        return self.session.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email):
        return self.session.query(User).filter(User.email == email).first()

    def update_user(self, user_id, updates):
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in updates.items():
                setattr(user, key, value)
            self.session.commit()
        return user

    def delete_user(self, user_id):
        user = self.get_user_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False

class PostDAL:
    def __init__(self, session):
        self.session = session

    def create_post(self, post_data):
        post = Post(**post_data)
        self.session.add(post)
        self.session.commit()
        return post

    def get_post_by_id(self, post_id):
        return self.session.query(Post).filter(Post.post_id == post_id).first()

    def get_posts_by_user(self, user_id, limit=20, offset=0):
        return self.session.query(Post).filter(Post.user_id == user_id).order_by(Post.created_at.desc()).offset(offset).limit(limit).all()

    def get_posts_by_category(self, category, limit=20, offset=0):
        return self.session.query(Post).filter(Post.category == category).order_by(Post.created_at.desc()).offset(offset).limit(limit).all()

    def get_trending_posts(self, limit=20):
        return self.session.query(Post).filter(Post.is_trending == True).order_by(Post.engagement_rate.desc()).limit(limit).all()

    def update_post(self, post_id, updates):
        post = self.get_post_by_id(post_id)
        if post:
            for key, value in updates.items():
                setattr(post, key, value)
            self.session.commit()
        return post

    def delete_post(self, post_id):
        post = self.get_post_by_id(post_id)
        if post:
            self.session.delete(post)
            self.session.commit()
            return True
        return False

class ReelDAL:
    def __init__(self, session):
        self.session = session

    def create_reel(self, reel_data):
        reel = Reel(**reel_data)
        self.session.add(reel)
        self.session.commit()
        return reel

    def get_reel_by_id(self, reel_id):
        return self.session.query(Reel).filter(Reel.reel_id == reel_id).first()

    def get_reels_by_user(self, user_id, limit=20, offset=0):
        return self.session.query(Reel).filter(Reel.user_id == user_id).order_by(Reel.created_at.desc()).offset(offset).limit(limit).all()

    def get_trending_reels(self, limit=20):
        return self.session.query(Reel).filter(Reel.is_trending == True).order_by(Reel.viral_score.desc()).limit(limit).all()

    def get_reels_for_user_feed(self, user_preferences, limit=20):
        # This would implement personalized feed logic based on user preferences
        return self.session.query(Reel).order_by(Reel.engagement_rate.desc()).limit(limit).all()

    def update_reel(self, reel_id, updates):
        reel = self.get_reel_by_id(reel_id)
        if reel:
            for key, value in updates.items():
                setattr(reel, key, value)
            self.session.commit()
        return reel

    def delete_reel(self, reel_id):
        reel = self.get_reel_by_id(reel_id)
        if reel:
            self.session.delete(reel)
            self.session.commit()
            return True
        return False
