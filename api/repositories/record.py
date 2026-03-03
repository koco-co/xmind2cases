# api/repositories/record.py
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.record import Record
from api.models.testcase import TestCase
from api.repositories.base import BaseRepository


class RecordRepository(BaseRepository[Record]):
    """Record 数据访问层"""

    def __init__(self, db: AsyncSession):
        super().__init__(Record, db)

    async def get_with_testcase_count(self, id: int) -> Optional[dict]:
        """获取记录及其测试用例数量"""
        record = await self.get(id)
        if not record:
            return None

        result = await self.db.execute(
            select(func.count(TestCase.id)).where(TestCase.record_id == id)
        )
        count = result.scalar()

        return {**record.__dict__, "testcase_count": count or 0}

    async def list_not_deleted(self, skip: int = 0, limit: int = 20) -> List[Record]:
        """获取未删除的记录列表"""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.is_deleted == 0)
            .order_by(self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def soft_delete(self, id: int) -> bool:
        """软删除记录"""
        record = await self.get(id)
        if record:
            record.is_deleted = 1
            return True
        return False
