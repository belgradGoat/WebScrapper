"""
User model for NotebookAI
Apple-inspired user data architecture with security focus
"""

from sqlalchemy import String, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from passlib.context import CryptContext
from typing import Optional, Dict, Any, List
import json

from ..core.database import Base


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """
    User model with Apple-style clean design and security
    """
    __tablename__ = "users"
    
    # Basic user information
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=False
    )
    
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )
    
    # Authentication
    hashed_password: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False
    )
    
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False
    )
    
    # User preferences (Apple's personalization approach)
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=lambda: {
            "theme": "system",  # light, dark, system
            "language": "en",
            "timezone": "UTC",
            "notifications": {
                "email": True,
                "push": True,
                "processing_complete": True,
                "ai_responses": False
            },
            "ai_settings": {
                "default_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
                "context_window": 10
            },
            "privacy": {
                "data_retention_days": 90,
                "analytics_opt_in": True,
                "improvement_opt_in": True
            }
        }
    )
    
    # Usage statistics
    usage_stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=lambda: {
            "files_uploaded": 0,
            "queries_made": 0,
            "storage_used_bytes": 0,
            "last_login": None,
            "total_sessions": 0
        }
    )
    
    # Profile information
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True
    )
    
    bio: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    
    # Relationships (Apple's relational thinking)
    data_sources: Mapped[List["DataSource"]] = relationship(
        "DataSource",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Properties
    @hybrid_property
    def display_name(self) -> str:
        """User's display name with Apple-style fallback"""
        return self.full_name or self.email.split("@")[0]
    
    def verify_password(self, password: str) -> bool:
        """Verify password with secure hashing"""
        return pwd_context.verify(password, self.hashed_password)
    
    def set_password(self, password: str) -> None:
        """Set password with secure hashing"""
        self.hashed_password = pwd_context.hash(password)
    
    def update_usage_stats(self, **kwargs) -> None:
        """Update usage statistics"""
        current_stats = self.usage_stats or {}
        current_stats.update(kwargs)
        self.usage_stats = current_stats
    
    def get_preference(self, key: str, default=None):
        """Get user preference with fallback"""
        if not self.preferences:
            return default
        
        keys = key.split(".")
        value = self.preferences
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set_preference(self, key: str, value) -> None:
        """Set user preference with nested key support"""
        if not self.preferences:
            self.preferences = {}
        
        keys = key.split(".")
        current = self.preferences
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with Apple-style clean output"""
        data = {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_sensitive:
            data.update({
                "is_superuser": self.is_superuser,
                "usage_stats": self.usage_stats,
            })
        
        return data
    
    def __str__(self) -> str:
        return f"User({self.display_name} <{self.email}>)"