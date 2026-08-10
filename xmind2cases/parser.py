#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parser for converting XMind content to test suite structures."""

import logging
import re
from typing import Any, Dict, Generator, List, Optional

from xmind2cases.metadata import TestCase, TestStep, TestSuite

config: Dict[str, Any] = {
    "sep": " ",
    "valid_sep": "&>+/-",
    "precondition_sep": "\n----\n",
    "summary_sep": "\n----\n",
    "ignore_char": "#!！",
}

_REQUIREMENT_RE = re.compile(r"\(#\d+\)")


def gen_requirements(labels: Optional[List[str]]) -> str:
    """Extract the first ``(#xxxxx)`` requirement tag from a topic's labels.

    Labels on the L1 node encode the related requirement, e.g. ``(#15889)``.
    Returns ``""`` when no label carries a parenthesized requirement ID.
    """
    if isinstance(labels, str):
        labels = [labels]
    for label in labels or []:
        if not isinstance(label, str):
            continue
        match = _REQUIREMENT_RE.search(label)
        if match:
            return match.group(0)
    return ""


def xmind_to_testsuites(xmind_content_dict: List[Dict[str, Any]]) -> List[TestSuite]:
    """Convert XMind file content to TestSuite list.

    Args:
        xmind_content_dict: XMind file content as a dictionary.

    Returns:
        List of TestSuite objects parsed from the XMind content.
    """
    suites = []

    for sheet in xmind_content_dict:
        logging.debug("start to parse a sheet: %s", sheet["title"])
        root_topic = sheet["topic"]
        sub_topics = root_topic.get("topics", [])

        if sub_topics:
            root_topic["topics"] = filter_empty_or_ignore_topic(sub_topics)
        else:
            logging.warning(
                "This is a blank sheet(%s), should have at least "
                "1 sub topic(test suite)",
                sheet["title"],
            )
            continue
        suite = sheet_to_suite(root_topic)
        logging.debug("sheet(%s) parsing complete: %s", sheet["title"], suite.to_dict())
        suites.append(suite)

    return suites


