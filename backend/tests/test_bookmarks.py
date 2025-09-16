import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.main import app
from app.core.config import settings
from app.tests.utils.user import create_random_user, authentication_token_from_email
from app.tests.utils.bookmark import (
    create_random_bookmark, 
    create_random_bookmark_folder,
    add_bookmark_reminder,
    add_bookmark_tag,
    process_bulk_bookmark_action
)

client = TestClient(app)

def test_create_bookmark(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test creating a new bookmark"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    folder = create_random_bookmark_folder(db, user_id=user_id)
    
    data = {
        "folder_id": str(folder.id),
        "type": "save_for_later",
        "notes": "Test bookmark notes",
        "tags": ["tag1", "tag2"],
    }
    
    # Create an internship first
    from app.tests.utils.internship import create_random_internship
    internship = create_random_internship(db)
    data["internship_id"] = str(internship.id)
    
    response = client.post(
        f"{settings.API_V1_STR}/bookmarks/",
        headers=normal_user_token_headers,
        json=data,
    )
    
    assert response.status_code == 201, response.text
    content = response.json()
    assert content["folder_id"] == str(folder.id)
    assert content["type"] == "save_for_later"
    assert content["notes"] == "Test bookmark notes"
    assert set(content["tags"]) == {"tag1", "tag2"}
    assert "id" in content


def test_read_bookmark(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test reading a bookmark"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    bookmark = create_random_bookmark(db, user_id=user_id)
    
    response = client.get(
        f"{settings.API_V1_STR}/bookmarks/{bookmark.id}",
        headers=normal_user_token_headers,
    )
    
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == str(bookmark.id)
    assert content["user_id"] == user_id


def test_update_bookmark(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test updating a bookmark"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    bookmark = create_random_bookmark(db, user_id=user_id)
    folder = create_random_bookmark_folder(db, user_id=user_id)
    
    update_data = {
        "folder_id": str(folder.id),
        "notes": "Updated test notes",
        "is_archived": True,
        "priority": 2,
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/bookmarks/{bookmark.id}",
        headers=normal_user_token_headers,
        json=update_data,
    )
    
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == str(bookmark.id)
    assert content["folder_id"] == str(folder.id)
    assert content["notes"] == "Updated test notes"
    assert content["is_archived"] is True
    assert content["priority"] == 2


def test_delete_bookmark(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test deleting a bookmark"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    bookmark = create_random_bookmark(db, user_id=user_id)
    
    response = client.delete(
        f"{settings.API_V1_STR}/bookmarks/{bookmark.id}",
        headers=normal_user_token_headers,
    )
    
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["message"] == "Bookmark deleted successfully"
    
    # Verify the bookmark was deleted
    response = client.get(
        f"{settings.API_V1_STR}/bookmarks/{bookmark.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404


def test_add_reminder(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test adding a reminder to a bookmark"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    bookmark = create_random_bookmark(db, user_id=user_id)
    
    response = client.post(
        f"{settings.API_V1_STR}/bookmarks/{bookmark.id}/reminder",
        headers=normal_user_token_headers,
        json={"days": 7, "notes": "Follow up on this"},
    )
    
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == str(bookmark.id)
    assert content["remind_at"] is not None
    assert content["notes"] == "Follow up on this"


def test_bulk_update_bookmarks(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test bulk updating bookmarks"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    folder1 = create_random_bookmark_folder(db, user_id=user_id, name="Folder 1")
    folder2 = create_random_bookmark_folder(db, user_id=user_id, name="Folder 2")
    
    # Create some bookmarks
    bookmark1 = create_random_bookmark(db, user_id=user_id, folder_id=folder1.id)
    bookmark2 = create_random_bookmark(db, user_id=user_id, folder_id=folder1.id)
    bookmark3 = create_random_bookmark(db, user_id=user_id, folder_id=folder1.id)
    
    # Test moving bookmarks to another folder
    response = client.post(
        f"{settings.API_V1_STR}/bookmarks/bulk",
        headers=normal_user_token_headers,
        json={
            "bookmark_ids": [str(bookmark1.id), str(bookmark2.id)],
            "action": "move_to_folder",
            "folder_id": str(folder2.id)
        },
    )
    
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["action"] == "move_to_folder"
    assert content["updated_count"] == 2
    
    # Verify the bookmarks were moved
    response = client.get(
        f"{settings.API_V1_STR}/bookmarks/{bookmark1.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["folder_id"] == str(folder2.id)
    
    # Test adding tags
    response = client.post(
        f"{settings.API_V1_STR}/bookmarks/bulk",
        headers=normal_user_token_headers,
        json={
            "bookmark_ids": [str(bookmark1.id), str(bookmark2.id), str(bookmark3.id)],
            "action": "add_tags",
            "tags": ["important", "follow-up"]
        },
    )
    
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["action"] == "add_tags"
    assert content["updated_count"] == 3
    
    # Verify the tags were added
    response = client.get(
        f"{settings.API_V1_STR}/bookmarks/{bookmark1.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200, response.text
    assert set(response.json()["tags"]) >= {"important", "follow-up"}


def test_get_upcoming_reminders(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test getting upcoming reminders"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    
    # Create bookmarks with reminders
    bookmark1 = create_random_bookmark(db, user_id=user_id)
    bookmark1 = add_bookmark_reminder(db, bookmark1.id, user_id, days=1)  # Due tomorrow
    
    bookmark2 = create_random_bookmark(db, user_id=user_id)
    bookmark2 = add_bookmark_reminder(db, bookmark2.id, user_id, days=7)  # Due in a week
    
    # Get upcoming reminders (next 3 days)
    response = client.get(
        f"{settings.API_V1_STR}/bookmarks/upcoming/reminders",
        headers=normal_user_token_headers,
        params={"days_ahead": 3}
    )
    
    assert response.status_code == 200, response.text
    content = response.json()
    assert len(content) == 1  # Only bookmark1 is due in the next 3 days
    assert content[0]["id"] == str(bookmark1.id)


def test_bookmark_folders_crud(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test CRUD operations for bookmark folders"""
    # Create a folder
    create_data = {
        "name": "Test Folder",
        "description": "Test description",
        "is_private": True,
        "icon": "folder",
        "color": "blue"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/bookmarks/folders/",
        headers=normal_user_token_headers,
        json=create_data,
    )
    
    assert response.status_code == 201, response.text
    folder = response.json()
    assert folder["name"] == "Test Folder"
    assert folder["description"] == "Test description"
    assert folder["is_private"] is True
    
    # Get the folder
    response = client.get(
        f"{settings.API_V1_STR}/bookmarks/folders/{folder['id']}",
        headers=normal_user_token_headers,
    )
    
    assert response.status_code == 200, response.text
    assert response.json()["id"] == folder["id"]
    
    # Update the folder
    update_data = {
        "name": "Updated Folder Name",
        "description": "Updated description",
        "is_private": False
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/bookmarks/folders/{folder['id']}",
        headers=normal_user_token_headers,
        json=update_data,
    )
    
    assert response.status_code == 200, response.text
    updated_folder = response.json()
    assert updated_folder["name"] == "Updated Folder Name"
    assert updated_folder["description"] == "Updated description"
    assert updated_folder["is_private"] is False
    
    # Delete the folder
    response = client.delete(
        f"{settings.API_V1_STR}/bookmarks/folders/{folder['id']}",
        headers=normal_user_token_headers,
    )
    
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Folder deleted successfully"
    
    # Verify the folder was deleted
    response = client.get(
        f"{settings.API_V1_STR}/bookmarks/folders/{folder['id']}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
