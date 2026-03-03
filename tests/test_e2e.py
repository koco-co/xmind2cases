# tests/test_e2e.py
import pytest
import os
from xmind2testcase.utils import get_xmind_testcase_list
from xmind2testcase.zentao import xmind_to_zentao_csv_file

def test_xmind8_to_zentao_csv(xmind8_file):
    """测试 xmind8 到禅道 CSV 的完整流程"""
    # 步骤 1: 解析测试用例
    testcases = get_xmind_testcase_list(xmind8_file)
    assert len(testcases) > 0

    # 步骤 2: 转换为 CSV
    csv_file = xmind_to_zentao_csv_file(xmind8_file)
    assert os.path.exists(csv_file)

    # 步骤 3: 验证 CSV 文件格式
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

        # 验证有表头和数据行
        assert len(lines) > 1

        # 验证表头包含必要字段
        header = lines[0]
        assert '用例标题' in header or '用例名称' in header or 'name' in header.lower()

    # 清理生成的 CSV 文件
    if os.path.exists(csv_file):
        os.remove(csv_file)

def test_xmind2026_to_zentao_csv(xmind2026_file):
    """测试 xmind2026 到禅道 CSV 的完整流程"""
    # 步骤 1: 解析测试用例
    testcases = get_xmind_testcase_list(xmind2026_file)
    assert len(testcases) > 0

    # 步骤 2: 转换为 CSV
    csv_file = xmind_to_zentao_csv_file(xmind2026_file)
    assert os.path.exists(csv_file)

    # 步骤 3: 验证 CSV 文件格式
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

        # 验证有表头和数据行
        assert len(lines) > 1

        # 验证表头包含必要字段
        header = lines[0]
        assert '用例标题' in header or '用例名称' in header or 'name' in header.lower()

    # 清理生成的 CSV 文件
    if os.path.exists(csv_file):
        os.remove(csv_file)
