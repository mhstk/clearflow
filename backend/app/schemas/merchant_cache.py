from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional



class MerchantCacheBase(BaseModel):
    merchant_key: str
    suggested_category: str
    suggested_note: str
    suggested_explanation: str


class MerchantCacheCreate(MerchantCacheBase):
    user_id: int


class MerchantCacheResponse(MerchantCacheBase):
    id: int
    user_id: int
    created_at: datetime
    last_used_at: datetime

    class Config:
        from_attributes = True


class CategorizeMerchantRequest(BaseModel):
    merchant_key: str
    sample_descriptions: List[str]


class CategorizeMerchantResponse(BaseModel):
    merchant_key: str
    category: str
    note: str
    explanation: str


class InsightsRequest(BaseModel):
    account_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    category: Optional[List[str]] = None
    merchant_query: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None


class InsightsResponse(BaseModel):
    insights: List[str]


class BatchCategorizationRequest(BaseModel):
    transaction_ids: List[int]
    auto_apply: bool = True


class TransactionCategorizationResult(BaseModel):
    transaction_id: int
    category: str
    note: str
    confidence: str
    applied: bool
    error: Optional[str] = None


class BatchCategorizationResponse(BaseModel):
    results: List[TransactionCategorizationResult]
    total_processed: int
    successful: int
    failed: int