def filter_empty_or_ignore_topic(topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter blank or topics starting with ignore characters.

    Args:
        topics: List of topic dictionaries to filter.

    Returns:
        Filtered list of topics.
    """
    result = [
        topic
        for topic in topics
        if not (
            topic["title"] is None
            or topic["title"].strip() == ""
            or topic["title"][0] in config["ignore_char"]
        )
    ]

    for topic in result:
        sub_topics = topic.get("topics", [])
        topic["topics"] = filter_empty_or_ignore_topic(sub_topics)

    return result


def filter_empty_or_ignore_element(values: List[Any]) -> List[str]:
    """Filter all empty or ignored XMind elements.

    Filters notes, comments, and labels elements that are empty or start
    with ignore characters.

    Args:
        values: List of values to filter.

    Returns:
        Filtered list of non-empty string values.
    """
    result = []
    for value in values:
        if (
            isinstance(value, str)
            and value.strip() != ""
            and value[0] not in config["ignore_char"]
        ):
            result.append(value.strip())
    return result


def sheet_to_suite(root_topic: Dict[str, Any]) -> TestSuite:
    """Convert an XMind sheet to a TestSuite instance.

    Args:
        root_topic: Root topic dictionary from XMind sheet.

    Returns:
        TestSuite instance created from the root topic.
    """
    suite = TestSuite()
    root_title = root_topic["title"]
    separator = root_title[-1]

    if separator in config["valid_sep"]:
        logging.debug(
            "find a valid separator for connecting testcase title: %s", separator
        )
        config["sep"] = separator
        root_title = root_title[:-1]
    else:
        config["sep"] = " "

    suite.name = root_title
    suite.details = root_topic["note"]
    suite.sub_suites = []

    for suite_dict in root_topic["topics"]:
        suite.sub_suites.append(parse_testsuite(suite_dict))

    return suite


def parse_testsuite(suite_dict: Dict[str, Any]) -> TestSuite:
    """Parse a test suite from a dictionary.

    Args:
        suite_dict: Dictionary containing test suite data.

    Returns:
        TestSuite instance parsed from the dictionary.
    """
    testsuite = TestSuite()
    testsuite.name = suite_dict["title"]
    testsuite.details = suite_dict["note"]
    testsuite.testcase_list = []
    requirements = gen_requirements(suite_dict.get("labels"))
    logging.debug("start to parse a testsuite: %s", testsuite.name)

    for cases_dict in suite_dict.get("topics", []):
        for case in recurse_parse_testcase(cases_dict):
            case.requirements = requirements
            testsuite.testcase_list.append(case)

    logging.debug(
        "testsuite(%s) parsing complete: %s", testsuite.name, testsuite.to_dict()
    )
    return testsuite


def recurse_parse_testcase(
    case_dict: Dict[str, Any], parent: Optional[List[Dict[str, Any]]] = None
) -> Generator[TestCase, None, None]:
    """Recursively parse test cases from a topic dictionary.

    Args:
        case_dict: Dictionary containing test case data.
        parent: Optional list of parent topic dictionaries.

    Yields:
        TestCase instances parsed from the topic structure.
    """
    if is_testcase_topic(case_dict):
        case = parse_a_testcase(case_dict, parent)
        yield case
    else:
        if not parent:
            parent = []

        parent.append(case_dict)

        for child_dict in case_dict.get("topics", []):
            for case in recurse_parse_testcase(child_dict, parent):
                yield case

        parent.pop()


def is_testcase_topic(case_dict: Dict[str, Any]) -> bool:
    """Check if a topic represents a test case.

    A topic with a priority marker, or no subtopic, indicates that it is
    a testcase.

    Args:
        case_dict: Dictionary containing topic data.

    Returns:
        True if the topic represents a test case, False otherwise.
    """
    priority = get_priority(case_dict)
    if priority:
        return True

    children = case_dict.get("topics", [])
    if children:
        return False

    return True


def parse_a_testcase(
    case_dict: Dict[str, Any], parent: Optional[List[Dict[str, Any]]]
) -> TestCase:
    """Parse a single test case from a dictionary.

    Args:
        case_dict: Dictionary containing test case data.
        parent: Optional list of parent topic dictionaries.

    Returns:
        TestCase instance parsed from the dictionary.
    """
    testcase = TestCase()
    topics = parent + [case_dict] if parent else [case_dict]

    testcase.name = gen_testcase_title(topics)

    preconditions = gen_testcase_preconditions(topics)
    testcase.preconditions = preconditions if preconditions else "无"

    summary = gen_testcase_summary(topics)
    testcase.summary = summary if summary else testcase.name
    testcase.execution_type = get_execution_type(topics)
    testcase.importance = get_priority(case_dict) or 2

    step_dict_list = case_dict.get("topics", [])
    if step_dict_list:
        testcase.steps = parse_test_steps(step_dict_list)

    # The result of the testcase takes precedence over the result of
    # the teststep
    testcase.result = get_test_result(case_dict["markers"])

    if testcase.result == 0 and testcase.steps:
        for step in testcase.steps:
            if step.result == 2:
                testcase.result = 2
                break
            if step.result == 3:
                testcase.result = 3
                break

            testcase.result = step.result

    logging.debug("finds a testcase: %s", testcase.to_dict())
    return testcase


def get_execution_type(topics: List[Dict[str, Any]]) -> int:
    """Get execution type from topic labels.

    Args:
        topics: List of topic dictionaries.

    Returns:
        Execution type: 1 for manual, 2 for automated.
    """
    labels = [topic.get("label", "") for topic in topics]
    labels = filter_empty_or_ignore_element(labels)
    exe_type = 1
    for item in labels[::-1]:
        if item.lower() in ["自动", "auto", "automate", "automation"]:
            exe_type = 2
            break
        if item.lower() in ["手动", "手工", "manual"]:
            exe_type = 1
            break
    return exe_type


def get_priority(case_dict: Dict[str, Any]) -> Optional[int]:
    """Get the topic's priority (equivalent to testcase importance).

    Args:
        case_dict: Dictionary containing topic data with markers.

    Returns:
        Priority value (1-3) if found, None otherwise.
    """
    if isinstance(case_dict["markers"], list):
        for marker in case_dict["markers"]:
            if marker.startswith("priority"):
                return int(marker[-1])
    return None


def _extract_topic_field(topics: List[Dict[str, Any]], field: str) -> List[str]:
    """Extract a field from topics and filter empty/ignored values.

    Args:
        topics: List of topic dictionaries.
        field: Field name to extract from each topic.

    Returns:
        List of non-empty field values.
    """
    values = [topic.get(field, "") for topic in topics]
    return filter_empty_or_ignore_element(values)


def gen_testcase_title(topics: List[Dict[str, Any]]) -> str:
    """Link all topic titles as testcase title.

    Args:
        topics: List of topic dictionaries.

    Returns:
        Combined testcase title string.
    """
    titles = _extract_topic_field(topics, "title")

    # When separator is not blank, add space around separator,
    # e.g. '/' will be changed to ' / '
    separator = config["sep"]
    if separator != " ":
        separator = f" {separator} "

    return separator.join(titles)


def gen_testcase_preconditions(topics: List[Dict[str, Any]]) -> str:
    """Generate testcase preconditions from topic notes.

    Args:
        topics: List of topic dictionaries.

    Returns:
        Combined preconditions string.
    """
    notes = _extract_topic_field(topics, "note")
    return config["precondition_sep"].join(notes)


def gen_testcase_summary(topics: List[Dict[str, Any]]) -> str:
    """Generate testcase summary from topic comments.

    Args:
        topics: List of topic dictionaries.

    Returns:
        Combined summary string.
    """
    comments = _extract_topic_field(topics, "comment")
    return config["summary_sep"].join(comments)


def parse_test_steps(step_dict_list: List[Dict[str, Any]]) -> List[TestStep]:
    """Parse test steps from a list of step dictionaries.

    Args:
        step_dict_list: List of step dictionaries.

    Returns:
        List of TestStep instances.
    """
    steps = []

    for step_num, step_dict in enumerate(step_dict_list, 1):
        test_step = parse_a_test_step(step_dict)
        test_step.step_number = step_num
        steps.append(test_step)

    return steps


def parse_a_test_step(step_dict: Dict[str, Any]) -> TestStep:
    """Parse a single test step from a dictionary.

    Args:
        step_dict: Dictionary containing test step data.

    Returns:
        TestStep instance parsed from the dictionary.
    """
    test_step = TestStep()
    test_step.actions = step_dict["title"]

    expected_topics = step_dict.get("topics", [])
    if expected_topics:  # Have expected result
        expected_topic = expected_topics[0]
        # One test step action, one test expected result
        test_step.expectedresults = expected_topic["title"]
        markers = expected_topic["markers"]
        test_step.result = get_test_result(markers)
    else:  # Only have test step
        markers = step_dict["markers"]
        test_step.result = get_test_result(markers)

    logging.debug("finds a teststep: %s", test_step.to_dict())
    return test_step


def get_test_result(markers: Any) -> int:
    """Get test result from markers.

    Test result values:
    - 0: non-execution
    - 1: pass
    - 2: failed
    - 3: blocked
    - 4: skipped

    Args:
        markers: Markers from XMind topic (list or other type).

    Returns:
        Test result value (0-4).
    """
    if isinstance(markers, list):
        if "symbol-right" in markers or "c_simbol-right" in markers:
            return 1
        elif "symbol-wrong" in markers or "c_simbol-wrong" in markers:
            return 2
        elif "symbol-pause" in markers or "c_simbol-pause" in markers:
            return 3
        elif "symbol-minus" in markers or "c_simbol-minus" in markers:
            return 4

    return 0
