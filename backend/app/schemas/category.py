"""
Pydantic schemas for user categories.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    """Base schema for category data."""
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')  # Hex color
    icon: Optional[str] = None


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = None


class CategoryReorder(BaseModel):
    """Schema for reordering categories."""
    category_ids: List[int] = Field(..., min_length=1)


class CategoryResponse(BaseModel):
    """Schema for category response."""
    id: int
    name: str
    color: Optional[str]
    icon: Optional[str]
    sort_order: int
    is_system: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    """Schema for list of categories."""
    categories: List[CategoryResponse]
    total: int
