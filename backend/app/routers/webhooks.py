import hmac
import hashlib
import json
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import get_db
from app.langgraph.evaluation_graph import run_evaluation

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

def _verify_vapi_signature(body: bytes, signature_header: str) -> bool:
    """Verify the HMAC-SHA256 signature sent by Vapi in the X-Vapi-Signature header."""
    secret = settings.SECRET_KEY
    if not secret or secret == "dev-secret-key" or not signature_header:

        return True
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, signature_header)

async def _process_call_ended(payload: dict):
    message = payload.get("message", {})

    # Vapi may send the call object inside message or at the top level
    call = message.get("call", {}) or payload.get("call", {})
    metadata = call.get("metadata", {}) or message.get("metadata", {})

    call_id = call.get("id", "") or message.get("callId", "")
    transcript = message.get("transcript", "") or payload.get("transcript", "")
    summary = message.get("summary", "") or payload.get("summary", "")
    customer_id = metadata.get("customer_id", "")
    company_id = metadata.get("company_id", "")

    print(f"[Webhook] end-of-call payload keys: {list(payload.keys())}")
    print(f"[Webhook] message keys: {list(message.keys())}")
    print(f"[Webhook] call_id={call_id}, customer_id={customer_id}, company_id={company_id}")

    if not customer_id or not company_id:
        db = get_db()
        customer = await db.customers.find_one({"call_id": call_id})
        if customer:
            customer_id = str(customer["_id"])
            company_id = customer.get("company_id", "")

    if not customer_id:
        print(f"[Webhook] Could not identify customer for call_id={call_id}")
        return

    print(f"[Webhook] Processing end-of-call for customer={customer_id}, call={call_id}")

    result = await run_evaluation(
        company_id=company_id,
        customer_id=customer_id,
        call_id=call_id,
        transcript=transcript,
        summary=summary,
    )

    print(f"[Webhook] Evaluation complete -> {result}")

@router.post("/vapi")
async def vapi_webhook(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()
    signature = request.headers.get("x-vapi-signature", "")

    if not _verify_vapi_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    message = payload.get("message", {})
    event_type = message.get("type", "")

    print(f"[Webhook] Received Vapi event: type={event_type}")

    if event_type == "end-of-call-report":
        background_tasks.add_task(_process_call_ended, payload)
        return JSONResponse({"status": "processing"}, status_code=200)

    elif event_type == "status-update":
        call_status = message.get("status", "")
        call_id = message.get("call", {}).get("id", "")
        print(f"[Webhook] Status update: call={call_id}, status={call_status}")
        return JSONResponse({"status": "acknowledged"}, status_code=200)

    return JSONResponse({"status": "ok"}, status_code=200)

@router.post("/vapi/test")
async def test_webhook(background_tasks: BackgroundTasks, customer_id: str, company_id: str):
    mock_transcript = """
    Agent: Hello! This is an AI assistant from Sunrise Realty. Are you looking to buy or sell a property?
    Customer: Hi! Yes, actually I've been looking to buy a house in the suburbs.
    Agent: That's great! What's your budget range?
    Customer: We're looking at around $400,000 to $500,000.
    Agent: Perfect. Are you pre-approved for a mortgage?
    Customer: Yes, we just got pre-approved last week.
    Agent: Excellent! Would you like to schedule a consultation with one of our agents?
    Customer: Absolutely, that sounds great!
    Agent: Wonderful! Our team will reach out to schedule a meeting. Thank you for your time!
    Customer: Thank you, goodbye!
    """

    mock_payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {
                "id": f"test-call-{customer_id}",
                "metadata": {
                    "customer_id": customer_id,
                    "company_id": company_id,
                },
            },
            "transcript": mock_transcript,
            "summary": "Customer is interested in buying a house. Budget $400k-$500k. Pre-approved for mortgage. Wants consultation.",
        }
    }

    background_tasks.add_task(_process_call_ended, mock_payload)
    return {"status": "test_webhook_dispatched", "customer_id": customer_id}
