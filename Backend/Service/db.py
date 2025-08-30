from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        logging.info("Database tables created successfully")

def get_session():
    """Get database session"""
    return db.session

def close_session():
    """Close database session"""
    db.session.close()

def commit_session():
    """Commit database session"""
    db.session.commit()

def rollback_session():
    """Rollback database session"""
    db.session.rollback()

class DatabaseManager:
    """Database manager for common operations"""
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        init_db(app)
    
    def get_engine(self):
        """Get SQLAlchemy engine"""
        return db.engine
    
    def get_session(self):
        """Get database session"""
        return db.session
    
    def execute_query(self, query, params=None):
        """Execute raw SQL query"""
        with db.engine.connect() as connection:
            result = connection.execute(query, params or {})
            return result
    
    def health_check(self):
        """Check database health"""
        try:
            db.session.execute("SELECT 1")
            return True
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
            return False
