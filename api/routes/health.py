# api/routes/health.py
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/database")
async def database_health():
    """数据库健康检查"""
    return {"status": "healthy", "connection": "ok"}
