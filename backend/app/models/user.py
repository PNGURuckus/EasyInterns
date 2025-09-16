from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from sqlalchemy import Boolean
from sqlalchemy.dialects.postgresql import JSONB
from .base import BaseModel, UserRole
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .internship import Internship, Bookmark, Application, Resume

class UserBase(SQLModel):
    email: str = Field(..., unique=True, index=True, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.USER)
    is_active: bool = Field(default=True)
    preferences: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    
class User(UserBase, BaseModel, table=True):
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    hashed_password: str = Field(nullable=False, max_length=255)
    email_verified: bool = Field(default=False)
    last_login: Optional[datetime] = None
    is_active: bool = Field(default=True, sa_column=Column("is_active", type_=Boolean, default=True))
    is_superuser: bool = Field(default=False, sa_column=Column("is_superuser", type_=Boolean, default=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, 
                              sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    internships: List["Internship"] = Relationship(back_populates="posted_by")
    bookmarks: List["Bookmark"] = Relationship(back_populates="user")
    applications: List["Application"] = Relationship(back_populates="user")
    resumes: List["Resume"] = Relationship(back_populates="user")
    
    def verify_password(self, password: str) -> bool:
        from app.core.security import verify_password
        return verify_password(password, self.hashed_password)
        
    def __repr__(self) -> str:
        return f"<User {self.email}>"

class UserCreate(SQLModel):
    email: str
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str
    is_active: bool = True
    is_superuser: bool = False
    role: UserRole = UserRole.USER
    
class UserUpdate(SQLModel):
    full_name: Optional[str] = None
    preferences: Optional[dict] = None
    
class UserInDB(UserBase):
    id: UUID
    hashed_password: str
    email_verified: bool
    
class UserPublic(UserBase):
    id: UUID
    email_verified: bool
    created_at: datetime
    
class Token(SQLModel):
    access_token: str
    token_type: str
    
class TokenPayload(SQLModel):
    sub: Optional[UUID] = None
    
class NewPassword(SQLModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
class ResetPassword(SQLModel):
    email: str
