"""NeerSetu — Autonomous Canal Irrigation Dispatcher & Conflict Resolver."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from db.database import init_db
from db.seed import seed
from api.farmers import router as farmers_router
from api.schedules import router as schedules_router
from api.emergency import router as emergency_router
from api.negotiations import router as negotiations_router
from api.credits import router as credits_router
from api.audit import router as audit_router
from api.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB and seed demo data
    init_db()
    seed()
    yield
    # Shutdown: nothing to clean up for SQLite


app = FastAPI(
    title="NeerSetu API",
    description=(
        "Autonomous Multi-Agent Canal Dispatcher and Conflict Resolver. "
        "Flow-aware fairness · Agentic negotiation · Water credit compensation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow all origins in development; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(dashboard_router)
app.include_router(farmers_router)
app.include_router(schedules_router)
app.include_router(emergency_router)
app.include_router(negotiations_router)
app.include_router(credits_router)
app.include_router(audit_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "NeerSetu",
        "version": "1.0.0",
        "status": "running",
        "tagline": "WaterBridge — Autonomous Canal Irrigation Dispatcher",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
