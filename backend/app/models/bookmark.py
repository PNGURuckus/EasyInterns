from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TSVECTOR
from pydantic import validator, HttpUrl, EmailStr, constr, conlist
from uuid import UUID, uuid4
from datetime import datetime, date
from enum import Enum, auto

from .base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    ConfigMixin
)

if TYPE_CHECKING:
    from .user import User
    from .internship import Internship

class BookmarkType(str, Enum):
    """Type of bookmark"""
    SAVE_FOR_LATER = "save_for_later"
    FAVORITE = "favorite"
    APPLY_LATER = "apply_later"
    COMPARE = "compare"
    REFERENCE = "reference"
    CUSTOM = "custom"

class BookmarkFolder(BaseModel, TimestampMixin, table=True):
    """Model for organizing bookmarks into folders"""
    __tablename__ = "bookmark_folders"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(..., foreign_key="users.id", index=True)
    name: str = Field(..., max_length=100, description="Name of the folder")
    description: Optional[str] = Field(
        default=None, 
        max_length=500, 
        description="Optional description for the folder"
    )
    is_default: bool = Field(
        default=False, 
        index=True,
        description="Whether this is a default folder (e.g., 'Favorites', 'Applied')"
    )
    is_private: bool = Field(
        default=True,
        description="Whether this folder is private to the user"
    )
    icon: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional icon for the folder (e.g., 'star', 'briefcase')"
    )
    color: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Optional color code for the folder (e.g., '#FF5733')"
    )
    position: int = Field(
        default=0,
        description="Position/order of the folder in the list"
    )
    
    # Relationships
    user: "User" = Relationship(back_populates="bookmark_folders")
    bookmarks: List["Bookmark"] = Relationship(back_populates="folder")
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str
        }

