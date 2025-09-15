from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, get_jwt_identity
from flask_cors import CORS
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
import json
from config import Config
from ml_algorithms import RecommendationEngine, ContentModerator, ImageProcessor
import logging

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*")
cors = CORS(app)

# Initialize ML components
recommendation_engine = RecommendationEngine()
content_moderator = ContentModerator()
image_processor = ImageProcessor()

# Import models and routes after app initialization
from models import User, Post, Story, Like, Comment, Follow, Message, Notification
from routes.auth import auth_bp
from routes.posts import posts_bp
from routes.users import users_bp
from routes.messages import messages_bp
from routes.recommendations import recommendations_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(posts_bp, url_prefix='/api/posts')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(messages_bp, url_prefix='/api/messages')
app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Socket.IO events for real-time features
@socketio.on('connect')
def on_connect():
    logger.info(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def on_disconnect():
    logger.info(f'Client disconnected: {request.sid}')

@socketio.on('join_room')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'Joined room {room}'}, room=request.sid)

@socketio.on('leave_room')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'Left room {room}'}, room=request.sid)

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = data['username']
    timestamp = datetime.utcnow().isoformat()

    emit('new_message', {
        'message': message,
        'username': username,
        'timestamp': timestamp
    }, room=room)

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# Create database tables
@app.before_first_request
def create_tables():
    db.create_all()
    logger.info('Database tables created successfully')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', Config.PORT))
    socketio.run(app, host=Config.HOST, port=port, debug=Config.DEBUG)
