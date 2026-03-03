#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert XMind file to Zentao testcase CSV file.

Zentao official document about import CSV testcase file:
https://www.zentao.net/book/zentaopmshelp/243.mhtml
"""

import csv
import logging
import os
from typing import Any, Dict, List, Tuple

from xmind2testcase.utils import get_absolute_path, get_xmind_testcase_list


def xmind_to_zentao_csv_file(xmind_file: str) -> str:
    """Convert XMind file to a Zentao CSV file.

    Args:
        xmind_file: Path to the XMind file.

    Returns:
        Path to the created Zentao CSV file.
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info("Start converting XMind file(%s) to zentao file...", xmind_file)
    testcases = get_xmind_testcase_list(xmind_file)

    fileheader = [
        "所属模块",
        "用例标题",
        "前置条件",
        "步骤",
        "预期",
        "关键词",
        "优先级",
        "用例类型",
        "适用阶段",
    ]
    zentao_testcase_rows = [fileheader]

    for testcase in reversed(testcases):
        row = gen_a_testcase_row(testcase)
        zentao_testcase_rows.append(row)

    zentao_file = xmind_file[:-6] + ".csv"
    if os.path.exists(zentao_file):
        os.remove(zentao_file)

    with open(zentao_file, "w", encoding="utf8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(zentao_testcase_rows)
        logging.info(
            "Convert XMind file(%s) to a zentao csv file(%s) successfully!",
            xmind_file,
            zentao_file,
        )

    return zentao_file


def gen_a_testcase_row(testcase_dict: Dict[str, Any]) -> List[str]:
    """Generate a testcase row for Zentao CSV format.

    Args:
        testcase_dict: Dictionary containing testcase data.

    Returns:
        List of strings representing a CSV row.
    """
    case_module = gen_case_module(testcase_dict["suite"])
    case_title = testcase_dict["name"]
    case_precondition = testcase_dict["preconditions"].replace("\n", "<br>")
    case_step, case_expected_result = gen_case_step_and_expected_result(
        testcase_dict.get("steps", [])
    )
    case_keyword = ""
    case_priority = gen_case_priority(testcase_dict["importance"])
    case_type = gen_case_type(testcase_dict["execution_type"])
    case_apply_phase = "功能测试阶段"

    return [
        case_module,
        case_title,
        case_precondition,
        case_step,
        case_expected_result,
        case_keyword,
        case_priority,
        case_type,
        case_apply_phase,
    ]


def gen_case_module(module_name: str) -> str:
    """Generate case module name, normalizing parentheses.

    Args:
        module_name: Original module name.

    Returns:
        Normalized module name, or '/' if empty.
    """
    if module_name:
        module_name = module_name.replace("（", "(").replace("）", ")")
    else:
        module_name = "/"
    return module_name


def gen_case_step_and_expected_result(steps: List[Dict[str, Any]]) -> Tuple[str, str]:
    """Generate case step and expected result strings from steps.

    Args:
        steps: List of step dictionaries.

    Returns:
        Tuple of (case_step, case_expected_result) strings.
    """
    case_step = ""
    case_expected_result = ""

    for step_dict in steps:
        step_num = step_dict["step_number"]
        actions = step_dict["actions"].strip()
        case_step += f"{step_num}. {actions}\n"

        expected_results = step_dict.get("expectedresults", "")
        if expected_results:
            expected_results = expected_results.replace("\n", "\n").strip()
            case_expected_result += f"{step_num}. {expected_results}\n"

    return case_step, case_expected_result


def gen_case_priority(priority: int) -> str:
    """Generate case priority string.

    Args:
        priority: Priority value (1-4).

    Returns:
        String representation of priority, default '2'.
    """
    mapping = {1: "1", 2: "2", 3: "3", 4: "4"}
    return mapping.get(priority, "2")


def gen_case_type(case_type: int) -> str:
    """Generate case type string.

    Args:
        case_type: Case type value (1=功能测试, 2=接口测试).

    Returns:
        String representation of case type, default '功能测试'.
    """
    mapping = {1: "功能测试", 2: "接口测试"}
    return mapping.get(case_type, "功能测试")
