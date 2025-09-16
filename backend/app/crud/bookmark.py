from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.models.bookmark import (
    Bookmark, BookmarkCreate, BookmarkUpdate, BookmarkPublic,
    BookmarkFolder, BookmarkFolderCreate, BookmarkFolderUpdate,
    BookmarkType, BookmarkFilter, BookmarkBulkAction
)
from app.models.internship import Internship
from app.models.user import User
from app.crud.base import CRUDBase

class CRUDBookmark(CRUDBase[Bookmark, BookmarkCreate, BookmarkUpdate]):
    """CRUD operations for Bookmark model"""
    
    def get_user_bookmarks(
        self,
        db: Session,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
        order_by: Optional[List[str]] = None
    ) -> Tuple[List[Bookmark], int]:
        """
        Get bookmarks for a specific user with filtering, searching and pagination.
        
        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of filters to apply
            search: Search term to filter results
            order_by: List of fields to order by (prefix with '-' for descending)
            
        Returns:
            Tuple of (bookmarks, total_count)
        """
        query = self._base_query.where(Bookmark.user_id == user_id)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(Bookmark, field):
                    if isinstance(value, list):
                        query = query.where(getattr(Bookmark, field).in_(value))
                    else:
                        query = query.where(getattr(Bookmark, field) == value)
        
        # Apply search
        if search:
            search_conditions = []
            search_fields = [
                'notes', 'tags',
                'internship.title', 'internship.company.name',
                'internship.description'
            ]
            
            for field in search_fields:
                if field == 'tags':
                    # Special handling for array field
                    search_conditions.append(Bookmark.tags.any(search))
                elif '.' in field:
                    # Handle related fields (e.g., internship.title)
                    rel_model, rel_field = field.split('.')
                    if hasattr(Bookmark, rel_model):
                        rel_attr = getattr(Bookmark, rel_model)
                        if hasattr(rel_attr.property.entity.class_, rel_field):
                            search_conditions.append(
                                getattr(rel_attr.property.entity.class_, rel_field)
                                .ilike(f'%{search}%')
                            )
                elif hasattr(Bookmark, field):
                    search_conditions.append(
                        getattr(Bookmark, field).ilike(f'%{search}%')
                    )
            
            if search_conditions:
                query = query.where(or_(*search_conditions))
        
        # Get total count before pagination
        total = db.scalar(
            select([func.count()])
            .select_from(query.subquery())
        ) or 0
        
        # Apply ordering (default to most recently updated first)
        if not order_by:
            order_by = ['-updated_at']
            
        order_clauses = []
        for field in order_by:
            if field.startswith('-'):
                order_field = field[1:]
                if hasattr(Bookmark, order_field):
                    order_clauses.append(desc(getattr(Bookmark, order_field)))
            else:
                if hasattr(Bookmark, field):
                    order_clauses.append(asc(getattr(Bookmark, field)))
        
        if order_clauses:
            query = query.order_by(*order_clauses)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Eager load relationships
        query = query.options(
            joinedload(Bookmark.internship).joinedload(Internship.company),
            joinedload(Bookmark.folder)
        )
        
        results = db.execute(query).unique().scalars().all()
        return results, total
    
    def get_with_details(self, db: Session, id: UUID, user_id: Optional[UUID] = None) -> Optional[Bookmark]:
        """
        Get a bookmark with all its details.
        
        Args:
            db: Database session
            id: Bookmark ID
            user_id: Optional user ID to ensure ownership
            
        Returns:
            Bookmark with relationships loaded
        """
        query = self._base_query.where(Bookmark.id == id)
        
        if user_id:
            query = query.where(Bookmark.user_id == user_id)
        
        query = query.options(
            joinedload(Bookmark.user),
            joinedload(Bookmark.internship).joinedload(Internship.company),
            joinedload(Bookmark.folder)
        )
        
        return db.execute(query).unique().scalar_one_or_none()
    
    def create_with_activity(
        self, 
        db: Session, 
        *, 
        obj_in: BookmarkCreate, 
        user_id: UUID,
        **kwargs
    ) -> Bookmark:
        """
        Create a new bookmark and set up any reminders.
        
        Args:
            db: Database session
            obj_in: Bookmark data
            user_id: ID of the user creating the bookmark
            **kwargs: Additional fields to set on the bookmark
            
        Returns:
            The created bookmark
        """
        try:
            # Convert Pydantic model to dict and add user_id
            create_data = obj_in.dict(exclude_unset=True)
            create_data.update({
                'user_id': user_id,
                **kwargs
            })
            
            # Set reminder if remind_in_days is provided
            if 'remind_in_days' in create_data and create_data['remind_in_days']:
                remind_in_days = create_data.pop('remind_in_days')
                create_data['remind_at'] = datetime.utcnow() + timedelta(days=remind_in_days)
            
            # Create the bookmark
            db_obj = Bookmark(**create_data)
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise
    
    def update_with_activity(
        self,
        db: Session,
        *,
        db_obj: Bookmark,
        obj_in: Union[BookmarkUpdate, Dict[str, Any]],
        user_id: UUID,
        **kwargs
    ) -> Bookmark:
        """
        Update a bookmark and handle reminder updates.
        
        Args:
            db: Database session
            db_obj: The bookmark to update
            obj_in: Update data
            user_id: ID of the user updating the bookmark
            **kwargs: Additional fields to update
            
        Returns:
            The updated bookmark
        """
        try:
            update_data = obj_in.dict(exclude_unset=True) if not isinstance(obj_in, dict) else obj_in
            
            # Handle reminder updates
            if 'remind_in_days' in update_data:
                remind_in_days = update_data.pop('remind_in_days')
                if remind_in_days is not None:
                    update_data['remind_at'] = datetime.utcnow() + timedelta(days=remind_in_days)
                else:
                    update_data['remind_at'] = None
            
            # Update the object
            for field, value in update_data.items():
                if hasattr(db_obj, field) and value is not None:
                    setattr(db_obj, field, value)
            
            # Update timestamps
            db_obj.updated_at = datetime.utcnow()
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise
    
    def add_reminder(
        self,
        db: Session,
        *,
        db_obj: Bookmark,
        days: int,
        notes: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> Bookmark:
        """
        Add or update a reminder for a bookmark.
        
        Args:
            db: Database session
            db_obj: The bookmark to update
            days: Number of days in the future to set the reminder
            notes: Optional notes for the reminder
            user_id: ID of the user setting the reminder
            
        Returns:
            The updated bookmark
        """
        try:
            db_obj.remind_at = datetime.utcnow() + timedelta(days=days)
            if notes:
                db_obj.notes = notes
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise
    
    def clear_reminder(
        self,
        db: Session,
        *,
        db_obj: Bookmark,
        user_id: Optional[UUID] = None
    ) -> Bookmark:
        """
        Clear a bookmark's reminder.
        
        Args:
            db: Database session
            db_obj: The bookmark to update
            user_id: ID of the user clearing the reminder
            
        Returns:
            The updated bookmark
        """
        try:
            db_obj.remind_at = None
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise
    
    def add_tag(
        self,
        db: Session,
        *,
        db_obj: Bookmark,
        tag: str,
        user_id: Optional[UUID] = None
    ) -> Bookmark:
        """
        Add a tag to a bookmark.
        
        Args:
            db: Database session
            db_obj: The bookmark to update
            tag: Tag to add
            user_id: ID of the user adding the tag
            
        Returns:
            The updated bookmark
        """
        try:
            if not db_obj.tags:
                db_obj.tags = []
            
            if tag not in db_obj.tags:
                db_obj.tags.append(tag)
                
                db.add(db_obj)
                db.commit()
                db.refresh(db_obj)
            
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise
    
    def remove_tag(
        self,
        db: Session,
        *,
        db_obj: Bookmark,
        tag: str,
        user_id: Optional[UUID] = None
    ) -> Bookmark:
        """
        Remove a tag from a bookmark.
        
        Args:
            db: Database session
            db_obj: The bookmark to update
            tag: Tag to remove
            user_id: ID of the user removing the tag
            
        Returns:
            The updated bookmark
        """
        try:
            if db_obj.tags and tag in db_obj.tags:
                db_obj.tags.remove(tag)
                
                db.add(db_obj)
                db.commit()
                db.refresh(db_obj)
            
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise
    
    def get_upcoming_reminders(
        self,
        db: Session,
        user_id: UUID,
        days_ahead: int = 7,
        limit: int = 50
    ) -> List[Bookmark]:
        """
        Get upcoming bookmark reminders for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            days_ahead: Number of days to look ahead for reminders
            limit: Maximum number of reminders to return
            
        Returns:
            List of bookmarks with upcoming reminders
        """
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)
        
        query = self._base_query.where(
            and_(
                Bookmark.user_id == user_id,
                Bookmark.remind_at.isnot(None),
                Bookmark.remind_at >= now,
                Bookmark.remind_at <= end_date
            )
        ).options(
            joinedload(Bookmark.internship).joinedload(Internship.company),
            joinedload(Bookmark.folder)
        ).order_by(
            Bookmark.remind_at.asc()
        ).limit(limit)
        
        return db.execute(query).unique().scalars().all()
    
    def process_bulk_action(
        self,
        db: Session,
        *,
        action: BookmarkBulkAction,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Process a bulk action on bookmarks.
        
        Args:
            db: Database session
            action: The bulk action to perform
            user_id: ID of the user performing the action
            
        Returns:
            Dictionary with results of the bulk action
        """
        try:
            # Get the bookmarks to update
            bookmarks = db.execute(
                select(Bookmark)
                .where(
                    and_(
                        Bookmark.id.in_(action.bookmark_ids),
                        Bookmark.user_id == user_id
                    )
                )
            ).scalars().all()
            
            if not bookmarks:
                return {"message": "No bookmarks found for the given IDs", "updated_count": 0}
            
            updated_count = 0
            
            # Process the action
            if action.action == "move_to_folder":
                if not action.folder_id:
                    raise ValueError("folder_id is required for move_to_folder action")
                
                for bookmark in bookmarks:
                    bookmark.folder_id = action.folder_id
                    bookmark.updated_at = datetime.utcnow()
                    db.add(bookmark)
                
                updated_count = len(bookmarks)
                
            elif action.action == "add_tags":
                if not action.tags:
                    raise ValueError("tags are required for add_tags action")
                
                for bookmark in bookmarks:
                    if not bookmark.tags:
                        bookmark.tags = []
                    
                    for tag in action.tags:
                        if tag not in bookmark.tags:
                            bookmark.tags.append(tag)
                    
                    bookmark.updated_at = datetime.utcnow()
                    db.add(bookmark)
                
                updated_count = len(bookmarks)
                
            elif action.action == "remove_tags":
                if not action.tags:
                    raise ValueError("tags are required for remove_tags action")
                
                for bookmark in bookmarks:
                    if not bookmark.tags:
                        continue
                    
                    tags_removed = False
                    for tag in action.tags:
                        if tag in bookmark.tags:
                            bookmark.tags.remove(tag)
                            tags_removed = True
                    
                    if tags_removed:
                        bookmark.updated_at = datetime.utcnow()
                        db.add(bookmark)
                        updated_count += 1
                
            elif action.action == "set_priority":
                if action.priority is None:
                    raise ValueError("priority is required for set_priority action")
                
                for bookmark in bookmarks:
                    bookmark.priority = action.priority
                    bookmark.updated_at = datetime.utcnow()
                    db.add(bookmark)
                
                updated_count = len(bookmarks)
                
            elif action.action == "set_reminder":
                if action.remind_in_days is None:
                    raise ValueError("remind_in_days is required for set_reminder action")
                
                for bookmark in bookmarks:
                    bookmark.remind_at = datetime.utcnow() + timedelta(days=action.remind_in_days)
                    bookmark.updated_at = datetime.utcnow()
                    db.add(bookmark)
                
                updated_count = len(bookmarks)
                
            elif action.action == "clear_reminder":
                for bookmark in bookmarks:
                    if bookmark.remind_at is not None:
                        bookmark.remind_at = None
                        bookmark.updated_at = datetime.utcnow()
                        db.add(bookmark)
                        updated_count += 1
                
            elif action.action == "change_type":
                if action.new_type is None:
                    raise ValueError("new_type is required for change_type action")
                
                for bookmark in bookmarks:
                    bookmark.type = action.new_type
                    bookmark.updated_at = datetime.utcnow()
                    db.add(bookmark)
                
                updated_count = len(bookmarks)
                
            elif action.action == "delete":
                # Hard delete the bookmarks
                for bookmark in bookmarks:
                    db.delete(bookmark)
                
                updated_count = len(bookmarks)
                
            db.commit()
            
            return {
                "message": f"Successfully processed {updated_count} bookmarks",
                "updated_count": updated_count,
                "action": action.action
            }
            
        except Exception as e:
            db.rollback()
            raise


class CRUDBookmarkFolder(CRUDBase[BookmarkFolder, BookmarkFolderCreate, BookmarkFolderUpdate]):
    """CRUD operations for BookmarkFolder model"""
    
    def get_user_folders(
        self,
        db: Session,
        user_id: UUID,
        *,
        include_default: bool = True,
        include_private: bool = True,
        include_shared: bool = False
    ) -> List[BookmarkFolder]:
        """
        Get folders for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user
            include_default: Whether to include default folders
            include_private: Whether to include private folders
            include_shared: Whether to include shared folders
            
        Returns:
            List of bookmark folders
        """
        query = self._base_query.where(BookmarkFolder.user_id == user_id)
        
        conditions = []
        
        if include_default:
            conditions.append(BookmarkFolder.is_default == True)
        
        if include_private:
            conditions.append(
                and_(
                    BookmarkFolder.is_private == True,
                    BookmarkFolder.is_default == False
                )
            )
        
        if include_shared:
            conditions.append(BookmarkFolder.is_private == False)
        
        if conditions:
            query = query.where(or_(*conditions))
        
        query = query.order_by(BookmarkFolder.position.asc(), BookmarkFolder.name.asc())
        
        return db.execute(query).scalars().all()
    
    def get_default_folder(self, db: Session, user_id: UUID) -> BookmarkFolder:
        """
        Get or create the default folder for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            The default bookmark folder
        """
        # Try to get an existing default folder
        folder = db.execute(
            select(BookmarkFolder)
            .where(
                and_(
                    BookmarkFolder.user_id == user_id,
                    BookmarkFolder.is_default == True
                )
            )
        ).scalars().first()
        
        if folder:
            return folder
        
        # Create a default folder if none exists
        default_folder = BookmarkFolder(
            user_id=user_id,
            name="Saved",
            is_default=True,
            is_private=True,
            position=0,
            icon="bookmark"
        )
        
        db.add(default_folder)
        db.commit()
        db.refresh(default_folder)
        
        return default_folder
    
    def update_folder_position(
        self,
        db: Session,
        *,
        db_obj: BookmarkFolder,
        new_position: int,
        user_id: UUID
    ) -> BookmarkFolder:
        """
        Update a folder's position and reorder other folders if needed.
        
        Args:
            db: Database session
            db_obj: The folder to update
            new_position: New position for the folder
            user_id: ID of the user
            
        Returns:
            The updated folder
        """
        try:
            current_position = db_obj.position
            
            if current_position == new_position:
                return db_obj
            
            # Update the position of other folders
            if new_position < current_position:
                # Moving up - increment positions of folders in between
                db.execute(
                    update(BookmarkFolder)
                    .where(
                        and_(
                            BookmarkFolder.user_id == user_id,
                            BookmarkFolder.position >= new_position,
                            BookmarkFolder.position < current_position,
                            BookmarkFolder.id != db_obj.id
                        )
                    )
                    .values(position=BookmarkFolder.position + 1)
                )
            else:
                # Moving down - decrement positions of folders in between
                db.execute(
                    update(BookmarkFolder)
                    .where(
                        and_(
                            BookmarkFolder.user_id == user_id,
                            BookmarkFolder.position > current_position,
                            BookmarkFolder.position <= new_position,
                            BookmarkFolder.id != db_obj.id
                        )
                    )
                    .values(position=BookmarkFolder.position - 1)
                )
            
            # Update the current folder's position
            db_obj.position = new_position
            db_obj.updated_at = datetime.utcnow()
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise
    
    def delete_folder(
        self,
        db: Session,
        *,
        db_obj: BookmarkFolder,
        move_to_folder_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Delete a folder and optionally move its bookmarks to another folder.
        
        Args:
            db: Database session
            db_obj: The folder to delete
            move_to_folder_id: ID of the folder to move bookmarks to
            
        Returns:
            Dictionary with results of the deletion
        """
        try:
            if db_obj.is_default:
                raise ValueError("Cannot delete the default folder")
            
            # Get the bookmarks in this folder
            bookmarks = db.execute(
                select(Bookmark)
                .where(Bookmark.folder_id == db_obj.id)
            ).scalars().all()
            
            # Move bookmarks to the specified folder or the default folder
            target_folder_id = move_to_folder_id
            
            if not target_folder_id and bookmarks:
                # If no target folder specified and there are bookmarks, use the default folder
                default_folder = self.get_default_folder(db, db_obj.user_id)
                target_folder_id = default_folder.id
            
            # Update bookmarks to the new folder
            if target_folder_id and bookmarks:
                db.execute(
                    update(Bookmark)
                    .where(Bookmark.folder_id == db_obj.id)
                    .values(folder_id=target_folder_id)
                )
            
            # Delete the folder
            db.delete(db_obj)
            db.commit()
            
            return {
                "message": "Folder deleted successfully",
                "bookmarks_moved": len(bookmarks) if target_folder_id else 0,
                "target_folder_id": str(target_folder_id) if target_folder_id else None
            }
            
        except SQLAlchemyError as e:
            db.rollback()
            raise


# Create instances of the CRUD classes
bookmark = CRUDBookmark(Bookmark)
bookmark_folder = CRUDBookmarkFolder(BookmarkFolder)
