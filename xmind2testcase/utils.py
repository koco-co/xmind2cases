#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Utility functions for XMind file processing."""
import json
import logging
import os
from typing import Any, Dict, List

from xmind2testcase.metadata import TestSuite
from xmind2testcase.parser import xmind_to_testsuites


def normalize_xmind_data(xmind_dict: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize xmindparser output to match legacy xmind library format.

    Args:
        xmind_dict: Raw output from xmindparser.xmind_to_dict()

    Returns:
        Normalized data structure matching old xmind library format

    Raises:
        ValueError: If input is invalid or empty
    """
    if not isinstance(xmind_dict, list):
        raise ValueError(
            f"Expected list from xmindparser, got {type(xmind_dict).__name__}"
        )

    if len(xmind_dict) == 0:
        raise ValueError("XMind data is empty")

    def normalize_topic(topic: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single topic node."""
        if not isinstance(topic, dict):
            return topic

        # 字段映射：makers → markers
        if 'makers' in topic:
            topic['markers'] = topic['makers']

        # 确保 markers 字段存在
        if 'markers' not in topic:
            topic['markers'] = []

        # 字段映射：labels → label
        if 'labels' in topic and isinstance(topic['labels'], list):
            # 取第一个 label，或 None
            topic['label'] = topic['labels'][0] if topic['labels'] else None
        elif 'label' not in topic:
            topic['label'] = None

        # 确保其他必需字段存在
        topic.setdefault('note', None)
        topic.setdefault('comment', None)
        topic.setdefault('link', None)
        topic.setdefault('id', None)

        # 递归处理子 topics
        if 'topics' in topic and isinstance(topic['topics'], list):
            topic['topics'] = [
                normalize_topic(sub_topic)
                for sub_topic in topic['topics']
            ]

        return topic

    # 深拷贝以避免修改原始数据
    import copy
    normalized_dict = copy.deepcopy(xmind_dict)

    # 标准化每个 sheet
    for sheet in normalized_dict:
        if 'topic' in sheet and isinstance(sheet['topic'], dict):
            sheet['topic'] = normalize_topic(sheet['topic'])

    return normalized_dict


def get_absolute_path(path: str) -> str:
    """Return the absolute path of a file.

    If path contains a start point (e.g., Unix '/') then use the specified
    start point instead of the current working directory. The starting point
    of the file path is allowed to begin with a tilde "~", which will be
    replaced with the user's home directory.

    Args:
        path: File path to convert to absolute path.

    Returns:
        Absolute path of the file.
    """
    file_path, file_name = os.path.split(path)
    if not file_path:
        file_path = os.getcwd()
    file_path = os.path.abspath(os.path.expanduser(file_path))
    return os.path.join(file_path, file_name)


def get_xmind_testsuites(xmind_file: str) -> List[TestSuite]:
    """Load the XMind file and parse to TestSuite list.

    Args:
        xmind_file: Path to the XMind file.

    Returns:
        List of TestSuite objects parsed from the XMind file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid or parsing fails.
    """
    from xmindparser import xmind_to_dict

    xmind_file = get_absolute_path(xmind_file)

    # 文件存在性检查
    if not os.path.exists(xmind_file):
        raise FileNotFoundError(
            f"XMind file not found: {xmind_file}"
        )

    # 文件扩展名检查
    if not xmind_file.lower().endswith('.xmind'):
        raise ValueError(
            f"Invalid file format. Expected .xmind file, got: {xmind_file}"
        )

    logging.info('Parsing XMind file: %s', xmind_file)

    # 解析文件
    try:
        xmind_content_dict = xmind_to_dict(xmind_file)
    except Exception as e:
        raise ValueError(
            f"Failed to parse XMind file: {xmind_file}. "
            f"Error: {str(e)}"
        ) from e

    # 数据验证
    if not xmind_content_dict:
        raise ValueError(
            f"Invalid XMind file: {xmind_file}. "
            "File is empty or contains no valid data."
        )

    # 标准化数据格式
    try:
        xmind_content_dict = normalize_xmind_data(xmind_content_dict)
    except Exception as e:
        raise ValueError(
            f"Failed to normalize XMind data: {str(e)}"
        ) from e

    logging.debug("Normalized XMind data: %s", xmind_content_dict)

    # 解析为 TestSuite 对象
    testsuites = xmind_to_testsuites(xmind_content_dict)

    logging.info('Successfully parsed %d testsuite(s)', len(testsuites))
    return testsuites


def _calculate_suite_statistics(testcase_list: List[Any]) -> Dict[str, int]:
    """Calculate statistics for a list of test cases.

    Args:
        testcase_list: List of test cases.

    Returns:
        Dictionary with statistics: case_num, non_execution, pass, failed,
        blocked, skipped.
    """
    statistics = {
        'case_num': len(testcase_list),
        'non_execution': 0,
        'pass': 0,
        'failed': 0,
        'blocked': 0,
        'skipped': 0
    }

    for case in testcase_list:
        result = case.result
        if result == 0:
            statistics['non_execution'] += 1
        elif result == 1:
            statistics['pass'] += 1
        elif result == 2:
            statistics['failed'] += 1
        elif result == 3:
            statistics['blocked'] += 1
        elif result == 4:
            statistics['skipped'] += 1
        else:
            logging.warning('This testcase result is abnormal: %s, '
                           'please check it: %s', result, case.to_dict())

    return statistics


def get_xmind_testsuite_list(xmind_file: str) -> List[Dict[str, Any]]:
    """Load the XMind file and get all testsuites in it.

    Args:
        xmind_file: Path to the target XMind file.

    Returns:
        A list of testsuite data dictionaries.
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testsuite data list...',
                 xmind_file)
    testsuite_list = get_xmind_testsuites(xmind_file)
    suite_data_list = []

    for testsuite in testsuite_list:
        product_statistics = {
            'case_num': 0,
            'non_execution': 0,
            'pass': 0,
            'failed': 0,
            'blocked': 0,
            'skipped': 0
        }
        for sub_suite in testsuite.sub_suites:
            suite_statistics = _calculate_suite_statistics(
                sub_suite.testcase_list or []
            )
            sub_suite.statistics = suite_statistics
            for item in product_statistics:
                product_statistics[item] += suite_statistics[item]

        testsuite.statistics = product_statistics
        suite_data = testsuite.to_dict()
        suite_data_list.append(suite_data)

    logging.info('Convert XMind file(%s) to testsuite data list successfully!',
                 xmind_file)
    return suite_data_list


def get_xmind_testcase_list(xmind_file: str) -> List[Dict[str, Any]]:
    """Load the XMind file and get all testcases in it.

    Args:
        xmind_file: Path to the target XMind file.

    Returns:
        A list of testcase data dictionaries.
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testcases dict data...',
                 xmind_file)
    testsuites = get_xmind_testsuites(xmind_file)
    testcases = []

    for testsuite in testsuites:
        product = testsuite.name
        for suite in testsuite.sub_suites:
            for case in suite.testcase_list or []:
                case_data = case.to_dict()
                case_data['product'] = product
                case_data['suite'] = suite.name
                testcases.append(case_data)

    logging.info('Convert XMind file(%s) to testcases dict data successfully!',
                 xmind_file)
    return testcases


