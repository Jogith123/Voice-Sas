from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone

from app.database import get_db
from app.models.customer import CustomerCreate, CustomerUpdate, CustomerStatus

router = APIRouter(prefix="/api/leads", tags=["leads"])

def _serialize_customer(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    for k in ("created_at", "updated_at"):
        if k in doc and hasattr(doc[k], "isoformat"):
            doc[k] = doc[k].isoformat()
    return doc

def _serialize_log(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    for k in ("created_at", "started_at", "ended_at"):
        if k in doc and hasattr(doc[k], "isoformat"):
            doc[k] = doc[k].isoformat()
    return doc

@router.get("/", response_model=list)
async def list_leads(
    company_id: str = Query(..., description="Filter leads by company ID"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.customers.find({"company_id": company_id}).sort("created_at", -1)
    customers = await cursor.to_list(length=500)
    return [_serialize_customer(c) for c in customers]

@router.get("/{customer_id}", response_model=dict)
async def get_lead(customer_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        customer = await db.customers.find_one({"_id": ObjectId(customer_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid customer ID")

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return _serialize_customer(customer)

@router.get("/{customer_id}/call-log", response_model=dict)
async def get_lead_call_log(customer_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    log = await db.call_logs.find_one(
        {"customer_id": customer_id},
        sort=[("created_at", -1)],
    )
    if not log:
        raise HTTPException(status_code=404, detail="No call log found for this customer")
    return _serialize_log(log)

@router.post("/", response_model=dict, status_code=201)
async def create_lead(body: CustomerCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    now = datetime.now(timezone.utc)
    doc = body.model_dump()
    doc["status"] = CustomerStatus.PENDING
    doc["created_at"] = now
    doc["updated_at"] = now

    result = await db.customers.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return doc

@router.patch("/{customer_id}", response_model=dict)
async def update_lead(
    customer_id: str,
    body: CustomerUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)

    result = await db.customers.find_one_and_update(
        {"_id": ObjectId(customer_id)},
        {"$set": update_data},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")

    return _serialize_customer(result)

@router.delete("/{customer_id}", status_code=204)
async def delete_lead(customer_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db.customers.delete_one({"_id": ObjectId(customer_id)})

@router.post("/{customer_id}/reset", response_model=dict)
async def reset_lead_status(customer_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    now = datetime.now(timezone.utc)
    result = await db.customers.find_one_and_update(
        {"_id": ObjectId(customer_id)},
        {"$set": {"status": "PENDING", "call_id": None, "updated_at": now}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _serialize_customer(result)
