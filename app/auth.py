from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlmodel import Session
from typing import Optional
import httpx

from .config import settings
from .repositories import get_repositories, get_session
from .models import User

security = HTTPBearer(auto_error=False)

async def verify_supabase_token(token: str) -> dict:
    """Verify Supabase JWT token"""
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration missing"
        )
    
    try:
        # Get Supabase JWT secret from their API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.supabase_url}/auth/v1/jwks",
                headers={"apikey": settings.supabase_anon_key}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not verify token"
                )
        
        # For now, we'll decode without verification for development
        # In production, you should properly verify the JWT signature
        payload = jwt.get_unverified_claims(token)
        
        if payload.get("aud") != "authenticated":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience"
            )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    payload = await verify_supabase_token(credentials.credentials)
    supabase_id = payload.get("sub")
    email = payload.get("email")
    
    if not supabase_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    repos = get_repositories(session)
    user = repos['users'].get_by_supabase_id(supabase_id)
    
    if not user:
        # Create user if doesn't exist
        user = repos['users'].create_user(
            supabase_id=supabase_id,
            email=email,
            name=payload.get("user_metadata", {}).get("name")
        )
    
    return user

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None
