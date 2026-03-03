# api/models/test_step.py
from sqlalchemy import String, Integer, Column, ForeignKey
from api.models.base import Base


class TestStep(Base):
    """测试步骤模型"""

    __tablename__ = "test_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    testcase_id = Column(
        Integer, ForeignKey("testcases.id", ondelete="CASCADE"), nullable=False
    )
    step_number = Column(Integer, nullable=False)
    actions = Column(String, nullable=False)
    expectedresults = Column(String, nullable=True)
    execution_type = Column(Integer, nullable=False, default=1)
    result = Column(Integer, nullable=True)
