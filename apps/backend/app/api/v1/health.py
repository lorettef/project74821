from fastapi import APIRouter

from app.core.config import settings
from app.core.database import check_db_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    db_connected = await check_db_connection()
    return {
        "status": "ok",
        "db": "connected" if db_connected else "disconnected",
        "version": settings.APP_VERSION,
    }
