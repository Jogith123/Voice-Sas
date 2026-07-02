"""
Database Seeding Script
=======================
Seeds the MongoDB database with 2 mock companies and 3 leads each.
Run: python scripts/seed_db.py

Requires MONGODB_URI and MONGODB_DB_NAME to be set in backend/.env
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from app.config import settings

def utcnow():
    return datetime.now(timezone.utc)

COMPANIES = [
    {
        "name": "Sunrise Realty",
        "slug": "sunrise-realty",
        "system_prompt": (
            "You are a professional real estate agent for Sunrise Realty, a premium home buying and selling agency. "
            "Sunrise Realty specializes in residential properties in suburban and urban markets. "
            "Your goal is to qualify leads by understanding if they want to buy or sell a property, "
            "their budget, preferred locations, timeline, and if they are pre-approved for financing. "
            "Be warm, knowledgeable, and helpful. Always emphasize Sunrise Realty's award-winning service "
            "and expert local market knowledge."
        ),
        "primary_color": "#f59e0b",
        "logo_url": None,
        "vapi_assistant_id": None,
        "created_at": utcnow(),
    },
    {
        "name": "BlueSky Rentals",
        "slug": "bluesky-rentals",
        "system_prompt": (
            "You are a friendly leasing consultant for BlueSky Rentals, a modern apartment rental company. "
            "BlueSky Rentals offers luxury and affordable apartment units across the city. "
            "Your goal is to qualify leads by understanding their rental needs: budget range, "
            "number of bedrooms, preferred neighborhoods, move-in date, and lease duration. "
            "Highlight BlueSky's amenities like rooftop pools, co-working spaces, and pet-friendly policies. "
            "Be enthusiastic and accommodating."
        ),
        "primary_color": "#3b82f6",
        "logo_url": None,
        "vapi_assistant_id": None,
        "created_at": utcnow(),
    },
    {
        "name": "Krid AI",
        "slug": "krid-ai",
        "system_prompt": (
            "You are an AI sales assistant for Krid AI, a cutting-edge real estate technology company. "
            "Krid AI helps property buyers, sellers, and investors leverage artificial intelligence "
            "to make smarter real estate decisions faster. "
            "Your goal is to qualify leads by understanding their real estate pain points, "
            "whether they are buyers, sellers, or investors, their timeline, and their interest level "
            "in AI-powered property analytics tools. "
            "Be innovative, concise, and data-driven in your approach."
        ),
        "primary_color": "#8b5cf6",
        "logo_url": None,
        "vapi_assistant_id": None,
        "created_at": utcnow(),
    },
]

LEADS_TEMPLATE = {
    "sunrise-realty": [
        {
            "name": "Jogith",
            "phone": "+919392330425",
            "email": "jogith@email.com",
            "notes": "Real phone for campaign demo",
            "status": "PENDING",
            "call_id": None,
        },
        {
            "name": "Dheeraj",
            "phone": "+917416322138",
            "email": "dheeraj@email.com",
            "notes": "Real phone for campaign demo",
            "status": "PENDING",
            "call_id": None,
        },
        {
            "name": "Prashant",
            "phone": "+919949429430",
            "email": "prashant@email.com",
            "notes": "Real phone for campaign demo",
            "status": "PENDING",
            "call_id": None,
        },
    ],
    "bluesky-rentals": [
        {
            "name": "Jogith",
            "phone": "+919392330425",
            "email": "jogith@email.com",
            "notes": "Real phone for campaign demo",
            "status": "PENDING",
            "call_id": None,
        },
        {
            "name": "Dheeraj",
            "phone": "+917416322138",
            "email": "dheeraj@email.com",
            "notes": "Real phone for campaign demo",
            "status": "PENDING",
            "call_id": None,
        },
        {
            "name": "Prashant",
            "phone": "+919949429430",
            "email": "prashant@email.com",
            "notes": "Real phone for campaign demo",
            "status": "PENDING",
            "call_id": None,
        },
    ],
    "krid-ai": [
        {
            "name": "Jogith",
            "phone": "+919392330425",
            "email": "jogith@email.com",
            "notes": "Real phone for campaign demo",
            "status": "PENDING",
            "call_id": None,
        },
        {
            "name": "Dheeraj",
            "phone": "+917416322138",
            "email": "dheeraj@email.com",
            "notes": "Real phone for campaign demo",
            "status": "PENDING",
            "call_id": None,
        },
        {
            "name": "Prashant",
            "phone": "+919949429430",
            "email": "prashant@email.com",
            "notes": "Real phone for campaign demo",
            "status": "PENDING",
            "call_id": None,
        },
    ],
}

async def seed():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    print(f"[Seed] Connecting to: {settings.MONGODB_DB_NAME}")

    await db.companies.delete_many({})
    await db.customers.delete_many({})
    await db.call_logs.delete_many({})
    print("[Seed] Cleared existing collections")

    company_id_map = {}
    for company_data in COMPANIES:
        result = await db.companies.insert_one(company_data.copy())
        company_id_map[company_data["slug"]] = str(result.inserted_id)
        print(f"[Seed] Inserted company: {company_data['name']} -> {result.inserted_id}")

    now = utcnow()
    for slug, leads in LEADS_TEMPLATE.items():
        company_id = company_id_map[slug]
        for lead in leads:
            doc = {
                **lead,
                "company_id": company_id,
                "created_at": now,
                "updated_at": now,
            }
            result = await db.customers.insert_one(doc)
            print(f"[Seed] Inserted lead: {lead['name']} -> {result.inserted_id}")

    await db.customers.create_index([("company_id", 1), ("status", 1)])
    await db.customers.create_index([("call_id", 1)])
    await db.call_logs.create_index([("customer_id", 1)])
    await db.call_logs.create_index([("vapi_call_id", 1)])
    print("[Seed] Indexes created")

    client.close()
    print("\n[Seed] Database seeded successfully!")
    print(f"[Seed] Companies: {list(company_id_map.keys())}")
    print("[Seed] Leads: 5 per company (15 total) - Jogith (+919392330425) & Dheeraj (+917416322138) added as leads in each company")

if __name__ == "__main__":
    asyncio.run(seed())
