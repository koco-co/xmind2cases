# tests/test_utils.py
import pytest
from xmind2cases.utils import normalize_xmind_data


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
            "title": "Sheet 1",
            "topic": {
                "title": "Root",
                "topics": [{"title": "Test Case 1", "makers": ["priority-1"]}],
            },
        }
    ]

    result = normalize_xmind_data(input_data)

    # 验证原始 makers 字段保留
    assert result[0]["topic"]["topics"][0]["makers"] == ["priority-1"]
    # 验证新增 markers 字段
    assert result[0]["topic"]["topics"][0]["markers"] == ["priority-1"]


def test_normalize_empty_makers():
    """测试没有 makers 时添加空 markers"""
    input_data = [
        {
            "title": "Sheet 1",
            "topic": {"title": "Root", "topics": [{"title": "Test Case 1"}]},
        }
    ]

    result = normalize_xmind_data(input_data)

    # 验证添加了空 markers
    assert result[0]["topic"]["topics"][0]["markers"] == []


def test_normalize_labels_to_label():
    """测试 labels 字段映射为 label（取第一个）"""
    input_data = [
        {
            "title": "Sheet 1",
            "topic": {
                "title": "Root",
                "topics": [{"title": "Test Case 1", "labels": ["自动", "高优先级"]}],
            },
        }
    ]

    result = normalize_xmind_data(input_data)

    # 验证原始 labels 字段保留
    assert result[0]["topic"]["topics"][0]["labels"] == ["自动", "高优先级"]
    # 验证新增 label 字段取第一个
    assert result[0]["topic"]["topics"][0]["label"] == "自动"


def test_normalize_empty_labels():
    """测试没有 labels 时添加 None label"""
    input_data = [
        {
            "title": "Sheet 1",
            "topic": {"title": "Root", "topics": [{"title": "Test Case 1"}]},
        }
    ]

    result = normalize_xmind_data(input_data)

    # 验证添加了 None label
    assert result[0]["topic"]["topics"][0]["label"] is None


def test_normalize_default_fields():
    """测试添加默认字段（note, comment, link, id）"""
    input_data = [
        {
            "title": "Sheet 1",
            "topic": {"title": "Root", "topics": [{"title": "Test Case 1"}]},
        }
    ]

    result = normalize_xmind_data(input_data)

    topic = result[0]["topic"]["topics"][0]

    # 验证所有默认字段存在
    assert "note" in topic
    assert topic["note"] is None
    assert "comment" in topic
    assert topic["comment"] is None
    assert "link" in topic
    assert topic["link"] is None
    assert "id" in topic
    assert topic["id"] is None


