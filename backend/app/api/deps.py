from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.user import User

# JWT Bearer token security
security = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: Bearer token credentials
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: If not authenticated or token is invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user


async def get_current_user_id(
    user: User = Depends(get_current_user)
) -> int:
    """
    Get current user ID from authenticated user.

    This maintains backward compatibility with existing endpoints
    that use get_current_user_id dependency.

    Args:
        user: Authenticated user from get_current_user

    Returns:
        User ID
    """
    return user.id


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get user if authenticated, None otherwise.

    Useful for endpoints that work with or without authentication.

    Args:
        credentials: Bearer token credentials (optional)
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        return None

    return db.query(User).filter(
        User.id == user_id,
        User.is_active == True
    ).first()
