"""
API endpoints for user-defined categories.

Users can create, update, delete, and reorder their own categories.
The "Other" category is a system category that cannot be modified.
"Uncategorized" is not stored - it's just a default value for transactions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user_id
from app.models.user_category import UserCategory, DEFAULT_USER_CATEGORIES
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryReorder,
    CategoryResponse,
    CategoryListResponse
)

router = APIRouter()


def initialize_default_categories(db: Session, user_id: int) -> List[UserCategory]:
    """
    Initialize default categories for a new user.
    Called automatically when user first accesses their categories.
    """
    categories = []
    for cat_data in DEFAULT_USER_CATEGORIES:
        category = UserCategory(
            user_id=user_id,
            name=cat_data["name"],
            color=cat_data["color"],
            sort_order=cat_data["sort_order"],
            is_system=cat_data["is_system"]
        )
        db.add(category)
        categories.append(category)

    db.commit()
    for cat in categories:
        db.refresh(cat)

    return categories


def get_user_categories_list(db: Session, user_id: int) -> List[UserCategory]:
    """
    Get user's categories, initializing defaults if none exist.
    """
    categories = db.query(UserCategory).filter(
        UserCategory.user_id == user_id
    ).order_by(UserCategory.sort_order).all()

    # Initialize defaults if user has no categories
    if not categories:
        categories = initialize_default_categories(db, user_id)

    return categories


@router.get("", response_model=CategoryListResponse)
def get_categories(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get all categories for the current user.

    If user has no categories, default categories are automatically created.
    Returns categories sorted by sort_order.

    Note: "Uncategorized" is NOT included - it's a system value, not a category.
    """
    categories = get_user_categories_list(db, user_id)

    return CategoryListResponse(
        categories=[CategoryResponse.model_validate(cat) for cat in categories],
        total=len(categories)
    )


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Create a new category.

    Category name must be unique for the user (case-insensitive).
    """
    # Check if category name already exists (case-insensitive)
    existing = db.query(UserCategory).filter(
        UserCategory.user_id == user_id,
        UserCategory.name.ilike(category_data.name)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category_data.name}' already exists"
        )

    # Get max sort_order to add new category at the end (but before "Other")
    max_order = db.query(UserCategory).filter(
        UserCategory.user_id == user_id,
        UserCategory.is_system == False
    ).count()

    category = UserCategory(
        user_id=user_id,
        name=category_data.name,
        color=category_data.color or "#6b7280",  # Default gray
        icon=category_data.icon,
        sort_order=max_order + 1,
        is_system=False
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return CategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Update a category.

    System categories (like "Other") cannot be modified.
    When renaming, all transactions with the old category name are updated.
    """
    category = db.query(UserCategory).filter(
        UserCategory.id == category_id,
        UserCategory.user_id == user_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System categories cannot be modified"
        )

    # Store old name for transaction update
    old_name = category.name

    # Check for duplicate name (if name is being changed)
    if category_data.name and category_data.name.lower() != category.name.lower():
        existing = db.query(UserCategory).filter(
            UserCategory.user_id == user_id,
            UserCategory.name.ilike(category_data.name),
            UserCategory.id != category_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_data.name}' already exists"
            )

    # Update fields
    if category_data.name is not None:
        category.name = category_data.name
    if category_data.color is not None:
        category.color = category_data.color
    if category_data.icon is not None:
        category.icon = category_data.icon

    # If name was changed, update all transactions and merchant cache with the old category name
    if category_data.name is not None and category_data.name != old_name:
        from app.models.transaction import Transaction
        from app.models.merchant_cache import MerchantCache

        # Update transactions
        db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.category == old_name
        ).update({"category": category_data.name})

        # Update merchant cache
        db.query(MerchantCache).filter(
            MerchantCache.user_id == user_id,
            MerchantCache.suggested_category == old_name
        ).update({"suggested_category": category_data.name})

    db.commit()
    db.refresh(category)

    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Delete a category.

    System categories (like "Other") cannot be deleted.
    Transactions with this category will be set to "Uncategorized".
    """
    category = db.query(UserCategory).filter(
        UserCategory.id == category_id,
        UserCategory.user_id == user_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System categories cannot be deleted"
        )

    # Update transactions with this category to "Uncategorized"
    from app.models.transaction import Transaction
    db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.category == category.name
    ).update({"category": "Uncategorized", "category_source": "uncategorized"})

    db.delete(category)
    db.commit()

    return None


@router.post("/reorder", response_model=CategoryListResponse)
def reorder_categories(
    reorder_data: CategoryReorder,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Reorder categories by providing category IDs in desired order.

    System categories (like "Other") will always remain at the end.
    """
    # Validate all category IDs belong to user
    categories = db.query(UserCategory).filter(
        UserCategory.id.in_(reorder_data.category_ids),
        UserCategory.user_id == user_id
    ).all()

    if len(categories) != len(reorder_data.category_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category IDs"
        )

    # Create lookup for new order
    id_to_order = {cat_id: idx for idx, cat_id in enumerate(reorder_data.category_ids)}

    # Update sort_order for each category
    for category in categories:
        if not category.is_system:  # Don't reorder system categories
            category.sort_order = id_to_order[category.id]

    db.commit()

    # Return updated list
    all_categories = get_user_categories_list(db, user_id)

    return CategoryListResponse(
        categories=[CategoryResponse.model_validate(cat) for cat in all_categories],
        total=len(all_categories)
    )


@router.post("/reset", response_model=CategoryListResponse)
def reset_categories(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Reset categories to defaults.

    Deletes all user categories and recreates defaults.
    Transactions will have their categories set to "Uncategorized".
    """
    # Update all transactions to Uncategorized
    from app.models.transaction import Transaction
    db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).update({"category": "Uncategorized", "category_source": "uncategorized"})

    # Delete all user categories
    db.query(UserCategory).filter(
        UserCategory.user_id == user_id
    ).delete()

    db.commit()

    # Create defaults
    categories = initialize_default_categories(db, user_id)

    return CategoryListResponse(
        categories=[CategoryResponse.model_validate(cat) for cat in categories],
        total=len(categories)
    )


# Helper function for other services
def get_user_category_names(db: Session, user_id: int) -> List[str]:
    """
    Get list of category names for a user.
    Used by AI categorization services.

    Note: Does NOT include "Uncategorized" - that's a system value.
    """
    categories = get_user_categories_list(db, user_id)
    return [cat.name for cat in categories]
