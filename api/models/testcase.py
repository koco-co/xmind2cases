# api/models/testcase.py
from sqlalchemy import String, Integer, Column, ForeignKey
from sqlalchemy.orm import relationship
from api.models.base import Base


class TestCase(Base):
    """测试用例模型"""

    __tablename__ = "testcases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(
        Integer, ForeignKey("records.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    summary = Column(String, nullable=True)
    preconditions = Column(String, nullable=True)
    execution_type = Column(Integer, nullable=False, default=1)
    importance = Column(Integer, nullable=False, default=2)
    estimated_exec_duration = Column(Integer, nullable=True)
    status = Column(Integer, nullable=False, default=7)
    version = Column(Integer, nullable=False, default=1)
    product = Column(String, nullable=True)
    suite = Column(String, nullable=True)
    result = Column(Integer, nullable=True)

    # 关系
    steps = relationship("TestStep", cascade="all, delete-orphan")
