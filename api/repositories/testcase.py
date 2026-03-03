# api/repositories/testcase.py
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.testcase import TestCase
from api.models.test_step import TestStep
from api.repositories.base import BaseRepository


class TestCaseRepository(BaseRepository[TestCase]):
    """TestCase 数据访问层"""

    def __init__(self, db: AsyncSession):
        super().__init__(TestCase, db)

    async def get_by_record(self, record_id: int) -> List[TestCase]:
        """获取记录的所有测试用例"""
        result = await self.db.execute(
            select(TestCase)
            .where(TestCase.record_id == record_id)
            .order_by(TestCase.id)
        )
        return list(result.scalars().all())

    async def create_with_steps(
        self, testcase_data: dict, steps_data: List[dict]
    ) -> TestCase:
        """创建测试用例及其步骤"""
        testcase = TestCase(**testcase_data)
        self.db.add(testcase)
        await self.db.flush()

        for step_data in steps_data:
            step_data["testcase_id"] = testcase.id
            step = TestStep(**step_data)
            self.db.add(step)

        return testcase
