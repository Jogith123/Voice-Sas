from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from .company import PyObjectId
from app.utils import utcnow

class CustomerStatus(str, Enum):
    PENDING = "PENDING"
    CALL_INITIATED = "CALL_INITIATED"
    QUALIFIED = "QUALIFIED"
    NOT_INTERESTED = "NOT_INTERESTED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"

class CustomerBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None

class CustomerCreate(CustomerBase):
    company_id: str

class CustomerUpdate(BaseModel):
    status: Optional[CustomerStatus] = None
    call_id: Optional[str] = None
    notes: Optional[str] = None

class Customer(CustomerBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    company_id: str
    status: CustomerStatus = CustomerStatus.PENDING
    call_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}
