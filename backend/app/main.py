import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import connect_db, close_db
from app.routers import tenants, leads, campaigns, webhooks

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()

app = FastAPI(
    title="Voice AI Orchestrator API",
    description="Multi-Tenant Agentic Voice AI SaaS – powered by LangGraph + Vapi AI",
    version="1.0.0",
    lifespan=lifespan,
)

_origins = ["*"] if settings.APP_ENV == "development" else settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=settings.APP_ENV == "development",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenants.router)
app.include_router(leads.router)
app.include_router(campaigns.router)
app.include_router(webhooks.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "voice-ai-orchestrator"}

FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

if os.path.exists(FRONTEND_BUILD_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = os.path.join(FRONTEND_BUILD_DIR, "index.html")
        return FileResponse(index)
