# tests/test_integration.py
import pytest
from xmind2testcase.utils import get_xmind_testsuites, get_xmind_testcase_list

def test_parse_xmind8_file(xmind8_file):
    """测试解析 xmind8 文件"""
    testsuites = get_xmind_testsuites(xmind8_file)

    # 验证返回了测试集
    assert len(testsuites) > 0

    # 验证测试集结构
    suite = testsuites[0]
    assert suite.name is not None
    assert len(suite.sub_suites) > 0

def test_xmind8_to_testcase_list(xmind8_file):
    """测试 xmind8 文件转换为测试用例列表"""
    testcases = get_xmind_testcase_list(xmind8_file)

    # 验证返回了测试用例
    assert len(testcases) > 0

    # 验证测试用例结构
    case = testcases[0]
    assert 'name' in case
    assert 'steps' in case
    assert 'product' in case
    assert 'suite' in case
