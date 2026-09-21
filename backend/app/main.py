from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.api.router import api_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Hospital Management System (HMS) - Modular Monolith API",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for MVP / Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include All Domain Routers under /api/v1
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "message": "Hospital Management System API is running",
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.app_version,
    }


@app.get("/api/v1/database-test")
async def database_test():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "test": value,
    }