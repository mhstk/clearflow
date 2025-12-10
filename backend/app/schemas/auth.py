"""
Authentication schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Request schemas
class SignupRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for email/password login."""
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth authentication."""
    code: str  # Authorization code from Google


# Response schemas
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class UserAuthResponse(BaseModel):
    """User profile in auth responses."""
    id: int
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_demo: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Response for successful authentication."""
    user: UserAuthResponse
    token: Token


class GoogleAuthUrlResponse(BaseModel):
    """Response containing Google OAuth URL."""
    url: str
