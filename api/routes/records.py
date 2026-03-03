# api/routes/records.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from api.core.database import get_db
from api.services.record import RecordService
from api.services.xmind_parser import XMindParserService
from api.schemas.record import RecordResponse
from api.core.exceptions import RecordNotFoundError

router = APIRouter(prefix="/records", tags=["records"])


def get_record_service(db: AsyncSession = Depends(get_db)) -> RecordService:
    """依赖注入：获取 RecordService"""
    parser = XMindParserService()
    return RecordService(db, parser)


@router.get("", response_model=List[RecordResponse])
async def list_records(
    skip: int = 0, limit: int = 20, service: RecordService = Depends(get_record_service)
):
    """获取记录列表"""
    return await service.list_records(skip, limit)


@router.post("", response_model=RecordResponse)
async def create_record(
    file: UploadFile = File(...), service: RecordService = Depends(get_record_service)
):
    """上传 XMind 文件并创建记录"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{record_id}")
async def get_record(
    record_id: int, service: RecordService = Depends(get_record_service)
):
    """获取记录详情"""
    try:
        return await service.get_record(record_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
