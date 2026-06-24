"""Flask-SQLAlchemy 数据库模型"""

import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 默认列配置：所属模块、用例标题、前置条件、步骤、预期、优先级
DEFAULT_COLUMNS = [
    {
        "id": "suite",
        "name": "所属模块",
        "order": 1,
        "is_custom": False,
        "rich_text_break": False,
        "empty_check": False,
    },
    {
        "id": "name",
        "name": "用例标题",
        "order": 2,
        "is_custom": False,
        "rich_text_break": False,
        "empty_check": False,
    },
    {
        "id": "preconditions",
        "name": "前置条件",
        "order": 3,
        "is_custom": False,
        "rich_text_break": False,
        "empty_check": False,
    },
    {
        "id": "steps",
        "name": "步骤",
        "order": 4,
        "is_custom": False,
        "rich_text_break": False,
        "empty_check": False,
    },
    {
        "id": "expectedresults",
        "name": "预期",
        "order": 5,
        "is_custom": False,
        "rich_text_break": False,
        "empty_check": False,
    },
    {
        "id": "importance",
        "name": "优先级",
        "order": 6,
        "is_custom": False,
        "rich_text_break": False,
        "empty_check": False,
    },
]


class Record(db.Model):
    """上传文件记录"""

    __tablename__ = "records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(500), nullable=False)
    create_on = db.Column(db.String(50), nullable=False)
    note = db.Column(db.Text)
    is_deleted = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "create_on": self.create_on,
            "note": self.note,
            "is_deleted": self.is_deleted,
        }


class ColumnTemplate(db.Model):
    """列模版配置"""

    __tablename__ = "column_preferences"  # 保持表名兼容旧数据

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    columns_json = db.Column(db.Text, nullable=False)
    header_color = db.Column(db.String(20), default="#fef2f2")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def columns(self):
        """解析 columns_json 为列表"""
        return json.loads(self.columns_json) if self.columns_json else []

    @columns.setter
    def columns(self, value):
        """将列表序列化为 columns_json"""
        self.columns_json = json.dumps(value, ensure_ascii=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "columns": self.columns,
            "header_color": self.header_color or "#fef2f2",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AppSetting(db.Model):
    """应用设置（如上次导出使用的模版 ID）"""

    __tablename__ = "app_settings"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)


class CaseSnapshot(db.Model):
    """用例快照：按文件名持久化整份用例 JSON。

    首次预览从 XMind 解析初始化，之后以快照为准，使预览编辑得以持久化、
    导出也读取编辑后的内容。新表，db.create_all() 会自动建表，无需迁移。
    """

    __tablename__ = "case_snapshots"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(500), nullable=False, unique=True, index=True)
    cases_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
