from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
import random

from sqlalchemy.orm import Session

from app import models, schemas
from app.models.bookmark import BookmarkType
from app.crud import bookmark as crud_bookmark


def create_random_bookmark(
    db: Session,
    user_id: int,
    folder_id: Optional[UUID] = None,
    type: Optional[str] = None,
    **kwargs
) -> models.Bookmark:
    """Create a random bookmark for testing"""
    if type is None:
        type = random.choice(list(BookmarkType)).value
    
    # Create a random internship if not provided
    if "internship_id" not in kwargs:
        from .internship import create_random_internship
        internship = create_random_internship(db)
        kwargs["internship_id"] = internship.id
    
    # Create a random folder if not provided
    if folder_id is None:
        folder = create_random_bookmark_folder(db, user_id=user_id)
        folder_id = folder.id
    
    bookmark_in = schemas.BookmarkCreate(
        folder_id=folder_id,
        type=type,
        notes=f"Test bookmark notes {uuid4()}",
        tags=[f"tag-{i}" for i in range(random.randint(0, 3))],
        **kwargs
    )
    
    return crud_bookmark.bookmark.create_with_activity(
        db=db,
        obj_in=bookmark_in,
        user_id=user_id
    )


def create_random_bookmark_folder(
    db: Session,
    user_id: int,
    name: Optional[str] = None,
    is_private: bool = True,
    **kwargs
) -> models.BookmarkFolder:
    """Create a random bookmark folder for testing"""
    if name is None:
        name = f"Test Folder {uuid4().hex[:8]}"
    
    folder_in = schemas.BookmarkFolderCreate(
        name=name,
        description=f"Test folder description {uuid4()}",
        is_private=is_private,
        icon=random.choice(["folder", "bookmark", "star", "briefcase"]),
        color=random.choice(["blue", "green", "red", "yellow", "purple", "pink"]),
        position=0,
        **kwargs
    )
    
    return crud_bookmark.bookmark_folder.create(
        db=db,
        obj_in={
            **folder_in.dict(exclude_unset=True),
            "user_id": user_id
        }
    )


def add_bookmark_reminder(
    db: Session,
    bookmark_id: UUID,
    user_id: int,
    days: int = 7,
    notes: Optional[str] = None
) -> models.Bookmark:
    """Add a reminder to a bookmark"""
    return crud_bookmark.bookmark.add_reminder(
        db=db,
        db_obj=crud_bookmark.bookmark.get(db, id=bookmark_id, user_id=user_id),
        days=days,
        notes=notes or f"Reminder for bookmark {bookmark_id}",
        user_id=user_id
    )


def add_bookmark_tag(
    db: Session,
    bookmark_id: UUID,
    user_id: int,
    tag: str
) -> models.Bookmark:
    """Add a tag to a bookmark"""
    return crud_bookmark.bookmark.add_tag(
        db=db,
        db_obj=crud_bookmark.bookmark.get(db, id=bookmark_id, user_id=user_id),
        tag=tag,
        user_id=user_id
    )


def process_bulk_bookmark_action(
    db: Session,
    bookmark_ids: List[UUID],
    user_id: int,
    action: str,
    **kwargs
) -> Dict[str, Any]:
    """Process a bulk action on bookmarks"""
    action_obj = schemas.BookmarkBulkAction(
        bookmark_ids=bookmark_ids,
        action=action,
        **kwargs
    )
    
    return crud_bookmark.bookmark.process_bulk_action(
        db=db,
        action=action_obj,
        user_id=user_id
    )
