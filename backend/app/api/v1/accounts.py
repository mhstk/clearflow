from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user_id
from app.models.account import Account
from app.schemas.account import AccountResponse, AccountCreate

router = APIRouter()


@router.get("/", response_model=List[AccountResponse])
def get_accounts(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get all accounts for current user"""
    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get specific account"""
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == user_id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return account


@router.post("/", response_model=AccountResponse)
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Create a new account"""
    db_account = Account(
        user_id=user_id,
        **account.model_dump()
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account
