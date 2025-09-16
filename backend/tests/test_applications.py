import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any

from app.main import app
from app.core.config import settings
from app.tests.utils.user import create_random_user, authentication_token_from_email
from app.tests.utils.internship import create_random_internship
from app.tests.utils.resume import create_random_resume
from app.tests.utils.application import create_random_application

client = TestClient(app)

def test_create_application(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test creating a new application"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    internship = create_random_internship(db)
    resume = create_random_resume(db, user_id=user_id)
    
    data = {
        "internship_id": str(internship.id),
        "resume_id": str(resume.id),
        "status": "applied",
        "stage": "application",
        "source": "company_website",
        "notes": "Test application notes",
        "applied_at": datetime.utcnow().isoformat(),
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/applications/",
        headers=normal_user_token_headers,
        json=data,
    )
    
    assert response.status_code == 201
    content = response.json()
    assert content["internship_id"] == str(internship.id)
    assert content["resume_id"] == str(resume.id)
    assert content["status"] == "applied"
    assert content["stage"] == "application"
    assert content["source"] == "company_website"
    assert "id" in content


def test_read_application(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test reading an application"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    application = create_random_application(db, user_id=user_id)
    
    response = client.get(
        f"{settings.API_V1_STR}/applications/{application.id}",
        headers=normal_user_token_headers,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(application.id)
    assert content["user_id"] == user_id


def test_update_application(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test updating an application"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    application = create_random_application(db, user_id=user_id)
    
    update_data = {
        "notes": "Updated test notes",
        "status": "interviewing",
        "stage": "interview"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/applications/{application.id}",
        headers=normal_user_token_headers,
        json=update_data,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(application.id)
    assert content["notes"] == "Updated test notes"
    assert content["status"] == "interviewing"
    assert content["stage"] == "interview"


def test_delete_application(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test deleting an application"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    application = create_random_application(db, user_id=user_id)
    
    response = client.delete(
        f"{settings.API_V1_STR}/applications/{application.id}",
        headers=normal_user_token_headers,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Application deleted successfully"
    
    # Verify the application was deleted
    response = client.get(
        f"{settings.API_V1_STR}/applications/{application.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404


def test_update_application_status(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test updating an application's status"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    application = create_random_application(db, user_id=user_id, status="applied")
    
    response = client.post(
        f"{settings.API_V1_STR}/applications/{application.id}/status",
        headers=normal_user_token_headers,
        json={"status": "interviewing"},
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(application.id)
    assert content["status"] == "interviewing"
    
    # Check that the activity was logged
    assert len(content["activity_log"]) > 0
    assert content["activity_log"][-1]["type"] == "status_change"
    assert content["activity_log"][-1]["details"]["new_status"] == "interviewing"


def test_add_application_activity(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test adding an activity to an application"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    application = create_random_application(db, user_id=user_id)
    
    activity_data = {
        "type": "note",
        "details": {
            "content": "Test note content",
            "is_important": True
        }
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/applications/{application.id}/activities",
        headers=normal_user_token_headers,
        json=activity_data,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(application.id)
    assert len(content["activity_log"]) > 0
    assert content["activity_log"][-1]["type"] == "note"
    assert content["activity_log"][-1]["details"]["content"] == "Test note content"


def test_get_application_stats(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test getting application statistics"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    
    # Create applications with different statuses
    create_random_application(db, user_id=user_id, status="applied")
    create_random_application(db, user_id=user_id, status="applied")
    create_random_application(db, user_id=user_id, status="interviewing")
    create_random_application(db, user_id=user_id, status="rejected")
    
    response = client.get(
        f"{settings.API_V1_STR}/applications/stats/overview",
        headers=normal_user_token_headers,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["total"] == 4
    assert content["by_status"]["applied"] == 2
    assert content["by_status"]["interviewing"] == 1
    assert content["by_status"]["rejected"] == 1


def test_get_upcoming_activities(
    db: Session, normal_user_token_headers: Dict[str, str]
) -> None:
    """Test getting upcoming activities"""
    # Create test data
    user_id = 1  # Will be set by the auth middleware
    
    # Create an application with an upcoming interview
    application = create_random_application(db, user_id=user_id, status="interviewing")
    
    # Add an upcoming interview activity
    activity_data = {
        "type": "interview_scheduled",
        "details": {
            "scheduled_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "interview_type": "technical",
            "interviewer": "John Doe",
            "notes": "Technical interview with the engineering team"
        }
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/applications/{application.id}/activities",
        headers=normal_user_token_headers,
        json=activity_data,
    )
    assert response.status_code == 200
    
    # Get upcoming activities
    response = client.get(
        f"{settings.API_V1_STR}/applications/upcoming/activities",
        headers=normal_user_token_headers,
        params={"days_ahead": 7, "limit": 10}
    )
    
    assert response.status_code == 200
    content = response.json()
    assert len(content) > 0
    assert content[0]["type"] == "interview"
