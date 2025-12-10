from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    name: str
    institution: Optional[str] = None
    account_type: Optional[str] = None
    account_number_last4: Optional[str] = None
    currency: str = "CAD"


class AccountCreate(AccountBase):
    pass


class AccountResponse(AccountBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
