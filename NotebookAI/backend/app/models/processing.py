"""
Processing models for NotebookAI
Apple-inspired background task and job management
"""

from sqlalchemy import String, Text, Integer, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta
import uuid

from ..core.database import Base


class JobType(str, Enum):
    """Job types with Apple-style categorization"""
    FILE_UPLOAD = "file_upload"
    TEXT_EXTRACTION = "text_extraction"
    URL_SCRAPING = "url_scraping"
    MEDIA_TRANSCRIPTION = "media_transcription"
    EMBEDDING_GENERATION = "embedding_generation"
    AI_ANALYSIS = "ai_analysis"
    DATA_EXPORT = "data_export"


class JobStatus(str, Enum):
    """Job status with clear state management"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(str, Enum):
    """Job priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ProcessingJob(Base):
    """
    Processing job model with Apple-style task management
    """
    __tablename__ = "processing_jobs"
    
    # Job identification
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    job_type: Mapped[JobType] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    # Job configuration
    priority: Mapped[JobPriority] = mapped_column(
        String(20),
        default=JobPriority.NORMAL,
        nullable=False,
        index=True
    )
    
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False
    )
    
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    timeout_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    # Job status and progress
    status: Mapped[JobStatus] = mapped_column(
        String(20),
        default=JobStatus.PENDING,
        nullable=False,
        index=True
    )
    
    progress_percentage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    progress_message: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Execution tracking
    started_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    
    execution_time_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    # Results and errors
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Job parameters and metadata
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=lambda: {}
    )
    
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=lambda: {
            "worker_id": "",
            "queue_name": "default",
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
            "disk_io_bytes": 0,
            "network_io_bytes": 0
        }
    )
    
    # Relationships
    data_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    data_source: Mapped[Optional["DataSource"]] = relationship(
        "DataSource",
        back_populates="processing_jobs"
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    parent_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("processing_jobs.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Self-referential relationship for job chains
    child_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob",
        cascade="all, delete-orphan"
    )
    
    # Properties
    @hybrid_property
    def is_active(self) -> bool:
        """Check if job is currently active"""
        return self.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.RETRYING]
    
    @hybrid_property
    def is_finished(self) -> bool:
        """Check if job is finished (completed or failed)"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    @hybrid_property
    def duration(self) -> Optional[timedelta]:
        """Calculate job duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return datetime.utcnow() - self.started_at
        return None
    
    @hybrid_property
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return (
            self.status == JobStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    @hybrid_property
    def estimated_completion_time(self) -> Optional[datetime]:
        """Estimate completion time based on progress"""
        if self.status == JobStatus.RUNNING and self.started_at and self.progress_percentage > 0:
            elapsed = datetime.utcnow() - self.started_at
            estimated_total = elapsed * (100 / self.progress_percentage)
            return self.started_at + estimated_total
        return None
    
    def start_job(self, worker_id: str = "") -> None:
        """Start job execution with Apple-style state management"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.progress_percentage = 0
        self.progress_message = "Starting job..."
        
        # Update metadata
        current_metadata = self.metadata or {}
        current_metadata["worker_id"] = worker_id
        current_metadata["started_at"] = self.started_at.isoformat()
        self.metadata = current_metadata
    
    def update_progress(self, percentage: int, message: str = "") -> None:
        """Update job progress"""
        self.progress_percentage = min(max(percentage, 0), 100)
        if message:
            self.progress_message = message
    
    def complete_job(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Complete job successfully"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100
        self.progress_message = "Job completed successfully"
        
        if result:
            self.result = result
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def fail_job(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Fail job with error information"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        
        if error_details:
            self.error_details = error_details
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def cancel_job(self, reason: str = "") -> None:
        """Cancel job execution"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.progress_message = f"Job cancelled: {reason}" if reason else "Job cancelled"
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def retry_job(self) -> bool:
        """Retry failed job"""
        if not self.can_retry:
            return False
        
        self.status = JobStatus.RETRYING
        self.retry_count += 1
        self.error_message = None
        self.error_details = None
        self.progress_percentage = 0
        self.progress_message = f"Retrying job (attempt {self.retry_count + 1})"
        
        return True
    
    def get_parameter(self, key: str, default=None):
        """Get job parameter with fallback"""
        if not self.parameters:
            return default
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value) -> None:
        """Set job parameter"""
        if not self.parameters:
            self.parameters = {}
        self.parameters[key] = value
    
    def to_dict(self, include_details: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with Apple-style clean output"""
        data = {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "job_type": self.job_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "progress_percentage": self.progress_percentage,
            "progress_message": self.progress_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "can_retry": self.can_retry,
            "is_active": self.is_active,
            "is_finished": self.is_finished,
            "execution_time_seconds": self.execution_time_seconds,
            "estimated_completion_time": self.estimated_completion_time.isoformat() if self.estimated_completion_time else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        
        if include_details:
            data.update({
                "parameters": self.parameters,
                "result": self.result,
                "error_message": self.error_message,
                "error_details": self.error_details,
                "metadata": self.metadata,
                "data_source_id": str(self.data_source_id) if self.data_source_id else None,
                "parent_job_id": str(self.parent_job_id) if self.parent_job_id else None,
            })
        
        return data
    
    def __str__(self) -> str:
        return f"ProcessingJob({self.name} - {self.job_type.value} - {self.status.value})"