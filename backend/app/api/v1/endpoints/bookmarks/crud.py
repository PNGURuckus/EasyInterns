from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.models.bookmark import BookmarkType
from app.schemas.common import Message
from app.schemas.bookmark import (
    BookmarkCreate, BookmarkUpdate, BookmarkPublic,
    BookmarkFolderCreate, BookmarkFolderUpdate, BookmarkBulkAction
)

router = APIRouter()

# Bookmark endpoints
@router.get("/", response_model=List[BookmarkPublic])
def read_bookmarks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
    folder_id: Optional[UUID] = None,
    type: Optional[BookmarkType] = None,
    tags: Optional[List[str]] = Query(None),
    is_archived: Optional[bool] = None,
    has_reminder: Optional[bool] = None,
    search: Optional[str] = None,
    order_by: Optional[List[str]] = Query(None)
) -> Any:
    """
    Retrieve bookmarks with filtering, searching, and pagination.
    """
    # Build filters
    filters = {}
    if folder_id is not None:
        filters["folder_id"] = folder_id
    if type is not None:
        filters["type"] = type
    if tags is not None:
        filters["tags"] = tags
    if is_archived is not None:
        filters["is_archived"] = is_archived
    if has_reminder is not None:
        filters["remind_at_is_not_none"] = has_reminder
    
    # Get bookmarks
    bookmarks, total = crud.bookmark.get_user_bookmarks(
        db, 
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        filters=filters,
        search=search,
        order_by=order_by or ["-updated_at"]
    )
    
    # Add X-Total-Count header for pagination
    response = JSONResponse(
        content=[bookmark.dict() for bookmark in bookmarks]
    )
    response.headers["X-Total-Count"] = str(total)
    
    return response

@router.post("/", response_model=BookmarkPublic, status_code=status.HTTP_201_CREATED)
def create_bookmark(
    *,
    db: Session = Depends(deps.get_db),
    bookmark_in: BookmarkCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new bookmark.
    """
    # Check if the internship exists
    if bookmark_in.internship_id:
        internship = crud.internship.get(db, id=bookmark_in.internship_id)
        if not internship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The internship does not exist.",
            )
    
    # Check if the folder exists and belongs to the user
    if bookmark_in.folder_id:
        folder = crud.bookmark_folder.get(db, id=bookmark_in.folder_id)
        if not folder or folder.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The folder does not exist or you don't have permission to use it.",
            )
    
    # Create the bookmark
    bookmark = crud.bookmark.create_with_activity(
        db=db,
        obj_in=bookmark_in,
        user_id=current_user.id
    )
    
    return bookmark

@router.get("/{bookmark_id}", response_model=BookmarkPublic)
def read_bookmark(
    *,
    db: Session = Depends(deps.get_db),
    bookmark_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a bookmark by ID.
    """
    bookmark = crud.bookmark.get_with_details(
        db, 
        id=bookmark_id, 
        user_id=current_user.id
    )
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )
    
    return bookmark

@router.put("/{bookmark_id}", response_model=BookmarkPublic)
def update_bookmark(
    *,
    db: Session = Depends(deps.get_db),
    bookmark_id: UUID,
    bookmark_in: BookmarkUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a bookmark.
    """
    bookmark = crud.bookmark.get(db, id=bookmark_id, user_id=current_user.id)
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )
    
    # Update the bookmark
    bookmark = crud.bookmark.update(
        db, 
        db_obj=bookmark, 
        obj_in=bookmark_in
    )
    
    return bookmark

@router.delete("/{bookmark_id}", response_model=Message)
def delete_bookmark(
    *,
    db: Session = Depends(deps.get_db),
    bookmark_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a bookmark.
    """
    bookmark = crud.bookmark.get(db, id=bookmark_id, user_id=current_user.id)
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )
    
    crud.bookmark.remove(db, id=bookmark_id)
    
    return {"message": "Bookmark deleted successfully"}

