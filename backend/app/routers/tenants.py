from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone

from app.database import get_db
from app.models.company import Company, CompanyCreate

router = APIRouter(prefix="/api/tenants", tags=["tenants"])

def _serialize_company(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/", response_model=list)
async def list_tenants(db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db.companies.find({})
    companies = await cursor.to_list(length=100)
    return [_serialize_company(c) for c in companies]

@router.post("/", response_model=dict, status_code=201)
async def create_tenant(payload: CompanyCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    existing = await db.companies.find_one({"slug": payload.slug})
    if existing:
        raise HTTPException(status_code=409, detail="Company slug already exists")
    doc = payload.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    result = await db.companies.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_company(doc)

@router.get("/{company_id}", response_model=dict)
async def get_tenant(company_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        company = await db.companies.find_one({"_id": ObjectId(company_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company ID")

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return _serialize_company(company)
