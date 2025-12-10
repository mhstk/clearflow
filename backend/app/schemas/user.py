from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_demo: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