def test_normalize_deeply_nested_structure():
    """测试深层嵌套结构的处理"""
    input_data = [
        {
            "title": "Sheet 1",
            "topic": {
                "title": "Root",
                "topics": [
                    {
                        "title": "Suite 1",
                        "topics": [
                            {
                                "title": "Sub-suite 1",
                                "topics": [
                                    {
                                        "title": "Test Case 1",
                                        "makers": ["priority-2"],
                                        "labels": ["手动"],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        }
    ]

    result = normalize_xmind_data(input_data)

    # 验证深层嵌套的节点也被正确处理
    test_case = result[0]["topic"]["topics"][0]["topics"][0]["topics"][0]

    assert test_case["markers"] == ["priority-2"]
    assert test_case["label"] == "手动"
    assert test_case["note"] is None
    assert test_case["comment"] is None


def test_normalize_preserves_original_data():
    """测试标准化不修改原始数据"""
    import copy

    input_data = [
        {
            "title": "Sheet 1",
            "topic": {
                "title": "Root",
                "topics": [{"title": "Test Case 1", "makers": ["priority-1"]}],
            },
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
    assert result[0]["topic"]["topics"][0]["markers"] == ["priority-1"]

    # 验证原始数据没有 markers
    assert "markers" not in input_data[0]["topic"]["topics"][0]


def test_get_xmind_testsuites_file_not_found():
    """测试文件不存在时抛出异常"""
    from xmind2cases.utils import get_xmind_testsuites

    with pytest.raises(FileNotFoundError, match="XMind file not found"):
        get_xmind_testsuites("nonexistent.xmind")


def test_get_xmind_testsuites_invalid_format():
    """测试无效文件格式时抛出异常"""
    from xmind2cases.utils import get_xmind_testsuites
    import tempfile
    import os

    # 创建一个非 .xmind 文件
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        temp_file = f.name
        f.write(b"invalid content")

    try:
        with pytest.raises(ValueError, match="Invalid file format"):
            get_xmind_testsuites(temp_file)
    finally:
        os.unlink(temp_file)


# ---------------------------------------------------------------------------
# Regression tests: XMind files with missing sheet-level title (新版 XMind 2026+)
# ---------------------------------------------------------------------------

def _make_xmind_zen_bytes(sheets_json: str) -> bytes:
    """Build a minimal in-memory XMind Zen (ZIP) file from a sheets JSON string."""
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("content.json", sheets_json)
        zf.writestr("metadata.json", '{"creator":{"name":"test","version":"1.0"}}')
        zf.writestr("manifest.json", '{"file-entries":{"content.json":{}}}')
    buf.seek(0)
    return buf.read()


def test_normalize_topic_adds_default_title():
    """normalize_topic should add an empty-string title when the key is missing."""
    input_data = [
        {
            "title": "Sheet 1",
            "topic": {
                "title": "Root",
                "topics": [
                    {
                        # No "title" key at all — should be defaulted to ""
                        "markers": [],
                    }
                ],
            },
        }
    ]
    result = normalize_xmind_data(input_data)
    child = result[0]["topic"]["topics"][0]
    assert "title" in child
    assert child["title"] == ""


def test_xmindparser_compat_patch_missing_sheet_title(tmp_path):
    """get_xmind_testsuites should parse files whose sheets lack a title key.

    This reproduces the exact failure mode of 20260322-信永中和测试用例.xmind
    where the sheet object in content.json has no 'title' field.
    """
    import json

    # Build a minimal XMind Zen file whose sheet has NO 'title' field but
    # whose rootTopic has a title — exactly the new XMind 2026+ format.
    sheets = [
        {
            "id": "sheet-001",
            "class": "sheet",
            # 'title' intentionally omitted
            "rootTopic": {
                "id": "topic-001",
                "class": "topic",
                "title": "产品名称",
                "children": {
                    "attached": [
                        {
                            "id": "topic-002",
                            "title": "模块A",
                            "children": {
                                "attached": [
                                    {
                                        "id": "topic-003",
                                        "title": "测试用例1",
                                    }
                                ]
                            },
                        }
                    ]
                },
            },
        }
    ]

    xmind_file = tmp_path / "no_sheet_title.xmind"
    xmind_file.write_bytes(_make_xmind_zen_bytes(json.dumps(sheets)))

    from xmind2cases.utils import get_xmind_testsuites

    # Should not raise; previously raised ValueError("...Error: 'title'")
    suites = get_xmind_testsuites(str(xmind_file))
    assert len(suites) >= 1
    # The suite name should come from rootTopic.title
    assert suites[0].name == "产品名称"


def test_xmindparser_compat_patch_with_sheet_title(tmp_path):
    """get_xmind_testsuites should still work normally when sheet title IS present."""
    import json

    sheets = [
        {
            "id": "sheet-001",
            "class": "sheet",
            "title": "画布 1",
            "rootTopic": {
                "id": "topic-001",
                "class": "topic",
                "title": "产品名称",
                "children": {
                    "attached": [
                        {
                            "id": "topic-002",
                            "title": "模块A",
                            "children": {
                                "attached": [
                                    {
                                        "id": "topic-003",
                                        "title": "测试用例1",
                                    }
                                ]
                            },
                        }
                    ]
                },
            },
        }
    ]

    xmind_file = tmp_path / "with_sheet_title.xmind"
    xmind_file.write_bytes(_make_xmind_zen_bytes(json.dumps(sheets)))

    from xmind2cases.utils import get_xmind_testsuites

    suites = get_xmind_testsuites(str(xmind_file))
    assert len(suites) >= 1
    assert suites[0].name == "产品名称"

