from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    verify_password,
    get_current_active_user,
)
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserPublic
from app.models.user import User
from app.crud import user as crud_user

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud_user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            subject=user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Test access token
    """
    return current_user

@router.post("/register", response_model=UserPublic)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = crud_user.create(db, obj_in=user_in)
    return user

@router.post("/password-recovery/{email}", response_model=dict)
def recover_password(email: str, db: Session = Depends(get_db)) -> Any:
    """
    Password Recovery
    """
    user = crud_user.get_by_email(db, email=email)

    if not user:
        # Don't reveal that the user doesn't exist
        return {"msg": "If this email is registered, you will receive a password reset link."}

    # Generate password reset token (1 hour expiry)
    password_reset_token = create_access_token(
        subject=user.id, expires_delta=timedelta(hours=1)
    )
    
    # TODO: Send email with password reset link
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={password_reset_token}"
    print(f"Password reset link: {reset_link}")  # For development
    
    return {"msg": "If this email is registered, you will receive a password reset link."}

@router.post("/reset-password/", response_model=dict)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Reset password
    """
    # TODO: Implement password reset logic
    # 1. Verify token
    # 2. Update user password
    # 3. Invalidate token
    return {"msg": "Password reset successful"}

@router.post("/login/google")
def login_google():
    """
    Google OAuth login
    """
    # TODO: Implement Google OAuth
    pass

@router.post("/login/github")
def login_github():
    """
    GitHub OAuth login
    """
    # TODO: Implement GitHub OAuth
    pass
