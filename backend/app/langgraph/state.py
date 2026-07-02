from typing import TypedDict, Optional, List

class VoiceAgentState(TypedDict):
    company_id: str
    pending_customers: Optional[List[dict]]
    dispatched_calls: Optional[List[dict]]
    customer_id: Optional[str]
    call_id: Optional[str]
    transcript: Optional[str]
    summary: Optional[str]
    outcome: Optional[str]
    confidence: Optional[float]
    reasoning: Optional[str]
    error: Optional[str]
    errors: Optional[List[str]]
