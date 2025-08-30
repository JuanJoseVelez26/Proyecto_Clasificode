from datetime import datetime
from sqlalchemy import Column, String, Boolean, Enum, Text
from sqlalchemy.orm import relationship
import enum
from .base import DeclarativeBase

class UserRole(enum.Enum):
    """User roles enumeration"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class UserStatus(enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class User(DeclarativeBase):
    """User model for authentication and authorization"""
    
    __tablename__ = 'users'
    
    # User identification
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    full_name = Column(String(100), nullable=False)
    
    # User status and role
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional information
    phone = Column(String(20))
    department = Column(String(100))
    position = Column(String(100))
    bio = Column(Text)
    
    # Authentication
    last_login = Column(String(50))  # Store IP address
    login_count = Column(String(50), default="0")
    failed_login_attempts = Column(String(50), default="0")
    locked_until = Column(String(50))  # Store datetime as string
    
    # Relationships
    cases = relationship("Case", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.full_name and (self.first_name or self.last_name):
            self.full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
    
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_analyst(self):
        """Check if user is analyst"""
        return self.role == UserRole.ANALYST
    
    @property
    def is_viewer(self):
        """Check if user is viewer"""
        return self.role == UserRole.VIEWER
    
    @property
    def is_locked(self):
        """Check if user account is locked"""
        if not self.locked_until:
            return False
        try:
            locked_time = datetime.fromisoformat(self.locked_until)
            return datetime.utcnow() < locked_time
        except:
            return False
    
    def increment_login_count(self):
        """Increment login count"""
        try:
            count = int(self.login_count or "0")
            self.login_count = str(count + 1)
        except:
            self.login_count = "1"
    
    def increment_failed_attempts(self):
        """Increment failed login attempts"""
        try:
            count = int(self.failed_login_attempts or "0")
            self.failed_login_attempts = str(count + 1)
        except:
            self.failed_login_attempts = "1"
    
    def reset_failed_attempts(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = "0"
        self.locked_until = None
    
    def lock_account(self, minutes=30):
        """Lock account for specified minutes"""
        lock_time = datetime.utcnow().replace(microsecond=0) + datetime.timedelta(minutes=minutes)
        self.locked_until = lock_time.isoformat()
    
    def to_dict(self):
        """Convert user to dictionary excluding sensitive data"""
        data = super().to_dict()
        # Remove sensitive fields
        data.pop('password_hash', None)
        data.pop('failed_login_attempts', None)
        data.pop('locked_until', None)
        return data
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role.value}')>"
