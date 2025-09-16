"""
Common schemas used across the application
"""
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum

# Generic Type Variables
T = TypeVar('T')

class Message(BaseModel):
    """Generic message response schema"""
    detail: str = Field(..., description="A message describing the result of the operation")

class MessageResponse(Message):
    """Standard API response with a message"""
    pass

class Status(str, Enum):
    """Common status values"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class ResponseModel(BaseModel, Generic[T]):
    """Generic response model for API endpoints"""
    status: Status = Field(..., description="Status of the operation")
    message: str = Field(..., description="Human-readable message about the operation result")
    data: Optional[Union[T, List[T], Dict[str, Any]]] = Field(
        default=None, 
        description="Response data payload"
    )

class PaginatedResponse(ResponseModel[T]):
    """Paginated response model"""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

class BaseFilter(BaseModel):
    """Base filter for API queries"""
    limit: int = Field(20, ge=1, le=100, description="Number of items to return")
    offset: int = Field(0, ge=0, description="Number of items to skip")
    search: Optional[str] = Field(None, description="Search term")
    sort: Optional[str] = Field(None, description="Sort field and direction, e.g. 'name:asc' or 'created_at:desc'")

class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""
    created_at: Optional[datetime] = Field(
        None, 
        description="When the record was created"
    )
    updated_at: Optional[datetime] = Field(
        None, 
        description="When the record was last updated"
    )

class SoftDeleteMixin(BaseModel):
    """Mixin for soft delete functionality"""
    is_deleted: bool = Field(
        False, 
        description="Whether the record is marked as deleted"
    )
    deleted_at: Optional[datetime] = Field(
        None, 
        description="When the record was marked as deleted"
    )
