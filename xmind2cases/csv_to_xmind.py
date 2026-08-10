#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert Zentao CSV file to XMind testcase file.

Parses a CSV file exported from Zentao (禅道) and generates an XMind file
that the xmind2cases pipeline can work with.

The output XMind uses the modern JSON-based format (``content.json`` inside
a ZIP archive), compatible with XMind 2020+ / XMind Zen.
"""

import csv
import json
import logging
import os
import re
import uuid
import zipfile
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CSV parsing helpers
# ---------------------------------------------------------------------------

_RE_STEP_SPLIT = re.compile(r"(?:^|\n)(?=\d+\.\s)")

_PRIORITY_MAP = {
    "1": "priority-1",
    "2": "priority-2",
    "3": "priority-3",
    "4": "priority-4",
}


def _parse_steps(step_text: str) -> List[str]:
    """Split a ZenTao ``步骤`` column into individual step strings.

    Steps are separated by lines starting with ``N. `` (N = digit sequence).
    Returns an empty list when the field is empty / ``/`` / ``无``.
    """
    text = (step_text or "").strip()
    if not text or text in ("/", "无"):
        return []
    parts = _RE_STEP_SPLIT.split(text)
    result = [p.strip() for p in parts if p and p.strip()]
    cleaned = []
    for part in result:
        part = re.sub(r"^\d+\.\s*", "", part, count=1).strip()
        if part:
            cleaned.append(part)
    return cleaned


def _parse_expected(expected_text: str) -> List[str]:
    """Split a ZenTao ``预期`` column into individual expected-result strings."""
    text = (expected_text or "").strip()
    if not text or text in ("/", "无"):
        return []
    parts = _RE_STEP_SPLIT.split(text)
    result: List[str] = []
    for p in parts:
        p = p.strip()
        if p:
            p = re.sub(r"^\d+\.\s*", "", p, count=1).strip()
            result.append(p)
    return result


def _module_path_parts(module_path: str) -> List[str]:
    """Split a ZenTao ``所属模块`` path into non-empty segments.

    Example::

        "/版本迭代测试用例/v6.4.11/模块(#10629)"
        → ["版本迭代测试用例", "v6.4.11", "模块(#10629)"]
    """
    return [seg for seg in module_path.split("/") if seg.strip()]


# ---------------------------------------------------------------------------
# XMind JSON generation  (content.json — XMind Zen format)
# ---------------------------------------------------------------------------


def _new_id() -> str:
    """Generate a short unique ID suitable for XMind topics."""
    return uuid.uuid4().hex[:24]


def _make_topic(title: str, **kwargs: Any) -> Dict[str, Any]:
    """Build a topic dict for the XMind ``content.json`` structure."""
    topic: Dict[str, Any] = {
        "id": _new_id(),
        "title": title,
    }
    if kwargs.get("structure_class"):
        topic["structureClass"] = kwargs.pop("structure_class")
    topic.update(kwargs)
    return topic


def _ensure_child_topic(parent: Dict, title: str) -> Dict:
    """Find or create a child topic with *title* under *parent*.

    Used to share module-path topics across CSV rows.
    """
    children = parent.setdefault("children", {})
    attached = children.setdefault("attached", [])
    for child in attached:
        if child.get("title") == title:
            return child
    new = _make_topic(title)
    attached.append(new)
    return new


def _module_leaf_name(module_path: str) -> str:
    """Return the last (most specific) segment of a ``所属模块`` path.

    ZenTao prefixes the real module with iteration scaffolding such as
    ``/版本迭代测试用例/v6.4.11/``; only the trailing segment is the actual
    module, so the prefix is dropped::

        "/版本迭代测试用例/v6.4.11/数据资产适配lindorm(#10629)"
        → "数据资产适配lindorm(#10629)"
    """
    parts = _module_path_parts(module_path)
    return parts[-1] if parts else ""


def _module_node(root_topic: Dict, module_path: str) -> Dict:
    """Find-or-create the module node (last path segment) under *root_topic*.

    Returns *root_topic* itself when the path is empty.
    """
    name = _module_leaf_name(module_path)
    if not name:
        return root_topic
    return _ensure_child_topic(root_topic, name)


def _split_title(title: str, delimiters: Optional[List[str]]) -> List[str]:
    """Split a testcase title into hierarchy segments by *delimiters*.

    Any selected delimiter acts as a cut point (they are equivalent). The
    last returned segment is the actual testcase; earlier segments are shared
    grouping nodes. Empty/whitespace segments are dropped.

    ``delimiters=None`` defaults to splitting on a single space; an empty list
    disables splitting (the whole title becomes one segment).
    """
    text = (title or "").strip()
    if not text:
        return []
    if delimiters is None:
        delimiters = [" "]
    seps = [d for d in delimiters if d]
    if not seps:
        return [text]
    pattern = "|".join(re.escape(d) for d in seps)
    parts = re.split(pattern, text)
    return [p.strip() for p in parts if p.strip()]


def _add_testcase_topic(
    module_topic: Dict,
    row: Dict[str, str],
    delimiters: Optional[List[str]] = None,
) -> None:
    """Append a testcase topic from one CSV row.

    The ``用例标题`` is split by *delimiters* into hierarchy segments: the
    leading segments become shared grouping topics (find-or-create, merged
    across rows) and the final segment becomes the testcase leaf that carries
    the markers / notes / steps.
    """
    segments = _split_title(row.get("用例标题", ""), delimiters)
    if not segments:
        return

    # Walk grouping segments, sharing nodes across rows; the last segment is
    # the testcase itself and is always appended fresh (never merged).
    parent = module_topic
    for seg in segments[:-1]:
        parent = _ensure_child_topic(parent, seg)
    parent_topic = parent
    title = segments[-1]

    topic: Dict[str, Any] = _make_topic(title)

    # --- precondition → note ---
    precondition = (row.get("前置条件") or "").strip()
    if precondition and precondition not in ("无", "/", ""):
        topic["notes"] = {
            "plain": {"content": precondition},
        }

    # --- priority → marker ---
    priority_raw = (row.get("优先级") or "").strip()
    marker_id = _PRIORITY_MAP.get(priority_raw)
    if marker_id:
        topic["markers"] = [{"markerId": marker_id}]

    # --- execution type → label ---
    case_type = (row.get("用例类型") or "").strip()
    if case_type == "接口测试":
        topic["labels"] = ["auto"]

    # --- steps & expected results ---
    steps = _parse_steps(row.get("步骤", ""))
    expected = _parse_expected(row.get("预期", ""))

    step_topics: List[Dict] = []
    max_len = max(len(steps), len(expected))
    for idx in range(max_len):
        step_text = steps[idx] if idx < len(steps) else ""
        exp_text = expected[idx] if idx < len(expected) else ""

        if not step_text and not exp_text:
            continue

        step_topic = _make_topic(step_text or "(空)")
        if exp_text:
            exp_topic = _make_topic(exp_text)
            step_topic.setdefault("children", {})["attached"] = [exp_topic]
            # Fold so the expected-result child is hidden until expanded.
            step_topic["branch"] = "folded"

        step_topics.append(step_topic)

    if step_topics:
        topic.setdefault("children", {})["attached"] = step_topics
        # Fold the testcase node: with hundreds of cases, rendering every
        # step/expected node at once makes XMind extremely sluggish. Folding
        # keeps the module tree + case titles visible, details collapsed —
        # matching how cases.xmind (XMind-authored) ships.
        topic["branch"] = "folded"

    parent_topic.setdefault("children", {})
    parent_topic["children"].setdefault("attached", [])
    parent_topic["children"]["attached"].append(topic)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def zentao_csv_to_xmind_file(
    csv_path: str,
    output_path: Optional[str] = None,
    delimiters: Optional[List[str]] = None,
) -> str:
    """Convert a ZenTao CSV testcase export to an XMind file.

    Generates a modern JSON-format XMind file (``content.json`` inside ZIP),
    compatible with XMind 2020+ / XMind Zen.

    Args:
        csv_path: Path to the input ZenTao CSV file.
        output_path: Optional output path for the generated ``.xmind`` file.
            If omitted, the output is placed next to the CSV with a ``.xmind``
            extension.
        delimiters: Characters used to split each ``用例标题`` into nested
            topics (any one acts as a cut point). ``None`` defaults to a single
            space; an empty list keeps titles flat.

    Returns:
        Absolute path to the generated XMind file.

    Raises:
        FileNotFoundError: *csv_path* does not exist.
        ValueError: The CSV is unreadable or missing required columns.
    """
    csv_path = _resolve_path(csv_path)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    if not csv_path.lower().endswith(".csv"):
        raise ValueError(f"Expected a .csv file, got: {csv_path}")

    # ---- parse CSV ----
    required_columns = {"所属产品", "所属模块", "用例标题"}

    with open(csv_path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise ValueError(f"CSV file is empty or has no header: {csv_path}")

        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"CSV missing required columns: {', '.join(sorted(missing))}"
            )

        rows = list(reader)

    if not rows:
        logger.warning("CSV file contains no data rows: %s", csv_path)

    # ---- group by product (each product → one sheet) ----
    products: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        product = (row.get("所属产品") or "").strip()
        if not product:
            continue
        products.setdefault(product, []).append(row)

    # ---- build content.json structure ----
    sheets: List[Dict] = []
    for product_name, product_rows in products.items():
        root_topic = _make_topic(
            product_name,
            structure_class="org.xmind.ui.logic.right",
        )

        for row in product_rows:
            module_topic = _module_node(root_topic, row.get("所属模块", ""))
            _add_testcase_topic(module_topic, row, delimiters)

        sheet: Dict[str, Any] = {
            "id": _new_id(),
            "class": "sheet",
            "title": product_name,
            "rootTopic": root_topic,
        }
        sheets.append(sheet)

    # ---- resolve output path ----
    if output_path is None:
        output_path = csv_path[: -len(".csv")] + ".xmind"
        if os.path.exists(output_path):
            base, ext = os.path.splitext(output_path)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            output_path = f"{base}_{counter}{ext}"

    output_path = os.path.abspath(output_path)

    # ---- write XMind (ZIP with content.json) ----
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("content.json", json.dumps(sheets, ensure_ascii=False))
        zf.writestr(
            "metadata.json",
            json.dumps(
                {
                    "creator": {"name": "xmind2cases", "version": "2.0"},
                    "dataStructureVersion": "3",
                }
            ),
        )
        zf.writestr(
            "manifest.json",
            json.dumps(
                {
                    "file-entries": {
                        "content.json": {},
                        "metadata.json": {},
                    },
                }
            ),
        )

    logger.info(
        "Converted CSV(%s) to XMind(%s) successfully — %d product(s), %d case(s)",
        csv_path,
        output_path,
        len(products),
        len(rows),
    )
    return output_path


def _resolve_path(path: str) -> str:
    """Expand user home and convert to absolute path."""
    return os.path.abspath(os.path.expanduser(path))


def csv_to_testcase_dicts(csv_path: str) -> List[Dict[str, Any]]:
    """Parse a ZenTao CSV into a list of testcase dicts.

    The returned dicts match the schema produced by
    ``xmind2cases.utils.get_xmind_testcase_list`` so they can be used
    interchangeably in the web preview / export APIs.

    Returns:
        List of testcase dicts with keys ``name``, ``suite``, ``product``,
        ``preconditions``, ``steps``, ``importance``, ``execution_type``.
    """
    csv_path = _resolve_path(csv_path)

    with open(csv_path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    result: List[Dict[str, Any]] = []
    for row in rows:
        product = (row.get("所属产品") or "").strip()
        module = (row.get("所属模块") or "").strip()
        title = (row.get("用例标题") or "").strip()
        if not title:
            continue

        preconditions = (row.get("前置条件") or "").strip()
        if preconditions in ("无", "/", ""):
            preconditions = ""

        steps_raw = _parse_steps(row.get("步骤", ""))
        expected_raw = _parse_expected(row.get("预期", ""))
        steps: List[Dict[str, Any]] = []
        max_len = max(len(steps_raw), len(expected_raw))
        for idx in range(max_len):
            step_text = steps_raw[idx] if idx < len(steps_raw) else ""
            exp_text = expected_raw[idx] if idx < len(expected_raw) else ""
            step: Dict[str, Any] = {
                "step_number": idx + 1,
                "actions": step_text or "(空)",
                "expectedresults": exp_text,
                "execution_type": 1,
                "result": 0,
            }
            steps.append(step)

        priority_raw = (row.get("优先级") or "").strip()
        try:
            importance = int(priority_raw) if priority_raw else 2
        except ValueError:
            importance = 2
        if importance < 1 or importance > 4:
            importance = 2

        case_type = (row.get("用例类型") or "").strip()
        execution_type = 2 if case_type == "接口测试" else 1

        result.append(
            {
                "name": title,
                "suite": module,
                "product": product,
                "preconditions": preconditions or "无",
                "steps": steps,
                "importance": importance,
                "execution_type": execution_type,
                "requirements": (row.get("相关需求") or "").strip(),
            }
        )

    return result
