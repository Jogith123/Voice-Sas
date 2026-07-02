import asyncio
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import StateGraph, END

from app.langgraph.state import VoiceAgentState
from app.database import get_db
from app.services import vapi_service
from bson import ObjectId

async def fetch_pending_leads(state: VoiceAgentState) -> VoiceAgentState:
    db = get_db()
    company_id = state["company_id"]

    try:
        company = await db.companies.find_one({"_id": ObjectId(company_id)})
        if not company:
            return {**state, "error": f"Company {company_id} not found", "pending_customers": []}

        cursor = db.customers.find({
            "company_id": company_id,
            "status": "PENDING",
        })
        customers = await cursor.to_list(length=100)

        enriched = []
        for c in customers:
            enriched.append({
                **{k: str(v) if isinstance(v, ObjectId) else v for k, v in c.items()},
                "_company_name": company["name"],
                "_company_prompt": company.get("system_prompt", ""),
            })

        print(f"[Dispatch] Found {len(enriched)} pending leads for company {company['name']}")
        return {**state, "pending_customers": enriched, "errors": []}

    except Exception as e:
        print(f"[Dispatch] Error fetching pending leads: {e}")
        return {**state, "error": str(e), "pending_customers": []}

async def trigger_vapi_calls(state: VoiceAgentState) -> VoiceAgentState:
    db = get_db()
    customers = state.get("pending_customers", [])
    dispatched = []
    errors = list(state.get("errors") or [])

    for customer in customers:
        customer_id = str(customer.get("_id") or customer.get("id", ""))
        try:
            call_result = await vapi_service.create_outbound_call(
                customer_name=customer["name"],
                customer_phone=customer["phone"],
                company_name=customer["_company_name"],
                company_system_prompt=customer["_company_prompt"],
                customer_id=customer_id,
                company_id=state["company_id"],
            )
            call_id = call_result.get("id", "")
            dispatched.append({"customer_id": customer_id, "call_id": call_id})

            await db.customers.update_one(
                {"_id": ObjectId(customer_id)},
                {
                    "$set": {
                        "status": "CALL_INITIATED",
                        "call_id": call_id,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            print(f"[Dispatch] Call initiated for {customer['name']} -> call_id={call_id}")

            await asyncio.sleep(0.5)

        except Exception as e:
            error_msg = f"Failed to call {customer.get('name', customer_id)}: {str(e)}"
            errors.append(error_msg)
            print(f"[Dispatch] {error_msg}")

            try:
                await db.customers.update_one(
                    {"_id": ObjectId(customer_id)},
                    {"$set": {"status": "FAILED", "updated_at": datetime.now(timezone.utc)}},
                )
            except Exception:
                pass

    return {**state, "dispatched_calls": dispatched, "errors": errors}

def build_dispatch_graph() -> Any:
    workflow = StateGraph(VoiceAgentState)

    workflow.add_node("fetch_pending_leads", fetch_pending_leads)
    workflow.add_node("trigger_vapi_calls", trigger_vapi_calls)

    workflow.set_entry_point("fetch_pending_leads")
    workflow.add_edge("fetch_pending_leads", "trigger_vapi_calls")
    workflow.add_edge("trigger_vapi_calls", END)

    return workflow.compile()

dispatch_graph = build_dispatch_graph()

async def run_dispatch_campaign(company_id: str) -> dict:
    initial_state: VoiceAgentState = {
        "company_id": company_id,
        "pending_customers": None,
        "dispatched_calls": None,
        "customer_id": None,
        "call_id": None,
        "transcript": None,
        "summary": None,
        "outcome": None,
        "confidence": None,
        "reasoning": None,
        "error": None,
        "errors": [],
    }

    result = await dispatch_graph.ainvoke(initial_state)
    return {
        "dispatched": result.get("dispatched_calls", []),
        "errors": result.get("errors", []),
        "error": result.get("error"),
    }
