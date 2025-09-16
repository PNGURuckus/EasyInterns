from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast, Tuple, TypeVar, Sequence, Callable
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, parse_obj_as
from sqlalchemy import select, update, delete, func, or_, and_, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload, selectinload, Load, contains_eager
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql.expression import Select
from sqlmodel import SQLModel, select as sqlmodel_select
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Type variables
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
T = TypeVar('T')

# Custom exceptions
class CRUDError(Exception):
    """Base exception for CRUD operations"""
    pass

class NotFoundError(CRUDError):
    """Raised when a record is not found"""
    pass

class AlreadyExistsError(CRUDError):
    """Raised when trying to create a record that already exists"""
    pass

class DatabaseError(CRUDError):
    """Raised for database-related errors"""
    pass

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base CRUD (Create, Read, Update, Delete) operations with sync and async support.
    
    This class provides common database operations that can be extended by model-specific
    CRUD classes. It supports both synchronous and asynchronous database sessions.
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUDBase with the given model.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
        self._base_query = sqlmodel_select(self.model).where(
            getattr(self.model, 'is_deleted', True).is_(False)
            if hasattr(self.model, 'is_deleted') 
            else True
        )
    
    # Basic CRUD Operations (Synchronous)
    # =================================
    
    def get(self, db: Session, id: Union[UUID, str, int], **kwargs) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            db: Database session
            id: Record ID (UUID, string, or integer)
            **kwargs: Additional filter criteria
            
        Returns:
            The model instance if found, None otherwise
        """
        try:
            query = self._base_query.where(self.model.id == id)
            
            # Apply additional filters if provided
            for key, value in kwargs.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
            
            return db.exec(query).first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} with id {id}: {str(e)}")
            raise DatabaseError(f"Failed to get {self.model.__name__}: {str(e)}")
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        order_by: Optional[List[str]] = None,
        **kwargs
    ) -> Tuple[List[ModelType], int]:
        """
        Get multiple records with pagination, filtering, and sorting.
        
        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Dictionary of field-value pairs to filter by
            search: Search term to filter results
            search_fields: List of fields to search in
            order_by: List of fields to order by (prefix with '-' for descending)
            **kwargs: Additional filter criteria
            
        Returns:
            Tuple of (records, total_count)
        """
        try:
            query = self._base_query
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if value is not None and hasattr(self.model, field):
                        if isinstance(value, list):
                            query = query.where(getattr(self.model, field).in_(value))
                        else:
                            query = query.where(getattr(self.model, field) == value)
            
            # Apply search
            if search and search_fields:
                search_conditions = []
                for field in search_fields:
                    if hasattr(self.model, field):
                        search_conditions.append(
                            getattr(self.model, field).ilike(f"%{search}%")
                        )
                if search_conditions:
                    query = query.where(or_(*search_conditions))
            
            # Get total count (before pagination)
            count_query = select(func.count()).select_from(query.subquery())
            total = db.scalar(count_query)
            
            # Apply ordering
            if order_by:
                order_clauses = []
                for field in order_by:
                    if field.startswith('-'):
                        order_field = field[1:]
                        if hasattr(self.model, order_field):
                            order_clauses.append(desc(getattr(self.model, order_field)))
                    else:
                        if hasattr(self.model, field):
                            order_clauses.append(asc(getattr(self.model, field)))
                
                if order_clauses:
                    query = query.order_by(*order_clauses)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            results = db.exec(query).all()
            return results, total or 0
            
        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__} records: {str(e)}")
            raise DatabaseError(f"Failed to get {self.model.__name__} records: {str(e)}")
    
    def create(self, db: Session, *, obj_in: Union[CreateSchemaType, Dict[str, Any]], **kwargs) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Input data as Pydantic model or dict
            **kwargs: Additional fields to set on the new record
            
        Returns:
            The created model instance
            
        Raises:
            AlreadyExistsError: If a record with the same unique fields exists
            DatabaseError: For other database errors
        """
        try:
            # Convert Pydantic model to dict if needed
            if not isinstance(obj_in, dict):
                create_data = obj_in.dict(exclude_unset=True)
            else:
                create_data = obj_in.copy()
            
            # Add any additional fields
            create_data.update(kwargs)
            
            # Create and save the new record
            db_obj = self.model(**create_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error creating {self.model.__name__}: {str(e)}")
            raise AlreadyExistsError(f"{self.model.__name__} with these details already exists")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to create {self.model.__name__}: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating {self.model.__name__}: {str(e)}")
            raise CRUDError(f"Failed to create {self.model.__name__}")
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: Optional[ModelType] = None,
        obj_id: Optional[Union[UUID, str, int]] = None,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        **kwargs
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db: Database session
            db_obj: Existing model instance to update (if not provided, obj_id must be provided)
            obj_id: ID of the record to update (if db_obj is not provided)
            obj_in: Update data as Pydantic model or dict
            **kwargs: Additional fields to update
            
        Returns:
            The updated model instance
            
        Raises:
            NotFoundError: If the record doesn't exist
            DatabaseError: For database errors
        """
        try:
            # Get the object if only ID is provided
            if db_obj is None and obj_id is not None:
                db_obj = self.get(db, obj_id)
                if not db_obj:
                    raise NotFoundError(f"{self.model.__name__} not found")
            
            # Convert Pydantic model to dict if needed
            if not isinstance(obj_in, dict):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = obj_in.copy()
            
            # Add any additional fields
            update_data.update(kwargs)
            
            # Update the object
            for field, value in update_data.items():
                if hasattr(db_obj, field) and value is not None:
                    setattr(db_obj, field, value)
            
            # Update timestamps if they exist
            if hasattr(db_obj, 'updated_at'):
                setattr(db_obj, 'updated_at', datetime.utcnow())
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except NotFoundError:
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error updating {self.model.__name__}: {str(e)}")
            raise AlreadyExistsError(f"Update would violate unique constraint: {str(e)}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error updating {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to update {self.model.__name__}: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error updating {self.model.__name__}: {str(e)}")
            raise CRUDError(f"Failed to update {self.model.__name__}")
    
    def delete(self, db: Session, *, id: Union[UUID, str, int], soft: bool = True, **kwargs) -> bool:
        """
        Delete a record.
        
        Args:
            db: Database session
            id: ID of the record to delete
            soft: If True, perform a soft delete (mark as deleted) if supported
            **kwargs: Additional filter criteria
            
        Returns:
            bool: True if the record was deleted, False otherwise
            
        Raises:
            DatabaseError: For database errors
        """
        try:
            # First get the object
            obj = self.get(db, id, **kwargs)
            if not obj:
                return False
            
            # Handle soft delete if supported and requested
            if soft and hasattr(self.model, 'is_deleted'):
                setattr(obj, 'is_deleted', True)
                if hasattr(obj, 'deleted_at'):
                    setattr(obj, 'deleted_at', datetime.utcnow())
                db.add(obj)
                db.commit()
                return True
            
            # Otherwise, perform hard delete
            db.delete(obj)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {str(e)}")
            raise DatabaseError(f"Failed to delete {self.model.__name__}: {str(e)}")
    
    def exists(self, db: Session, **kwargs) -> bool:
        """
        Check if a record exists that matches the given filters.
        
        Args:
            db: Database session
            **kwargs: Filter criteria (field=value)
            
        Returns:
            bool: True if a matching record exists, False otherwise
        """
        try:
            query = self._base_query
            
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
            
            return db.exec(select([1]).select_from(query.subquery()).exists()).scalar()
            
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to check existence of {self.model.__name__}")
    
    def count(self, db: Session, **kwargs) -> int:
        """
        Count records matching the given filters.
        
        Args:
            db: Database session
            **kwargs: Filter criteria (field=value)
            
        Returns:
            int: Number of matching records
        """
        try:
            query = self._base_query
            
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    if isinstance(value, (list, tuple, set)):
                        query = query.where(getattr(self.model, field).in_(value))
                    else:
                        query = query.where(getattr(self.model, field) == value)
            
            return db.scalar(select([func.count()]).select_from(query.subquery())) or 0
            
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__} records: {str(e)}")
            raise DatabaseError(f"Failed to count {self.model.__name__} records")
    
    # Advanced Query Methods
    # ====================
    
    def get_by_ids(self, db: Session, ids: List[Union[UUID, str, int]], **kwargs) -> List[ModelType]:
        """
        Get multiple records by their IDs.
        
        Args:
            db: Database session
            ids: List of record IDs
            **kwargs: Additional filter criteria
            
        Returns:
            List of model instances
        """
        if not ids:
            return []
            
        try:
            query = self._base_query.where(self.model.id.in_(ids))
            
            # Apply additional filters
            for key, value in kwargs.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
            
            results = db.exec(query).all()
            
            # Preserve the order of the input IDs
            id_map = {str(obj.id): obj for obj in results}
            return [id_map[str(id)] for id in ids if str(id) in id_map]
            
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} records by IDs: {str(e)}")
            raise DatabaseError(f"Failed to get {self.model.__name__} records by IDs")
    
    def get_or_create(
        self, 
        db: Session, 
        *, 
        obj_in: Union[CreateSchemaType, Dict[str, Any]],
        filter_by: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[ModelType, bool]:
        """
        Get an existing record or create it if it doesn't exist.
        
        Args:
            db: Database session
            obj_in: Data to create the record with if it doesn't exist
            filter_by: Fields to filter by when checking for existence
            **kwargs: Additional fields to set on the new record
            
        Returns:
            Tuple of (model_instance, created) where created is a boolean indicating 
            whether the record was created
        """
        try:
            # If no filter is provided, use the input data to filter
            if filter_by is None:
                if not isinstance(obj_in, dict):
                    filter_by = obj_in.dict(exclude_unset=True)
                else:
                    filter_by = obj_in.copy()
            
            # Check if the record exists
            existing = self.get_by_fields(db, **filter_by)
            if existing:
                return existing[0], False
            
            # Create the record if it doesn't exist
            return self.create(db, obj_in=obj_in, **kwargs), True
            
        except Exception as e:
            logger.error(f"Error in get_or_create for {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to get or create {self.model.__name__}")
    
    def get_by_fields(self, db: Session, **filters) -> List[ModelType]:
        """
        Get records that match the given field filters.
        
        Args:
            db: Database session
            **filters: Field filters (field=value)
            
        Returns:
            List of matching model instances
        """
        try:
            query = self._base_query
            
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if value is None:
                        query = query.where(getattr(self.model, field).is_(None))
                    elif isinstance(value, (list, tuple, set)):
                        query = query.where(getattr(self.model, field).in_(value))
                    else:
                        query = query.where(getattr(self.model, field) == value)
            
            return db.exec(query).all()
            
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by fields: {str(e)}")
            raise DatabaseError(f"Failed to get {self.model.__name__} by fields")
    
    # Bulk Operations
    # ==============
    
    def bulk_create(
        self, 
        db: Session, 
        objs_in: List[Union[CreateSchemaType, Dict[str, Any]]],
        **kwargs
    ) -> List[ModelType]:
        """
        Create multiple records in a single transaction.
        
        Args:
            db: Database session
            objs_in: List of input data for the new records
            **kwargs: Additional fields to set on all new records
            
        Returns:
            List of created model instances
        """
        try:
            objs = []
            for obj_in in objs_in:
                if not isinstance(obj_in, dict):
                    create_data = obj_in.dict(exclude_unset=True)
                else:
                    create_data = obj_in.copy()
                
                # Add any additional fields
                create_data.update(kwargs)
                
                objs.append(self.model(**create_data))
            
            db.bulk_save_objects(objs)
            db.commit()
            
            # Refresh the objects to get their IDs
            for obj in objs:
                db.refresh(obj)
                
            return objs
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in bulk_create for {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to bulk create {self.model.__name__} records")
    
    def bulk_update(
        self,
        db: Session,
        objs: List[ModelType],
        update_data: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> None:
        """
        Update multiple records in a single transaction.
        
        Args:
            db: Database session
            objs: List of model instances to update
            update_data: Data to update the records with
        """
        try:
            if not isinstance(update_data, dict):
                update_data = update_data.dict(exclude_unset=True)
            
            # Update the objects
            for obj in objs:
                for field, value in update_data.items():
                    if hasattr(obj, field) and value is not None:
                        setattr(obj, field, value)
                
                # Update timestamps if they exist
                if hasattr(obj, 'updated_at'):
                    setattr(obj, 'updated_at', datetime.utcnow())
            
            db.bulk_save_objects(objs)
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in bulk_update for {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to bulk update {self.model.__name__} records")
    
    # Async Methods
    # ============
    
    async def get_async(self, db: AsyncSession, id: Union[UUID, str, int], **kwargs) -> Optional[ModelType]:
        """Async version of get"""
        try:
            query = self._base_query.where(self.model.id == id)
            
            # Apply additional filters if provided
            for key, value in kwargs.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
            
            result = await db.execute(query)
            return result.scalars().first()
            
        except Exception as e:
            logger.error(f"Async error getting {self.model.__name__} with id {id}: {str(e)}")
            raise DatabaseError(f"Failed to get {self.model.__name__}: {str(e)}")
    
    async def create_async(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: Union[CreateSchemaType, Dict[str, Any]], 
        **kwargs
    ) -> ModelType:
        """Async version of create"""
        try:
            # Convert Pydantic model to dict if needed
            if not isinstance(obj_in, dict):
                create_data = obj_in.dict(exclude_unset=True)
            else:
                create_data = obj_in.copy()
            
            # Add any additional fields
            create_data.update(kwargs)
            
            # Create and save the new record
            db_obj = self.model(**create_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Async integrity error creating {self.model.__name__}: {str(e)}")
            raise AlreadyExistsError(f"{self.model.__name__} with these details already exists")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Async database error creating {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to create {self.model.__name__}: {str(e)}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Async unexpected error creating {self.model.__name__}: {str(e)}")
            raise CRUDError(f"Failed to create {self.model.__name__}")
    
    # Add other async methods as needed...
    
    # Utility Methods
    # ==============
    
    def _apply_filters(self, query, filters: Dict[str, Any]) -> Any:
        """Apply filters to a query"""
        for field, value in filters.items():
            if hasattr(self.model, field):
                if value is None:
                    query = query.where(getattr(self.model, field).is_(None))
                elif isinstance(value, (list, tuple, set)):
                    query = query.where(getattr(self.model, field).in_(value))
                else:
                    query = query.where(getattr(self.model, field) == value)
        return query
    
    def _apply_ordering(self, query, order_by: List[str]) -> Any:
        """Apply ordering to a query"""
        order_clauses = []
        for field in order_by:
            if field.startswith('-'):
                order_field = field[1:]
                if hasattr(self.model, order_field):
                    order_clauses.append(desc(getattr(self.model, order_field)))
            else:
                if hasattr(self.model, field):
                    order_clauses.append(asc(getattr(self.model, field)))
        
        if order_clauses:
            query = query.order_by(*order_clauses)
            
        return query
