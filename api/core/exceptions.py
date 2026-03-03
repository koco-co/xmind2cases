# api/core/exceptions.py
from typing import Any


class Xmind2CasesError(Exception):
    """基础异常类"""

    def __init__(self, message: str, detail: Any = None):
        self.message = message
        self.detail = detail
        super().__init__(message)


class ValidationError(Xmind2CasesError):
    """数据验证错误 (400)"""

    pass


class NotFoundError(Xmind2CasesError):
    """资源不存在 (404)"""

    pass


class ConflictError(Xmind2CasesError):
    """冲突错误 (409)"""

    pass


class BusinessLogicError(Xmind2CasesError):
    """业务逻辑错误 (422)"""

    pass


class FileValidationError(ValidationError):
    """文件验证失败"""

    pass


class RecordNotFoundError(NotFoundError):
    """记录不存在"""

    pass


class TestCaseNotFoundError(NotFoundError):
    """测试用例不存在"""

    pass


class XMindParserError(Xmind2CasesError):
    """XMind 文件解析错误"""

    pass
