import jwt
import bcrypt
from datetime import datetime, timedelta
from flask import current_app, request
from functools import wraps
import logging

class SecurityService:
    """Security service for authentication and authorization"""
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.secret_key = app.config.get('SECRET_KEY')
        self.jwt_secret = app.config.get('JWT_SECRET_KEY')
        self.jwt_access_expires = app.config.get('JWT_ACCESS_TOKEN_EXPIRES')
        self.jwt_refresh_expires = app.config.get('JWT_REFRESH_TOKEN_EXPIRES')
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def generate_tokens(self, user_id, username, role):
        """Generate access and refresh tokens"""
        access_token = jwt.encode(
            {
                'user_id': user_id,
                'username': username,
                'role': role,
                'exp': datetime.utcnow() + self.jwt_access_expires,
                'iat': datetime.utcnow(),
                'type': 'access'
            },
            self.jwt_secret,
            algorithm='HS256'
        )
        
        refresh_token = jwt.encode(
            {
                'user_id': user_id,
                'exp': datetime.utcnow() + self.jwt_refresh_expires,
                'iat': datetime.utcnow(),
                'type': 'refresh'
            },
            self.jwt_secret,
            algorithm='HS256'
        )
        
        return access_token, refresh_token
    
    def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
    
    def refresh_access_token(self, refresh_token):
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.jwt_secret, algorithms=['HS256'])
            if payload.get('type') != 'refresh':
                raise Exception("Invalid token type")
            
            # Generate new access token
            access_token = jwt.encode(
                {
                    'user_id': payload['user_id'],
                    'exp': datetime.utcnow() + self.jwt_access_expires,
                    'iat': datetime.utcnow(),
                    'type': 'access'
                },
                self.jwt_secret,
                algorithm='HS256'
            )
            
            return access_token
        except jwt.ExpiredSignatureError:
            raise Exception("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid refresh token")
    
    def get_current_user_id(self):
        """Get current user ID from token"""
        token = self.get_token_from_request()
        if not token:
            return None
        
        payload = self.verify_token(token)
        return payload.get('user_id')
    
    def get_token_from_request(self):
        """Extract token from request"""
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return None
    
    def require_auth(self, f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = self.get_token_from_request()
            if not token:
                return {'message': 'Missing authentication token'}, 401
            
            try:
                payload = self.verify_token(token)
                request.current_user = payload
                return f(*args, **kwargs)
            except Exception as e:
                return {'message': str(e)}, 401
        
        return decorated_function
    
    def require_role(self, required_role):
        """Decorator to require specific role"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                token = self.get_token_from_request()
                if not token:
                    return {'message': 'Missing authentication token'}, 401
                
                try:
                    payload = self.verify_token(token)
                    user_role = payload.get('role')
                    
                    if user_role != required_role and user_role != 'admin':
                        return {'message': 'Insufficient permissions'}, 403
                    
                    request.current_user = payload
                    return f(*args, **kwargs)
                except Exception as e:
                    return {'message': str(e)}, 401
            
            return decorated_function
        return decorator
    
    def log_login_attempt(self, username, success, ip_address=None):
        """Log login attempt"""
        if not ip_address:
            ip_address = request.remote_addr
        
        log_message = f"Login attempt for user '{username}' from {ip_address}: {'SUCCESS' if success else 'FAILED'}"
        logging.info(log_message)
    
    def validate_password_strength(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        return True, "Password is strong"

# Global security service instance
security_service = SecurityService()
