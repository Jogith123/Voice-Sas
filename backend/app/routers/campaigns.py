from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from pydantic import BaseModel

from app.database import get_db
from app.langgraph.dispatch_graph import run_dispatch_campaign

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

class CampaignTriggerRequest(BaseModel):
    company_id: str

@router.post("/trigger", response_model=dict)
async def trigger_campaign(
    body: CampaignTriggerRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        company = await db.companies.find_one({"_id": ObjectId(body.company_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company ID")

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    pending_count = await db.customers.count_documents({
        "company_id": body.company_id,
        "status": "PENDING",
    })

    if pending_count == 0:
        return {
            "message": "No pending leads to call",
            "company_name": company["name"],
            "dispatched": 0,
        }

    background_tasks.add_task(run_dispatch_campaign, body.company_id)

    return {
        "message": f"Campaign initiated for {company['name']}",
        "company_name": company["name"],
        "pending_leads": pending_count,
        "status": "dispatching",
    }

@router.get("/stats/{company_id}", response_model=dict)
async def get_campaign_stats(company_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    cursor = db.customers.aggregate(pipeline)
    results = await cursor.to_list(length=20)

    stats = {
        "PENDING": 0,
        "CALL_INITIATED": 0,
        "QUALIFIED": 0,
        "NOT_INTERESTED": 0,
        "FAILED": 0,
        "NEEDS_REVIEW": 0,
        "total": 0,
    }
    for r in results:
        status = r["_id"]
        if status in stats:
            stats[status] = r["count"]
        stats["total"] += r["count"]

    return stats
