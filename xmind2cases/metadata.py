#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Metadata classes for test suites, test cases, and test steps."""

from typing import Dict, List, Optional, Any


class TestSuite:
    """Represents a test suite containing test cases and sub-suites.

    Attributes:
        name: Test suite name.
        details: Test suite detail information.
        testcase_list: List of test cases in this suite.
        sub_suites: List of sub test suites.
        statistics: Test suite statistics info with keys:
            'case_num', 'non_execution', 'pass', 'failed', 'blocked', 'skipped'.
    """

    def __init__(
        self,
        name: str = "",
        details: str = "",
        testcase_list: Optional[List["TestCase"]] = None,
        sub_suites: Optional[List["TestSuite"]] = None,
        statistics: Optional[Dict[str, int]] = None,
    ) -> None:
        """Initialize a TestSuite instance.

        Args:
            name: Test suite name.
            details: Test suite detail information.
            testcase_list: Test case list.
            sub_suites: Sub test suite list.
            statistics: Test suite statistics info with keys:
                'case_num', 'non_execution', 'pass', 'failed', 'blocked',
                'skipped'.
        """
        self.name = name
        self.details = details
        self.testcase_list = testcase_list
        self.sub_suites = sub_suites
        self.statistics = statistics

    def to_dict(self) -> Dict[str, Any]:
        """Convert the test suite to a dictionary.

        Returns:
            Dictionary representation of the test suite.
        """
        data: Dict[str, Any] = {
            "name": self.name,
            "details": self.details,
            "testcase_list": [],
            "sub_suites": [],
        }

        if self.sub_suites:
            for suite in self.sub_suites:
                data["sub_suites"].append(suite.to_dict())

        if self.testcase_list:
            for case in self.testcase_list:
                data["testcase_list"].append(case.to_dict())

        if self.statistics:
            data["statistics"] = self.statistics

        return data


class TestCase:
    """Represents a test case with steps and metadata.

    Attributes:
        name: Test case name.
        version: Test case version information.
        summary: Test case summary information.
        preconditions: Test case preconditions.
        execution_type: Execution type (1=manual, 2=automated).
        importance: Importance level (1=high, 2=middle, 3=low).
        estimated_exec_duration: Estimated execution duration.
        status: Test case status (1=draft, 2=ready to review,
            3=review in progress, 4=rework, 5=obsolete, 6=future, 7=final).
        result: Test result (0=non-execution, 1=pass, 2=failed,
            3=blocked, 4=skipped).
        requirements: Related requirement tag, e.g. ``(#15889)``.
        steps: List of test steps.
    """

    def __init__(
        self,
        name: str = "",
        version: int = 1,
        summary: str = "",
        preconditions: str = "",
        execution_type: int = 1,
        importance: int = 2,
        estimated_exec_duration: int = 3,
        status: int = 7,
        result: int = 0,
        steps: Optional[List["TestStep"]] = None,
        requirements: str = "",
    ) -> None:
        """Initialize a TestCase instance.

        Args:
            name: Test case name.
            version: Test case version information.
            summary: Test case summary information.
            preconditions: Test case preconditions.
            execution_type: Manual (1) or automated (2).
            importance: High (1), middle (2), or low (3).
            estimated_exec_duration: Estimated execution duration.
            status: Draft (1), ready to review (2), review in progress (3),
                rework (4), obsolete (5), future (6), final (7).
            result: Non-execution (0), pass (1), failed (2), blocked (3),
                skipped (4).
            steps: Test case step list.
        """
        self.name = name
        self.version = version
        self.summary = summary
        self.preconditions = preconditions
        self.execution_type = execution_type
        self.importance = importance
        self.estimated_exec_duration = estimated_exec_duration
        self.status = status
        self.result = result
        self.requirements = requirements
        self.steps = steps

    def to_dict(self) -> Dict[str, Any]:
        """Convert the test case to a dictionary.

        Returns:
            Dictionary representation of the test case.
        """
        data: Dict[str, Any] = {
            "name": self.name,
            "version": self.version,
            "summary": self.summary,
            "preconditions": self.preconditions,
            "execution_type": self.execution_type,
            "importance": self.importance,
            "estimated_exec_duration": self.estimated_exec_duration,
            "status": self.status,
            "result": self.result,
            "requirements": self.requirements,
            "steps": [],
        }

        if self.steps:
            for step in self.steps:
                data["steps"].append(step.to_dict())

        return data


class TestStep:
    """Represents a single test step within a test case.

    Attributes:
        step_number: Test step number.
        actions: Test step actions.
        expectedresults: Test step expected results.
        execution_type: Test step execution type (1=manual, 2=automated).
        result: Test result (0=non-execution, 1=pass, 2=failed,
            3=blocked, 4=skipped).
    """

    def __init__(
        self,
        step_number: int = 1,
        actions: str = "",
        expectedresults: str = "",
        execution_type: int = 1,
        result: int = 0,
    ) -> None:
        """Initialize a TestStep instance.

        Args:
            step_number: Test step number.
            actions: Test step actions.
            expectedresults: Test step expected results.
            execution_type: Test step execution type (1=manual, 2=automated).
            result: Non-execution (0), pass (1), failed (2), blocked (3),
                skipped (4).
        """
        self.step_number = step_number
        self.actions = actions
        self.expectedresults = expectedresults
        self.execution_type = execution_type
        self.result = result

    def to_dict(self) -> Dict[str, Any]:
        """Convert the test step to a dictionary.

        Returns:
            Dictionary representation of the test step.
        """
        return {
            "step_number": self.step_number,
            "actions": self.actions,
            "expectedresults": self.expectedresults,
            "execution_type": self.execution_type,
            "result": self.result,
        }
