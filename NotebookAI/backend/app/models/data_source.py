"""
Data Source model for NotebookAI
Apple-inspired data management with comprehensive metadata
"""

from sqlalchemy import String, Text, Integer, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

from ..core.database import Base


class DataSourceType(str, Enum):
    """Data source types with Apple-style clarity"""
    FILE = "file"
    URL = "url"
    TEXT = "text"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"


class ProcessingStatus(str, Enum):
    """Processing status with clear state management"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataSource(Base):
    """
    Data source model with Apple-style comprehensive metadata
    """
    __tablename__ = "data_sources"
    
    # Basic information
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        index=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    
    # Source details
    source_type: Mapped[DataSourceType] = mapped_column(
        SQLEnum(DataSourceType),
        nullable=False,
        index=True
    )
    
    original_filename: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )
    
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True
    )
    
    url: Mapped[Optional[str]] = mapped_column(
        String(1000), 
        nullable=True
    )
    
    content: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    
    # File metadata
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )
    
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True
    )
    
    file_extension: Mapped[Optional[str]] = mapped_column(
        String(10), 
        nullable=True
    )
    
    # Processing information
    status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False,
        index=True
    )
    
    processing_progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    
    # Content analysis results
    extracted_text: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    
    text_chunks_count: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )
    
    # Metadata (Apple's attention to detail)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=lambda: {
            "word_count": 0,
            "language": "en",
            "key_topics": [],
            "summary": "",
            "quality_score": 0.0,
            "readability_score": 0.0,
            "processing_time_seconds": 0,
            "ai_analysis": {}
        }
    )
    
    # Vector embedding information
    embedding_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False
    )
    
    vector_count: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )
    
    # User relationship
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="data_sources"
    )
    
    # Processing jobs relationship
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob",
        back_populates="data_source",
        cascade="all, delete-orphan"
    )
    
    # Properties
    @hybrid_property
    def is_processed(self) -> bool:
        """Check if data source is fully processed"""
        return self.status == ProcessingStatus.COMPLETED
    
    @hybrid_property
    def file_size_mb(self) -> Optional[float]:
        """File size in megabytes"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None
    
    @hybrid_property
    def display_name(self) -> str:
        """Display name with fallback"""
        return self.name or self.original_filename or f"Data Source {str(self.id)[:8]}"
    
    def update_processing_status(
        self, 
        status: ProcessingStatus, 
        progress: int = None,
        error_message: str = None
    ) -> None:
        """Update processing status with Apple-style state management"""
        self.status = status
        
        if progress is not None:
            self.processing_progress = min(max(progress, 0), 100)
        
        if error_message:
            self.error_message = error_message
        elif status == ProcessingStatus.COMPLETED:
            self.processing_progress = 100
            self.error_message = None
    
    def update_metadata(self, **kwargs) -> None:
        """Update metadata with merge support"""
        current_metadata = self.metadata or {}
        current_metadata.update(kwargs)
        self.metadata = current_metadata
    
    def get_metadata_value(self, key: str, default=None):
        """Get metadata value with fallback"""
        if not self.metadata:
            return default
        return self.metadata.get(key, default)
    
    def can_be_processed(self) -> bool:
        """Check if data source can be processed"""
        return self.status in [ProcessingStatus.PENDING, ProcessingStatus.FAILED]
    
    def get_content_preview(self, max_length: int = 200) -> str:
        """Get content preview with Apple-style truncation"""
        if self.extracted_text:
            text = self.extracted_text.strip()
            if len(text) <= max_length:
                return text
            return text[:max_length].rstrip() + "..."
        
        if self.content:
            text = self.content.strip()
            if len(text) <= max_length:
                return text
            return text[:max_length].rstrip() + "..."
        
        return "No content available"
    
    def to_dict(self, include_content: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with Apple-style clean output"""
        data = {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "source_type": self.source_type.value,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "file_size_mb": self.file_size_mb,
            "mime_type": self.mime_type,
            "file_extension": self.file_extension,
            "status": self.status.value,
            "processing_progress": self.processing_progress,
            "error_message": self.error_message,
            "text_chunks_count": self.text_chunks_count,
            "metadata": self.metadata,
            "embedding_status": self.embedding_status,
            "vector_count": self.vector_count,
            "content_preview": self.get_content_preview(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_content:
            data.update({
                "url": self.url,
                "content": self.content,
                "extracted_text": self.extracted_text,
            })
        
        return data
    
    def __str__(self) -> str:
        return f"DataSource({self.display_name} - {self.source_type.value})"