@router.post("/bulk", response_model=dict)
def bulk_bookmark_actions(
    *,
    db: Session = Depends(deps.get_db),
    action: BookmarkBulkAction,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Perform bulk actions on bookmarks.
    """
    return crud.bookmark.process_bulk_action(
        db,
        action=action,
        user_id=current_user.id
    )

@router.get("/upcoming/reminders", response_model=List[dict])
def get_upcoming_reminders(
    *,
    db: Session = Depends(deps.get_db),
    days_ahead: int = 7,
    limit: int = 10,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get upcoming bookmark reminders.
    """
    return crud.bookmark.get_upcoming_reminders(
        db,
        user_id=current_user.id,
        days_ahead=days_ahead,
        limit=limit
    )

# Bookmark Folder endpoints
@router.get("/folders/", response_model=List[schemas.BookmarkFolder])
def read_folders(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    include_shared: bool = False,
) -> Any:
    """
    Retrieve bookmark folders for the current user.
    """
    return crud.bookmark_folder.get_user_folders(
        db,
        user_id=current_user.id,
        include_shared=include_shared
    )

@router.post("/folders/", response_model=schemas.BookmarkFolder, status_code=status.HTTP_201_CREATED)
def create_folder(
    *,
    db: Session = Depends(deps.get_db),
    folder_in: BookmarkFolderCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new bookmark folder.
    """
    # Check if a folder with the same name already exists for this user
    existing_folder = db.query(models.BookmarkFolder).filter(
        models.BookmarkFolder.user_id == current_user.id,
        models.BookmarkFolder.name == folder_in.name
    ).first()
    
    if existing_folder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A folder with this name already exists.",
        )
    
    # Create the folder
    folder = crud.bookmark_folder.create(
        db=db,
        obj_in={
            **folder_in.dict(exclude_unset=True),
            "user_id": current_user.id
        }
    )
    
    return folder

@router.get("/folders/{folder_id}", response_model=schemas.BookmarkFolder)
def read_folder(
    *,
    db: Session = Depends(deps.get_db),
    folder_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a bookmark folder by ID.
    """
    folder = crud.bookmark_folder.get(db, id=folder_id, user_id=current_user.id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )
    
    return folder

@router.put("/folders/{folder_id}", response_model=schemas.BookmarkFolder)
def update_folder(
    *,
    db: Session = Depends(deps.get_db),
    folder_id: UUID,
    folder_in: BookmarkFolderUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a bookmark folder.
    """
    folder = crud.bookmark_folder.get(db, id=folder_id, user_id=current_user.id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )
    
    # Prevent updating the default folder's name
    if folder.is_default and folder_in.name and folder.name != folder_in.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot rename the default folder.",
        )
    
    # Update the folder
    folder = crud.bookmark_folder.update(
        db, 
        db_obj=folder, 
        obj_in=folder_in
    )
    
    return folder

@router.delete("/folders/{folder_id}", response_model=Message)
def delete_folder(
    *,
    db: Session = Depends(deps.get_db),
    folder_id: UUID,
    move_to_folder_id: Optional[UUID] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a bookmark folder.
    """
    folder = crud.bookmark_folder.get(db, id=folder_id, user_id=current_user.id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )
    
    # Delete the folder
    result = crud.bookmark_folder.delete_folder(
        db,
        db_obj=folder,
        move_to_folder_id=move_to_folder_id
    )
    
    return {"message": result["message"]}

@router.put("/folders/{folder_id}/position", response_model=schemas.BookmarkFolder)
def update_folder_position(
    *,
    db: Session = Depends(deps.get_db),
    folder_id: UUID,
    position: int = Body(..., embed=True),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a folder's position.
    """
    folder = crud.bookmark_folder.get(db, id=folder_id, user_id=current_user.id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )
    
    # Update the folder position
    folder = crud.bookmark_folder.update_folder_position(
        db,
        db_obj=folder,
        new_position=position,
        user_id=current_user.id
    )
    
    return folder
