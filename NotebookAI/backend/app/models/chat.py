"""
Chat models for NotebookAI
Apple-inspired conversational AI architecture
"""

from sqlalchemy import String, Text, ForeignKey, JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

from ..core.database import Base


class MessageRole(str, Enum):
    """Message roles with Apple-style clarity"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(Base):
    """
    Chat session model with Apple-style conversation management
    """
    __tablename__ = "chat_sessions"
    
    # Basic information
    title: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    
    # Session configuration
    ai_model: Mapped[str] = mapped_column(
        String(100),
        default="gpt-4",
        nullable=False
    )
    
    temperature: Mapped[float] = mapped_column(
        Float,
        default=0.7,
        nullable=False
    )
    
    max_tokens: Mapped[int] = mapped_column(
        Integer,
        default=2000,
        nullable=False
    )
    
    # Session statistics
    message_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    total_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # Session metadata
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=lambda: {
            "context_sources": [],
            "active_data_sources": [],
            "session_tags": [],
            "quality_ratings": [],
            "avg_response_time": 0.0,
            "language": "en"
        }
    )
    
    # User relationship
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user: Mapped["User"] = relationship(
        "User",
        back_populates="chat_sessions"
    )
    
    # Messages relationship
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
    
    # Properties
    @hybrid_property
    def display_title(self) -> str:
        """Display title with Apple-style fallback"""
        if self.title:
            return self.title
        
        # Generate title from first user message
        user_messages = [msg for msg in self.messages if msg.role == MessageRole.USER]
        if user_messages:
            first_message = user_messages[0].content
            if len(first_message) > 50:
                return first_message[:47] + "..."
            return first_message
        
        return f"Chat Session {str(self.id)[:8]}"
    
    @hybrid_property
    def estimated_cost(self) -> float:
        """Estimate session cost based on tokens"""
        # Rough cost estimation (adjust based on actual pricing)
        cost_per_1k_tokens = 0.002  # Example rate
        return (self.total_tokens / 1000) * cost_per_1k_tokens
    
    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ChatMessage":
        """Add message to session with Apple-style simplicity"""
        message = ChatMessage(
            session_id=self.id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self.message_count += 1
        return message
    
    def update_stats(self, tokens_used: int = 0) -> None:
        """Update session statistics"""
        self.total_tokens += tokens_used
        
        # Update metadata
        current_metadata = self.metadata or {}
        current_metadata["last_activity"] = self.updated_at.isoformat()
        self.metadata = current_metadata
    
    def get_context_messages(self, limit: int = 10) -> List["ChatMessage"]:
        """Get recent messages for context"""
        return self.messages[-limit:] if self.messages else []
    
    def to_dict(self, include_messages: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with Apple-style clean output"""
        data = {
            "id": str(self.id),
            "title": self.title,
            "display_title": self.display_title,
            "description": self.description,
            "ai_model": self.ai_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_messages:
            data["messages"] = [msg.to_dict() for msg in self.messages]
        
        return data


class ChatMessage(Base):
    """
    Chat message model with Apple-style message handling
    """
    __tablename__ = "chat_messages"
    
    # Message content
    role: Mapped[MessageRole] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    # Response metadata
    tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    response_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    # Message metadata
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=lambda: {
            "sources_cited": [],
            "data_sources_used": [],
            "model_version": "",
            "temperature": 0.7,
            "finish_reason": "",
            "user_rating": None,
            "feedback": ""
        }
    )
    
    # Session relationship
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages"
    )
    
    # Properties
    @hybrid_property
    def is_user_message(self) -> bool:
        """Check if message is from user"""
        return self.role == MessageRole.USER
    
    @hybrid_property
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant"""
        return self.role == MessageRole.ASSISTANT
    
    @hybrid_property
    def content_preview(self) -> str:
        """Content preview with Apple-style truncation"""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."
    
    def add_citation(self, source_id: str, source_name: str) -> None:
        """Add source citation to message"""
        current_metadata = self.metadata or {}
        sources = current_metadata.get("sources_cited", [])
        
        citation = {
            "source_id": source_id,
            "source_name": source_name,
            "cited_at": self.created_at.isoformat()
        }
        
        if citation not in sources:
            sources.append(citation)
            current_metadata["sources_cited"] = sources
            self.metadata = current_metadata
    
    def set_user_rating(self, rating: int, feedback: str = "") -> None:
        """Set user rating for message (1-5 scale)"""
        current_metadata = self.metadata or {}
        current_metadata["user_rating"] = max(1, min(5, rating))
        current_metadata["feedback"] = feedback
        self.metadata = current_metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with Apple-style clean output"""
        return {
            "id": str(self.id),
            "role": self.role.value,
            "content": self.content,
            "content_preview": self.content_preview,
            "tokens_used": self.tokens_used,
            "response_time_ms": self.response_time_ms,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __str__(self) -> str:
        return f"ChatMessage({self.role.value}: {self.content_preview})"