class Bookmark(BaseModel, TimestampMixin, table=True):
    """Model for saving and organizing bookmarked internships"""
    __tablename__ = "bookmarks"
    
    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    
    # Foreign keys
    user_id: UUID = Field(..., foreign_key="users.id", index=True)
    internship_id: UUID = Field(..., foreign_key="internships.id", index=True)
    folder_id: Optional[UUID] = Field(
        default=None, 
        foreign_key="bookmark_folders.id",
        index=True,
        description="Optional folder ID to organize bookmarks"
    )
    
    # Core fields
    type: BookmarkType = Field(
        default=BookmarkType.SAVE_FOR_LATER,
        index=True,
        description="Type of bookmark"
    )
    
    # Metadata
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="User notes about this bookmark"
    )
    
    # Priority/importance (1-5, with 5 being highest)
    priority: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Priority level from 1 (low) to 5 (high)"
    )
    
    # Reminders/Follow-up
    remind_at: Optional[datetime] = Field(
        default=None,
        index=True,
        description="When to remind the user about this bookmark"
    )
    
    # Custom fields (for flexible data storage)
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Custom fields for extended functionality"
    )
    
    # Tags for categorization
    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Tags for categorization and search"
    )
    
    # Relationships
    user: "User" = Relationship(back_populates="bookmarks")
    internship: "Internship" = Relationship(back_populates="bookmarks")
    folder: Optional[BookmarkFolder] = Relationship(back_populates="bookmarks")
    
    # Computed properties
    @property
    def is_reminder_active(self) -> bool:
        """Check if there's an active reminder"""
        if not self.remind_at:
            return False
        return self.remind_at > datetime.utcnow()
    
    @property
    def is_priority_high(self) -> bool:
        """Check if this is a high-priority bookmark"""
        return self.priority >= 4
    
    # Methods
    def add_tag(self, tag: str) -> None:
        """Add a tag to the bookmark"""
        if tag and tag not in self.tags:
            self.tags = self.tags or []
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the bookmark"""
        if tag in (self.tags or []):
            self.tags.remove(tag)
    
    def set_reminder(self, days: int = 7, hours: int = 0, minutes: int = 0) -> None:
        """Set a reminder for this bookmark"""
        self.remind_at = datetime.utcnow() + timedelta(
            days=days,
            hours=hours,
            minutes=minutes
        )
    
    def clear_reminder(self) -> None:
        """Clear any active reminder"""
        self.remind_at = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }

# Pydantic models for API
class BookmarkFolderCreate(SQLModel):
    """Schema for creating a new bookmark folder"""
    name: str = Field(..., max_length=100, description="Name of the folder")
    description: Optional[str] = Field(
        default=None, 
        max_length=500, 
        description="Optional description for the folder"
    )
    is_private: bool = Field(
        default=True,
        description="Whether this folder is private to the user"
    )
    icon: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional icon for the folder"
    )
    color: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Optional color code for the folder"
    )
    position: Optional[int] = Field(
        default=0,
        description="Position/order of the folder in the list"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Summer 2024 Internships",
                "description": "Internships to apply for next summer",
                "is_private": True,
                "icon": "briefcase",
                "color": "#3b82f6",
                "position": 1
            }
        }

class BookmarkFolderUpdate(SQLModel):
    """Schema for updating a bookmark folder"""
    name: Optional[str] = Field(
        default=None, 
        max_length=100, 
        description="New name for the folder"
    )
    description: Optional[str] = Field(
        default=None, 
        max_length=500, 
        description="Updated description for the folder"
    )
    is_private: Optional[bool] = Field(
        default=None,
        description="Whether this folder is private to the user"
    )
    icon: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Updated icon for the folder"
    )
    color: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Updated color code for the folder"
    )
    position: Optional[int] = Field(
        default=None,
        ge=0,
        description="New position/order of the folder"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Summer 2024 Internships - Priority",
                "color": "#ef4444",
                "position": 0
            }
        }

class BookmarkCreate(SQLModel):
    """Schema for creating a new bookmark"""
    internship_id: UUID = Field(..., description="ID of the internship to bookmark")
    type: BookmarkType = Field(
        default=BookmarkType.SAVE_FOR_LATER,
        description="Type of bookmark"
    )
    folder_id: Optional[UUID] = Field(
        default=None, 
        description="ID of the folder to add this bookmark to"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional notes about this bookmark"
    )
    priority: Optional[int] = Field(
        default=3,
        ge=1,
        le=5,
        description="Priority level from 1 (low) to 5 (high)"
    )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        max_items=10,
        description="Tags for categorization and search"
    )
    remind_in_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=90,
        description="Set a reminder for this many days in the future"
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Custom fields for extended functionality"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "internship_id": "123e4567-e89b-12d3-a456-426614174000",
                "type": "apply_later",
                "notes": "Great opportunity at a fast-growing startup",
                "priority": 4,
                "tags": ["backend", "python", "remote"],
                "remind_in_days": 7,
                "custom_fields": {
                    "application_deadline": "2024-03-15",
                    "salary_range": "$30-40/hr"
                }
            }
        }

class BookmarkUpdate(SQLModel):
    """Schema for updating an existing bookmark"""
    type: Optional[BookmarkType] = Field(
        default=None,
        description="Updated type of bookmark"
    )
    folder_id: Optional[UUID] = Field(
        default=None, 
        description="ID of the folder to move this bookmark to"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Updated notes about this bookmark"
    )
    priority: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Updated priority level from 1 (low) to 5 (high)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        max_items=10,
        description="Updated tags for categorization and search"
    )
    remind_at: Optional[datetime] = Field(
        default=None,
        description="When to remind the user about this bookmark"
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated custom fields"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "type": "favorite",
                "priority": 5,
                "notes": "Top choice! Apply before the deadline.",
                "tags": ["backend", "python", "top-priority"],
                "remind_at": "2024-02-15T09:00:00Z"
            }
        }

class BookmarkPublic(SQLModel):
    """Schema for public bookmark data"""
    id: UUID
    type: BookmarkType
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None
    priority: int = 3
    tags: List[str] = []
    remind_at: Optional[datetime] = None
    
    # Related data
    internship: Dict[str, Any]
    folder: Optional[Dict[str, Any]] = None
    
    # Computed fields
    is_reminder_active: bool = False
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }

class BookmarkFilter(SQLModel):
    """Filter options for querying bookmarks"""
    type: Optional[List[BookmarkType]] = Field(
        default=None,
        description="Filter by bookmark type"
    )
    folder_id: Optional[UUID] = Field(
        default=None,
        description="Filter by folder ID"
    )
    priority: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Filter by priority level (1-5)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags (AND match)"
    )
    has_reminder: Optional[bool] = Field(
        default=None,
        description="Filter by whether the bookmark has an active reminder"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search term to filter by internship title, company, or notes"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "type": ["favorite", "apply_later"],
                "priority": 4,
                "tags": ["python", "remote"],
                "has_reminder": True
            }
        }

class BookmarkBulkAction(SQLModel):
    """Schema for bulk actions on bookmarks"""
    bookmark_ids: List[UUID] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of bookmark IDs to perform the action on"
    )
    action: str = Field(
        ...,
        regex="^(move_to_folder|add_tags|remove_tags|set_priority|delete|archive|set_reminder|clear_reminder|change_type)$",
        description="Action to perform"
    )
    folder_id: Optional[UUID] = Field(
        default=None,
        description="Target folder ID (for 'move_to_folder' action)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags to add or remove (for 'add_tags' or 'remove_tags' actions)"
    )
    priority: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Priority level to set (for 'set_priority' action)"
    )
    remind_in_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=90,
        description="Days in the future to set a reminder (for 'set_reminder' action)"
    )
    new_type: Optional[BookmarkType] = Field(
        default=None,
        description="New bookmark type (for 'change_type' action)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "bookmark_ids": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "223e4567-e89b-12d3-a456-426614174002"
                ],
                "action": "add_tags",
                "tags": ["python", "backend"]
            }
        }
