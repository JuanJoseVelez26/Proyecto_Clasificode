from flask import Blueprint, request, jsonify
from Service.security import security_service
from Service.repository import user_repo
from Models.user import User, UserRole
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists
        if user_repo.get_by_username(data['username']):
            return jsonify({'error': 'Username already exists'}), 409
        
        if user_repo.get_by_email(data['email']):
            return jsonify({'error': 'Email already exists'}), 409
        
        # Validate password strength
        is_strong, message = security_service.validate_password_strength(data['password'])
        if not is_strong:
            return jsonify({'error': message}), 400
        
        # Hash password
        password_hash = security_service.hash_password(data['password'])
        
        # Create user
        user_data = {
            'username': data['username'],
            'email': data['email'],
            'password_hash': password_hash,
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'role': UserRole.VIEWER,  # Default role
            'is_active': True
        }
        
        user = user_repo.create(user_data)
        
        # Generate tokens
        access_token, refresh_token = security_service.generate_tokens(
            user.id, user.username, user.role.value
        )
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        logging.error(f"Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Get user
        user = user_repo.get_by_username(data['username'])
        if not user:
            security_service.log_login_attempt(data['username'], False)
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if account is locked
        if user.is_locked:
            return jsonify({'error': 'Account is temporarily locked'}), 423
        
        # Verify password
        if not security_service.verify_password(data['password'], user.password_hash):
            user.increment_failed_attempts()
            
            # Lock account if too many failed attempts
            if int(user.failed_login_attempts or "0") >= 5:
                user.lock_account(30)  # Lock for 30 minutes
            
            user.save(db)
            security_service.log_login_attempt(data['username'], False)
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Reset failed attempts and update login info
        user.reset_failed_attempts()
        user.increment_login_count()
        user.last_login = request.remote_addr
        user.save(db)
        
        # Generate tokens
        access_token, refresh_token = security_service.generate_tokens(
            user.id, user.username, user.role.value
        )
        
        security_service.log_login_attempt(data['username'], True)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    try:
        data = request.get_json()
        
        if not data.get('refresh_token'):
            return jsonify({'error': 'Refresh token is required'}), 400
        
        # Refresh access token
        access_token = security_service.refresh_access_token(data['refresh_token'])
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        logging.error(f"Token refresh error: {e}")
        return jsonify({'error': str(e)}), 401

@auth_bp.route('/profile', methods=['GET'])
@security_service.require_auth
def get_profile():
    """Get current user profile"""
    try:
        user_id = request.current_user['user_id']
        user = user_repo.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Get profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@security_service.require_auth
def update_profile():
    """Update current user profile"""
    try:
        user_id = request.current_user['user_id']
        user = user_repo.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Allow updating certain fields
        allowed_fields = ['first_name', 'last_name', 'email', 'phone', 'department', 'position', 'bio']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Update full_name if first_name or last_name changed
        if 'first_name' in update_data or 'last_name' in update_data:
            first_name = update_data.get('first_name', user.first_name)
            last_name = update_data.get('last_name', user.last_name)
            update_data['full_name'] = f"{first_name} {last_name}".strip()
        
        # Check email uniqueness if email is being updated
        if 'email' in update_data and update_data['email'] != user.email:
            existing_user = user_repo.get_by_email(update_data['email'])
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Email already exists'}), 409
        
        # Update user
        updated_user = user_repo.update(user.id, update_data)
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': updated_user.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Update profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@security_service.require_auth
def change_password():
    """Change user password"""
    try:
        user_id = request.current_user['user_id']
        user = user_repo.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not security_service.verify_password(data['current_password'], user.password_hash):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password strength
        is_strong, message = security_service.validate_password_strength(data['new_password'])
        if not is_strong:
            return jsonify({'error': message}), 400
        
        # Hash new password
        new_password_hash = security_service.hash_password(data['new_password'])
        
        # Update password
        user_repo.update(user.id, {'password_hash': new_password_hash})
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        logging.error(f"Change password error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
@security_service.require_auth
def logout():
    """Logout user (client should discard tokens)"""
    try:
        # In a more sophisticated implementation, you might want to blacklist the token
        # For now, we just return a success message
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        logging.error(f"Logout error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
