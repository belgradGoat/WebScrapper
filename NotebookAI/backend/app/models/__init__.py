"""
Models package for NotebookAI
Apple-inspired data model organization
"""

from .user import User
from .data_source import DataSource, DataSourceType, ProcessingStatus
from .chat import ChatSession, ChatMessage, MessageRole
from .processing import ProcessingJob, JobType, JobStatus, JobPriority

# Export all models for easy importing
__all__ = [
    "User",
    "DataSource",
    "DataSourceType", 
    "ProcessingStatus",
    "ChatSession",
    "ChatMessage",
    "MessageRole",
    "ProcessingJob",
    "JobType",
    "JobStatus",
    "JobPriority",
]