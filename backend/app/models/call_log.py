from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .company import PyObjectId
from app.utils import utcnow

class CallLog(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    customer_id: str
    company_id: str
    vapi_call_id: str
    status: str = "completed"
    transcript: Optional[str] = None
    summary: Optional[str] = None
    llm_reasoning: Optional[str] = None
    outcome: Optional[str] = None
    confidence: Optional[float] = None
    duration_seconds: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}
