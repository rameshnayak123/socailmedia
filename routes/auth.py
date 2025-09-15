from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity
from werkzeug.exceptions import BadRequest
from app import db, bcrypt
from models import User
import re
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    pattern = r'^[a-zA-Z0-9._]{3,30}$'
    return re.match(pattern, username) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['username', 'email', 'full_name', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        username = data['username'].lower()
        email = data['email'].lower()
        full_name = data['full_name']
        password = data['password']

        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400

        # Validate username format
        if not validate_username(username):
            return jsonify({'error': 'Invalid username format. Use 3-30 characters, letters, numbers, dots, and underscores only'}), 400

        # Validate password strength
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400

        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            if existing_user.username == username:
                return jsonify({'error': 'Username already exists'}), 409
            else:
                return jsonify({'error': 'Email already registered'}), 409

        # Create new user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            bio=data.get('bio', ''),
            phone_number=data.get('phone_number'),
            website=data.get('website')
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Create access token
        access_token = create_access_token(identity=new_user.id)

        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400

        username_or_email = data['username'].lower()
        password = data['password']

        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401

        if not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Create access token
        access_token = create_access_token(identity=user.id)

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict(include_email=True)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/verify-token', methods=['GET'])
def verify_token():
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()

        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'Invalid token'}), 401

        return jsonify({
            'valid': True,
            'user': user.to_dict(include_email=True)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Token verification failed', 'valid': False}), 401

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email', '').lower()

        if not email or not validate_email(email):
            return jsonify({'error': 'Valid email is required'}), 400

        user = User.query.filter_by(email=email).first()

        # Always return success to prevent email enumeration
        return jsonify({
            'message': 'If an account with this email exists, a password reset link has been sent.'
        }), 200

    except Exception as e:
        return jsonify({'error': 'Password reset request failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    try:
        verify_jwt_in_request()

        # In a production app, you might want to blacklist the token
        # For now, we'll just return a success message
        return jsonify({'message': 'Logged out successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Logout failed'}), 500
