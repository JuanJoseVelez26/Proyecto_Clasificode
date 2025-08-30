import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 86400)))
    JWT_ERROR_MESSAGE_KEY = 'message'
    
    # API Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    
    # AI/ML Services Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.8))
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/clasificode.log')
    
    # Email Configuration (optional)
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    # CORS Configuration
    CORS_ORIGINS = [
        'http://localhost:8080',
        'http://127.0.0.1:8080',
        'http://localhost:3000',
        'http://127.0.0.1:3000'
    ]
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # Security
    BCRYPT_LOG_ROUNDS = 12
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "200 per day;50 per hour;10 per minute"
    
    # Cache Configuration
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://test_user:test_pass@localhost:5432/test_db'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    config_name = os.getenv('FLASK_ENV', 'development')
    return config.get(config_name, config['default'])
