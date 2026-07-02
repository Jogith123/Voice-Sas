from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

_client: AsyncIOMotorClient = None

async def connect_db():
    global _client
    try:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
        )
        await _client.admin.command("ping")
        print("[DB] Connected to MongoDB: " + settings.MONGODB_DB_NAME)
    except Exception as e:
        print("[DB] WARNING: MongoDB connection failed: " + str(e))
        print("[DB] Server will start, but DB-dependent routes will fail.")
        print("[DB] Update MONGODB_URI in backend/.env and restart.")

async def close_db():
    global _client
    if _client:
        _client.close()
        print("[DB] MongoDB connection closed.")

def get_db() -> AsyncIOMotorDatabase:
    return _client[settings.MONGODB_DB_NAME]
