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

def test_normalize_makers_to_markers():
    """测试 makers 字段映射为 markers"""
    input_data = [
        {
            'title': 'Sheet 1',
            'topic': {
                'title': 'Root',
                'topics': [
                    {
                        'title': 'Test Case 1',
                        'makers': ['priority-1']
                    }
                ]
            }
        }
    ]

    result = normalize_xmind_data(input_data)

    # 验证原始 makers 字段保留
    assert result[0]['topic']['topics'][0]['makers'] == ['priority-1']
    # 验证新增 markers 字段
    assert result[0]['topic']['topics'][0]['markers'] == ['priority-1']

def test_normalize_empty_makers():
    """测试没有 makers 时添加空 markers"""
    input_data = [
        {
            'title': 'Sheet 1',
            'topic': {
                'title': 'Root',
                'topics': [
                    {'title': 'Test Case 1'}
                ]
            }
        }
    ]

    result = normalize_xmind_data(input_data)

    # 验证添加了空 markers
    assert result[0]['topic']['topics'][0]['markers'] == []

def test_normalize_labels_to_label():
    """测试 labels 字段映射为 label（取第一个）"""
    input_data = [
        {
            'title': 'Sheet 1',
            'topic': {
                'title': 'Root',
                'topics': [
                    {
                        'title': 'Test Case 1',
                        'labels': ['自动', '高优先级']
                    }
                ]
            }
        }
    ]

    result = normalize_xmind_data(input_data)

    # 验证原始 labels 字段保留
    assert result[0]['topic']['topics'][0]['labels'] == ['自动', '高优先级']
    # 验证新增 label 字段取第一个
    assert result[0]['topic']['topics'][0]['label'] == '自动'

def test_normalize_empty_labels():
    """测试没有 labels 时添加 None label"""
    input_data = [
        {
            'title': 'Sheet 1',
            'topic': {
                'title': 'Root',
                'topics': [
                    {'title': 'Test Case 1'}
                ]
            }
        }
    ]

    result = normalize_xmind_data(input_data)

    # 验证添加了 None label
    assert result[0]['topic']['topics'][0]['label'] is None
