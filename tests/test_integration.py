# tests/test_integration.py
import os
from xmind2cases.utils import get_xmind_testsuites, get_xmind_testcase_list


def test_parse_xmind_file(test_xmind):
    """测试解析 xmind 文件"""
    testsuites = get_xmind_testsuites(test_xmind)

    # 验证返回了测试集
    assert len(testsuites) > 0

    # 验证测试集结构
    suite = testsuites[0]
    assert suite.name is not None
    assert len(suite.sub_suites) > 0


def test_xmind_to_testcase_list(test_xmind):
    """测试 xmind 文件转换为测试用例列表"""
    testcases = get_xmind_testcase_list(test_xmind)

    # 验证返回了测试用例
    assert len(testcases) > 0

    # 验证测试用例结构
    case = testcases[0]
    assert "name" in case
    assert "steps" in case
    assert "product" in case
    assert "suite" in case


def test_convert_to_csv(test_xmind):
    """测试 CSV 转换功能"""
    from xmind2cases.zentao import xmind_to_zentao_csv_file

    # 转换为 CSV
    csv_file = xmind_to_zentao_csv_file(test_xmind)

    # 验证文件创建
    assert os.path.exists(csv_file)
    assert csv_file.endswith(".csv")

    # 验证文件内容不为空
    with open(csv_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert len(content) > 0
        # CSV 应该包含表头
        assert "用例标题" in content or "用例名称" in content or "TestCase" in content

    # 清理生成的 CSV 文件
    if os.path.exists(csv_file):
        os.remove(csv_file)


def test_zentao_csv_header_has_requirements_column(test_xmind):
    """CSV 表头在所属模块后紧跟相关需求"""
    from xmind2cases.zentao import xmind_to_zentao_csv_file

    import csv

    csv_file = xmind_to_zentao_csv_file(test_xmind)
    try:
        with open(csv_file, encoding="utf-8") as f:
            header = next(csv.reader(f))
        assert header[0] == "所属模块"
        assert header[1] == "相关需求"
        assert header[2] == "用例标题"
    finally:
        if os.path.exists(csv_file):
            os.remove(csv_file)


def test_parser_attaches_requirements_from_l1_labels():
    """相关需求默认取自 L1 节点的 labels 标签 (#xxxxx)"""
    from xmind2cases.parser import xmind_to_testsuites

    content = [
        {
            "title": "产品(#23)",
            "topic": {
                "title": "产品(#23)",
                "note": None,
                "topics": [
                    {
                        "title": "模块(#10629)",
                        "note": None,
                        "labels": ["(#15889)"],
                        "topics": [
                            {
                                "title": "用例1",
                                "markers": ["priority-2"],
                                "topics": [],
                            },
                        ],
                    },
                ],
            },
        }
    ]
    suites = xmind_to_testsuites(content)
    cases = suites[0].sub_suites[0].testcase_list
    assert cases[0].requirements == "(#15889)"


def test_gen_case_module_keeps_only_requirement_id():
    """所属模块简写为标题内的需求编号 (#xxxxx)"""
    from xmind2cases.zentao import gen_case_module

    assert gen_case_module("模块(#10629)") == "(#10629)"
    assert gen_case_module("模块（自动化）(#12345)") == "(#12345)"
    assert gen_case_module("无编号模块") == "无编号模块"
    assert gen_case_module("") == "/"


def test_zentao_row_requirements_and_fullwidth_parens():
    """行生成：相关需求列 + 全角括号统一转半角"""
    from xmind2cases.zentao import gen_a_testcase_row

    tc = {
        "suite": "模块（X）(#12345)",
        "name": "验证（登录）功能",
        "preconditions": "前置（条件）",
        "importance": 1,
        "execution_type": 1,
        "requirements": "(#15889)",
        "steps": [
            {
                "step_number": 1,
                "actions": "1）输入账号（admin）",
                "expectedresults": "2）登录成功）",
            },
        ],
    }
    row = gen_a_testcase_row(tc)
    assert row[0] == "(#12345)"  # 所属模块简写
    assert row[1] == "(#15889)"  # 相关需求
    assert row[2] == "验证(登录)功能"  # 标题全角→半角
    assert row[3] == "前置(条件)"
    assert row[4] == "1. 1)输入账号(admin)\n"
    assert "（" not in "".join(row) and "）" not in "".join(row)
