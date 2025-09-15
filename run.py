#!/usr/bin/env python3
"""
Instagram Clone - Flask Application Entry Point
Run this script to start the Instagram clone backend server.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app import app, socketio, db
from models import User, Post, Story, Like, Comment, Follow, Message, Notification

def create_sample_data():
    """Create sample data for development/testing"""
    if User.query.count() == 0:
        print("Creating sample data...")

        # Create sample users
        users = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'full_name': 'Admin User',
                'password': 'password123',
                'bio': 'System Administrator 👨‍💻 Welcome to Instagram Clone!',
                'is_verified': True
            },
            {
                'username': 'johndoe',
                'email': 'john@example.com',
                'full_name': 'John Doe',
                'password': 'password123',
                'bio': 'Photography enthusiast 📸 Travel lover ✈️ Coffee addict ☕',
                'profile_picture': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face'
            },
            {
                'username': 'sarahwilson',
                'email': 'sarah@example.com',
                'full_name': 'Sarah Wilson',
                'password': 'password123',
                'bio': 'Artist 🎨 Dreamer ✨ Living my best life 💫',
                'profile_picture': 'https://images.unsplash.com/photo-1494790108755-2616b2dc4d96?w=150&h=150&fit=crop&crop=face'
            },
            {
                'username': 'mikejohnson',
                'email': 'mike@example.com',
                'full_name': 'Mike Johnson',
                'password': 'password123',
                'bio': 'Fitness trainer 💪 Motivating people to reach their goals 🏋️‍♂️',
                'profile_picture': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
                'is_verified': True
            }
        ]

        created_users = []
        for user_data in users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                bio=user_data.get('bio', ''),
                profile_picture=user_data.get('profile_picture'),
                is_verified=user_data.get('is_verified', False)
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            created_users.append(user)

        db.session.commit()
        print(f"Created {len(created_users)} sample users")

        # Create sample posts
        sample_posts = [
            {
                'user': created_users[1],  # johndoe
                'image_url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=600&fit=crop',
                'caption': 'Beautiful sunset at the beach! 🌅 #sunset #beach #photography',
                'location': 'Malibu Beach'
            },
            {
                'user': created_users[2],  # sarahwilson
                'image_url': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=600&h=600&fit=crop',
                'caption': 'New artwork in progress! 🎨 What do you think? #art #painting #creative',
                'location': 'Art Studio'
            },
            {
                'user': created_users[3],  # mikejohnson
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&h=600&fit=crop',
                'caption': 'Morning workout done! 💪 Remember, consistency is key! #fitness #workout #motivation',
                'location': 'Gold\'s Gym'
            }
        ]

        for post_data in sample_posts:
            post = Post(
                user_id=post_data['user'].id,
                image_url=post_data['image_url'],
                caption=post_data['caption'],
                location=post_data['location']
            )
            db.session.add(post)

        db.session.commit()
        print(f"Created {len(sample_posts)} sample posts")

        # Create some sample interactions
        posts = Post.query.all()
        if posts:
            # Add some likes
            like1 = Like(user_id=created_users[1].id, post_id=posts[1].id)  # John likes Sarah's post
            like2 = Like(user_id=created_users[2].id, post_id=posts[0].id)  # Sarah likes John's post  
            like3 = Like(user_id=created_users[3].id, post_id=posts[0].id)  # Mike likes John's post

            db.session.add_all([like1, like2, like3])

            # Add some comments
            comment1 = Comment(
                user_id=created_users[2].id, 
                post_id=posts[0].id, 
                text="Stunning shot! 😍"
            )
            comment2 = Comment(
                user_id=created_users[3].id, 
                post_id=posts[0].id, 
                text="Love the colors!"
            )
            comment3 = Comment(
                user_id=created_users[1].id, 
                post_id=posts[1].id, 
                text="Amazing work! Keep it up 👏"
            )

            db.session.add_all([comment1, comment2, comment3])

            # Add some follows
            follow1 = Follow(follower_id=created_users[1].id, followed_id=created_users[2].id)  # John follows Sarah
            follow2 = Follow(follower_id=created_users[2].id, followed_id=created_users[1].id)  # Sarah follows John
            follow3 = Follow(follower_id=created_users[3].id, followed_id=created_users[1].id)  # Mike follows John

            db.session.add_all([follow1, follow2, follow3])

            db.session.commit()
            print("Created sample interactions (likes, comments, follows)")

        print("Sample data creation completed!")

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        create_sample_data()

    # Configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'

    print(f"""
    🚀 Instagram Clone Backend Server Starting...

    📍 Server URL: http://{host}:{port}
    🔧 Debug Mode: {'Enabled' if debug else 'Disabled'}
    📊 Database: {app.config['SQLALCHEMY_DATABASE_URI']}

    📋 Available Endpoints:
    • GET  /api/health - Health check
    • POST /api/auth/register - User registration
    • POST /api/auth/login - User login
    • GET  /api/posts/ - Get feed posts
    • POST /api/posts/ - Create new post
    • GET  /api/users/profile - Get current user profile
    • GET  /api/recommendations/posts - Get recommended posts

    💡 Test Accounts:
    • admin@example.com / password123
    • john@example.com / password123
    • sarah@example.com / password123
    • mike@example.com / password123

    🔗 Frontend should connect to: http://{host}:{port}

    ⚠️  Remember to configure environment variables in .env file!
    """)

    # Start the server with SocketIO support
    try:
        socketio.run(
            app, 
            host=host, 
            port=port, 
            debug=debug,
            allow_unsafe_werkzeug=True  # For development only
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
