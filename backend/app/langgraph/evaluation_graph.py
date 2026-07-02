from datetime import datetime, timezone
from typing import Any, Literal

from langgraph.graph import StateGraph, END

from app.langgraph.state import VoiceAgentState
from app.database import get_db
from app.services.llm_service import analyze_call_transcript
from bson import ObjectId

async def extract_transcript(state: VoiceAgentState) -> VoiceAgentState:
    transcript = state.get("transcript") or ""
    summary = state.get("summary") or ""

    if not transcript and not summary:
        print("[Evaluation] Warning: No transcript or summary available for analysis")

    print(f"[Evaluation] Transcript length: {len(transcript)} chars, Summary: {bool(summary)}")
    return {**state, "transcript": transcript, "summary": summary}

async def analyze_with_llm(state: VoiceAgentState) -> VoiceAgentState:
    result = await analyze_call_transcript(
        transcript=state.get("transcript", ""),
        summary=state.get("summary", ""),
    )
    print(f"[Evaluation] LLM result -> outcome={result['outcome']}, confidence={result['confidence']:.2f}")
    return {
        **state,
        "outcome": result["outcome"],
        "confidence": result["confidence"],
        "reasoning": result["reasoning"],
    }

def route_by_confidence(state: VoiceAgentState) -> Literal["update_status"]:
    outcome = state.get("outcome", "NEEDS_REVIEW")
    confidence = state.get("confidence", 0.0)
    print(f"[Evaluation] Routing: outcome={outcome}, confidence={confidence:.2f}")
    return "update_status"

async def update_status(state: VoiceAgentState) -> VoiceAgentState:
    db = get_db()
    customer_id = state.get("customer_id")
    company_id = state.get("company_id")
    call_id = state.get("call_id", "")
    outcome = state.get("outcome", "NEEDS_REVIEW")
    now = datetime.now(timezone.utc)

    try:
        update_result = await db.customers.update_one(
            {"_id": ObjectId(customer_id)},
            {
                "$set": {
                    "status": outcome,
                    "updated_at": now,
                }
            },
        )

        if update_result.matched_count == 0:
            await db.customers.update_one(
                {"call_id": call_id},
                {"$set": {"status": outcome, "updated_at": now}},
            )

        call_log = {
            "customer_id": customer_id,
            "company_id": company_id,
            "vapi_call_id": call_id,
            "status": "completed",
            "transcript": state.get("transcript"),
            "summary": state.get("summary"),
            "llm_reasoning": state.get("reasoning"),
            "outcome": outcome,
            "confidence": state.get("confidence"),
            "created_at": now,
        }
        await db.call_logs.insert_one(call_log)

        print(f"[Evaluation] Status updated -> customer={customer_id}, outcome={outcome}")

    except Exception as e:
        print(f"[Evaluation] Error updating status: {e}")
        return {**state, "error": str(e)}

    return {**state}

def build_evaluation_graph() -> Any:
    workflow = StateGraph(VoiceAgentState)

    workflow.add_node("extract_transcript", extract_transcript)
    workflow.add_node("analyze_with_llm", analyze_with_llm)
    workflow.add_node("update_status", update_status)

    workflow.set_entry_point("extract_transcript")
    workflow.add_edge("extract_transcript", "analyze_with_llm")
    workflow.add_conditional_edges(
        "analyze_with_llm",
        route_by_confidence,
        {"update_status": "update_status"},
    )
    workflow.add_edge("update_status", END)

    return workflow.compile()

evaluation_graph = build_evaluation_graph()

async def run_evaluation(
    company_id: str,
    customer_id: str,
    call_id: str,
    transcript: str,
    summary: str,
) -> dict:
    initial_state: VoiceAgentState = {
        "company_id": company_id,
        "customer_id": customer_id,
        "call_id": call_id,
        "transcript": transcript,
        "summary": summary,
        "pending_customers": None,
        "dispatched_calls": None,
        "outcome": None,
        "confidence": None,
        "reasoning": None,
        "error": None,
        "errors": [],
    }

    result = await evaluation_graph.ainvoke(initial_state)
    return {
        "outcome": result.get("outcome"),
        "confidence": result.get("confidence"),
        "reasoning": result.get("reasoning"),
        "error": result.get("error"),
    }