def _write_json_file(
    file_path: str,
    data: List[Dict[str, Any]]
) -> str:
    """Write data to a JSON file.

    Args:
        file_path: Path to the output JSON file.
        data: Data to write to the file.

    Returns:
        Path to the created JSON file.
    """
    if os.path.exists(file_path):
        os.remove(file_path)

    with open(file_path, 'w', encoding='utf8') as f:
        f.write(json.dumps(data, indent=4, separators=(',', ': '),
                          ensure_ascii=False))

    return file_path


def xmind_testsuite_to_json_file(xmind_file: str) -> str:
    """Convert XMind file to a testsuite JSON file.

    Args:
        xmind_file: Path to the XMind file.

    Returns:
        Path to the created testsuite JSON file.
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testsuites json file...',
                 xmind_file)
    testsuites = get_xmind_testsuite_list(xmind_file)
    testsuite_json_file = xmind_file[:-6] + '_testsuite.json'

    _write_json_file(testsuite_json_file, testsuites)
    logging.info('Convert XMind file(%s) to a testsuite json file(%s) '
                 'successfully!', xmind_file, testsuite_json_file)

    return testsuite_json_file


def xmind_testcase_to_json_file(xmind_file: str) -> str:
    """Convert XMind file to a testcase JSON file.

    Args:
        xmind_file: Path to the XMind file.

    Returns:
        Path to the created testcase JSON file.
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testcases json file...',
                 xmind_file)
    testcases = get_xmind_testcase_list(xmind_file)
    testcase_json_file = xmind_file[:-6] + '.json'

    _write_json_file(testcase_json_file, testcases)
    logging.info('Convert XMind file(%s) to a testcase json file(%s) '
                 'successfully!', xmind_file, testcase_json_file)

    return testcase_json_file
