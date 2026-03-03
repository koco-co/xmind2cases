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

def test_normalize_default_fields():
    """测试添加默认字段（note, comment, link, id）"""
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

    topic = result[0]['topic']['topics'][0]

    # 验证所有默认字段存在
    assert 'note' in topic
    assert topic['note'] is None
    assert 'comment' in topic
    assert topic['comment'] is None
    assert 'link' in topic
    assert topic['link'] is None
    assert 'id' in topic
    assert topic['id'] is None

def test_normalize_deeply_nested_structure():
    """测试深层嵌套结构的处理"""
    input_data = [
        {
            'title': 'Sheet 1',
            'topic': {
                'title': 'Root',
                'topics': [
                    {
                        'title': 'Suite 1',
                        'topics': [
                            {
                                'title': 'Sub-suite 1',
                                'topics': [
                                    {
                                        'title': 'Test Case 1',
                                        'makers': ['priority-2'],
                                        'labels': ['手动']
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    ]

    result = normalize_xmind_data(input_data)

    # 验证深层嵌套的节点也被正确处理
    test_case = result[0]['topic']['topics'][0]['topics'][0]['topics'][0]

    assert test_case['markers'] == ['priority-2']
    assert test_case['label'] == '手动'
    assert test_case['note'] is None
    assert test_case['comment'] is None

def test_normalize_preserves_original_data():
    """测试标准化不修改原始数据"""
    import copy

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

    # 创建原始数据的深拷贝用于对比
    original_data = copy.deepcopy(input_data)

    # 执行标准化
    result = normalize_xmind_data(input_data)

    # 验证原始数据未被修改
    assert input_data == original_data

    # 验证返回的是新对象
    assert input_data is not result

    # 验证结果包含 markers
    assert result[0]['topic']['topics'][0]['markers'] == ['priority-1']

    # 验证原始数据没有 markers
    assert 'markers' not in input_data[0]['topic']['topics'][0]

def test_get_xmind_testsuites_file_not_found():
    """测试文件不存在时抛出异常"""
    from xmind2testcase.utils import get_xmind_testsuites

    with pytest.raises(FileNotFoundError, match="XMind file not found"):
        get_xmind_testsuites('nonexistent.xmind')

def test_get_xmind_testsuites_invalid_format():
    """测试无效文件格式时抛出异常"""
    from xmind2testcase.utils import get_xmind_testsuites
    import tempfile
    import os

    # 创建一个非 .xmind 文件
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        temp_file = f.name
        f.write(b"invalid content")

    try:
        with pytest.raises(ValueError, match="Invalid file format"):
            get_xmind_testsuites(temp_file)
    finally:
        os.unlink(temp_file)
