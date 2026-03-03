# tests/test_utils.py
import pytest
from xmind2testcase.utils import normalize_xmind_data

def test_normalize_xmind_data_invalid_input_not_list():
    """测试输入不是列表时抛出异常"""
    with pytest.raises(ValueError, match="Expected list from xmindparser"):
        normalize_xmind_data("not a list")

def test_normalize_xmind_data_empty_list():
    """测试空列表时抛出异常"""
    with pytest.raises(ValueError, match="XMind data is empty"):
        normalize_xmind_data([])
