# tests/test_e2e.py
import csv
import os
import tempfile

from xmind2cases.utils import get_xmind_testcase_list
from xmind2cases.zentao import xmind_to_zentao_csv_file


def _make_minimal_csv() -> str:
    """Create a minimal ZenTao CSV fixture file and return its path."""
    rows = [
        ["用例编号", "所属产品", "所属模块", "用例标题", "前置条件", "步骤", "预期", "优先级", "用例类型"],
        ["TC001", "产品A", "/模块1/子模块A", "登录验证", "用户已注册", "1. 输入账号\n2. 输入密码", "1. 登录成功", "1", "功能测试"],
        ["TC002", "产品A", "/模块1/子模块B", "注册验证", "无", "1. 输入信息", "1. 注册成功", "2", "接口测试"],
    ]
    path = os.path.join(tempfile.gettempdir(), "_test_zentao_csv.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return path


def test_csv_to_xmind_end_to_end():
    """测试 CSV → XMind 完整流程"""
    from xmind2cases.csv_to_xmind import zentao_csv_to_xmind_file, csv_to_testcase_dicts

    csv_path = _make_minimal_csv()

    # 步骤 1: CSV → XMind
    xmind_path = zentao_csv_to_xmind_file(csv_path)
    assert os.path.exists(xmind_path)
    assert xmind_path.endswith(".xmind")

    # 步骤 2: 验证 XMind 可被项目解析器解析
    suites = get_xmind_testcase_list(xmind_path)

    # 步骤 3: 验证用例数据
    assert len(suites) == 2
    assert suites[0]["product"] == "产品A"

    # 步骤 4: CSV → testcase dicts（Web API 格式）
    dicts = csv_to_testcase_dicts(csv_path)
    assert len(dicts) == 2
    assert dicts[0]["name"] == "登录验证"
    assert dicts[0]["importance"] == 1
    assert dicts[0]["execution_type"] == 1  # 功能测试
    assert dicts[1]["execution_type"] == 2  # 接口测试

    # 清理
    os.remove(xmind_path)
    os.remove(csv_path)


def test_csv_to_xmind_missing_columns():
    """测试缺少必需列时抛出异常"""
    from xmind2cases.csv_to_xmind import zentao_csv_to_xmind_file

    path = os.path.join(tempfile.gettempdir(), "_test_bad_csv.csv")
    with open(path, "w", encoding="utf-8") as f:
        f.write("标题,描述\n测试1,描述1\n")

    try:
        zentao_csv_to_xmind_file(path)
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "missing required columns" in str(e).lower()
    finally:
        os.remove(path)


def test_csv_to_xmind_file_not_found():
    """测试文件不存在时抛出异常"""
    from xmind2cases.csv_to_xmind import zentao_csv_to_xmind_file

    try:
        zentao_csv_to_xmind_file("/nonexistent/path.csv")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_csv_to_xmind_invalid_extension():
    """测试非 CSV 后缀时抛出异常"""
    from xmind2cases.csv_to_xmind import zentao_csv_to_xmind_file
    import tempfile

    # 创建一个非 CSV 文件
    path = os.path.join(tempfile.gettempdir(), "_test_not_csv.xmind")
    with open(path, "w", encoding="utf-8") as f:
        f.write("dummy")

    try:
        zentao_csv_to_xmind_file(path)
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "Expected a .csv file" in str(e)
    finally:
        os.remove(path)


def test_parse_steps_various_formats():
    """测试步骤解析的多种格式"""
    from xmind2cases.csv_to_xmind import _parse_steps, _parse_expected

    # 简单格式
    steps = _parse_steps("1. 步骤1\n2. 步骤2")
    assert len(steps) == 2
    assert steps[0] == "步骤1"

    # 含子编号
    steps = _parse_steps("1. 1）子步骤1\n2）子步骤2\n2. 步骤2")
    assert len(steps) == 2
    assert "子步骤1" in steps[0]

    # 空值
    assert _parse_steps("") == []
    assert _parse_steps("无") == []

    # 预期结果
    expected = _parse_expected("1. 结果1\n2. 结果2\n3. ")
    assert len(expected) >= 2


def test_module_path_parsing():
    """测试模块路径拆分"""
    from xmind2cases.csv_to_xmind import _module_path_parts

    parts = _module_path_parts("/A/B/C")
    assert parts == ["A", "B", "C"]

    parts = _module_path_parts("")
    assert parts == []

    parts = _module_path_parts("单一模块")
    assert parts == ["单一模块"]


def test_module_leaf_name():
    """测试只取所属模块最后一段（丢弃迭代前缀）"""
    from xmind2cases.csv_to_xmind import _module_leaf_name

    assert _module_leaf_name("/版本迭代测试用例/v6.4.11/真实模块(#10629)") == "真实模块(#10629)"
    assert _module_leaf_name("单一模块") == "单一模块"
    assert _module_leaf_name("") == ""
    assert _module_leaf_name("/") == ""


def test_split_title_modes():
    """测试标题分隔符拆分的各种模式"""
    from xmind2cases.csv_to_xmind import _split_title

    # 默认（None）按空格
    assert _split_title("平台管理 通知中心 验证X", None) == ["平台管理", "通知中心", "验证X"]
    # 任一符号都作切分点
    assert _split_title("A 通知-中心", [" ", "-"]) == ["A", "通知", "中心"]
    # 不拆分（空列表）
    assert _split_title("A 通知-中心", []) == ["A 通知-中心"]
    # 自定义多字符分隔符
    assert _split_title("A::B::C", ["::"]) == ["A", "B", "C"]
    # 空段被丢弃、首尾空白被裁剪
    assert _split_title("  A   B  ", [" "]) == ["A", "B"]
    # 空标题
    assert _split_title("", None) == []


def _make_split_csv() -> str:
    """三条共享标题前缀的用例，用于验证分组合并与嵌套。"""
    rows = [
        ["所属产品", "所属模块", "用例标题", "步骤", "预期", "优先级", "用例类型"],
        ["产品X", "/迭代/v1/真实模块", "登录 输入 验证账号正确", "1. a", "1. b", "1", "功能测试"],
        ["产品X", "/迭代/v1/真实模块", "登录 输入 验证密码正确", "1. a", "1. b", "2", "功能测试"],
        ["产品X", "/迭代/v1/真实模块", "登录 退出 验证退出成功", "1. a", "1. b", "3", "功能测试"],
    ]
    path = os.path.join(tempfile.gettempdir(), "_test_split_csv.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    return path


def _read_content(xmind_path: str):
    import json
    import zipfile

    with zipfile.ZipFile(xmind_path) as zf:
        return json.loads(zf.read("content.json"))


def test_csv_title_split_creates_nested_groups():
    """端到端：标题按空格拆出层级，共享前缀合并，叶子带标记并折叠"""
    from xmind2cases.csv_to_xmind import zentao_csv_to_xmind_file

    csv_path = _make_split_csv()
    out = zentao_csv_to_xmind_file(csv_path)  # 默认按空格
    sheets = _read_content(out)

    root = sheets[0]["rootTopic"]
    assert root["title"] == "产品X"

    # 模块只保留最后一段，迭代前缀被丢弃
    module = root["children"]["attached"][0]
    assert module["title"] == "真实模块"

    # 共享的 “登录” 分组只有一个
    assert [c["title"] for c in module["children"]["attached"]] == ["登录"]
    login = module["children"]["attached"][0]

    # “登录” 下有 “输入”“退出” 两个子分组
    assert [c["title"] for c in login["children"]["attached"]] == ["输入", "退出"]

    # “输入” 下挂两条用例
    inputs = login["children"]["attached"][0]
    assert [c["title"] for c in inputs["children"]["attached"]] == ["验证账号正确", "验证密码正确"]

    # 叶子用例：折叠 + 带优先级标记
    leaf = inputs["children"]["attached"][0]
    assert leaf.get("branch") == "folded"
    assert leaf.get("markers") == [{"markerId": "priority-1"}]

    os.remove(out)
    os.remove(csv_path)


def test_csv_no_split_keeps_title_flat():
    """delimiters=[] 时标题不拆，用例整条挂在模块下"""
    from xmind2cases.csv_to_xmind import zentao_csv_to_xmind_file

    csv_path = _make_split_csv()
    out = zentao_csv_to_xmind_file(csv_path, delimiters=[])
    sheets = _read_content(out)

    module = sheets[0]["rootTopic"]["children"]["attached"][0]
    assert module["title"] == "真实模块"
    titles = [c["title"] for c in module["children"]["attached"]]
    assert "登录 输入 验证账号正确" in titles

    os.remove(out)
    os.remove(csv_path)


def test_xmind_to_zentao_csv(test_xmind):
    """测试 xmind 到禅道 CSV 的完整流程"""
    # 步骤 1: 解析测试用例
    testcases = get_xmind_testcase_list(test_xmind)
    assert len(testcases) > 0

    # 步骤 2: 转换为 CSV
    csv_file = xmind_to_zentao_csv_file(test_xmind)
    assert os.path.exists(csv_file)

    # 步骤 3: 验证 CSV 文件格式
    with open(csv_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

        # 验证有表头和数据行
        assert len(lines) > 1

        # 验证表头包含必要字段
        header = lines[0]
        assert "用例标题" in header or "用例名称" in header or "name" in header.lower()

    # 清理生成的 CSV 文件
    if os.path.exists(csv_file):
        os.remove(csv_file)
