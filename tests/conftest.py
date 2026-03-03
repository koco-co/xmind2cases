# tests/conftest.py
import os
import pytest

# 测试文件路径
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")


@pytest.fixture
def xmind8_file():
    """xmind8 版本测试文件"""
    return os.path.join(DOCS_DIR, "202602-数据资产v6.4.8(xmind8版本).xmind")


@pytest.fixture
def xmind2026_file():
    """xmind2026 版本测试文件"""
    return os.path.join(DOCS_DIR, "202602-数据资产v6.4.8(xmind2026版本).xmind")


@pytest.fixture
def reference_csv():
    """参考 CSV 文件"""
    return os.path.join(DOCS_DIR, "202602-数据资产v6.4.8(xmind8版本).csv")
