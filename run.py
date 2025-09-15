#!/usr/bin/env python3
"""
Social Media API Launch Script
Initializes the Flask application with ML models and sample data
"""

import os
import sys
import json
from datetime import datetime

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import flask
        import numpy
        import pandas
        import sklearn
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def initialize_database():
    """Initialize database with sample data if needed"""
    print("🔧 Initializing database...")

    # Check if test data exists
    if not os.path.exists('test_data.json'):
        print("📊 Generating test data...")
        from generate_test_data import TestDataGenerator
        generator = TestDataGenerator()
        generator.save_test_data()

    print("✅ Database initialization complete")

def start_application():
    """Start the Flask application"""
    print("🚀 Starting Social Media API with Machine Learning...")
    print("📍 API will be available at: http://localhost:5000")
    print("📚 Available endpoints:")
    print("   - POST /api/profile (Create user)")
    print("   - GET  /api/profile (Get user profile)")  
    print("   - POST /api/post (Create post)")
    print("   - GET  /api/post (Get posts)")
    print("   - POST /api/reels (Create reel)")
    print("   - GET  /api/reels (Get reels)")
    print("   - GET  /api/recommendations (Get recommendations)")
    print("   - POST /api/sentiment (Analyze sentiment)")
    print("   - GET  /api/user-behavior (Analyze user behavior)")
    print("   - GET  /api/analytics/dashboard (Analytics)")
    print("")
    print("🤖 ML Features enabled:")
    print("   ✓ Content Recommendation System")
    print("   ✓ Sentiment Analysis") 
    print("   ✓ User Behavior Prediction")
    print("   ✓ Trend Detection")
    print("   ✓ Engagement Prediction")
    print("")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)

    # Import and run the Flask app
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

def main():
    """Main execution function"""
    print("=" * 60)
    print("🎵 SOCIAL MEDIA API WITH MACHINE LEARNING 🤖")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)

    print(f"✅ Python {sys.version.split()[0]} detected")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Initialize database and sample data
    initialize_database()

    # Start the application
    try:
        start_application()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("Thank you for using Social Media API! 👋")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
