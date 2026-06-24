#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Flask web application for XMind to testcase conversion."""

import csv
import io
import json
import logging
import os
import re
from os.path import exists, join
from typing import Any, Generator, List, Optional, Tuple
from urllib.parse import quote
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

import arrow
from flask import (
    Flask,
    Response,
    abort,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from webtool.models import AppSetting, ColumnTemplate, DEFAULT_COLUMNS, Record, db
from xmind2cases.testlink import xmind_to_testlink_xml_file
from xmind2cases.utils import get_xmind_testcase_list, get_xmind_testsuites
from xmind2cases.zentao import xmind_to_zentao_csv_file
from xmind2cases.csv_to_xmind import zentao_csv_to_xmind_file

here = os.path.abspath(os.path.dirname(__file__))
log_file = os.path.join(here, "running.log")

# Log handler configuration
formatter = logging.Formatter(
    "%(asctime)s  %(name)s  %(levelname)s  [%(module)s - %(funcName)s]: %(message)s"
)
file_handler = logging.FileHandler(log_file, encoding="UTF-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

# XMind to testcase logger
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.DEBUG)

# Flask and werkzeug logger
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.addHandler(file_handler)
werkzeug_logger.addHandler(stream_handler)
werkzeug_logger.setLevel(logging.DEBUG)

# Global variables
UPLOAD_FOLDER = os.path.join(here, "uploads")
ALLOWED_EXTENSIONS = ["xmind", "csv"]
DEBUG = True
DATABASE = os.path.join(here, "data.db3")
HOST = "0.0.0.0"
PORT = int(os.environ.get("FLASK_PORT", "5002"))

# Flask app
app = Flask(__name__)
app.config.from_object(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def init() -> None:
    """Initialize the application: create directories and database."""
    app.logger.info("Start initializing the database...")
    if not exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)

    with app.app_context():
        db.create_all()

        # 迁移：为 column_preferences 添加 header_color 列（若不存在）
        try:
            from sqlalchemy import text

            result = db.session.execute(text("PRAGMA table_info(column_preferences)"))
            columns = [row[1] for row in result]
            if "header_color" not in columns:
                db.session.execute(
                    text(
                        "ALTER TABLE column_preferences ADD COLUMN header_color VARCHAR(20) DEFAULT '#fef2f2'"
                    )
                )
                db.session.commit()
            # 将非浅红色的 header_color 修正为 #fef2f2（浅红色）
            non_red = (
                "#f8fafc",
                "#e0e0e0",
                "#e2e8f0",
                "#f1f5f9",
                "#3b82f6",
                "#4f46e5",
                "#6366f1",
            )
            for color in non_red:
                db.session.execute(
                    text(
                        "UPDATE column_preferences SET header_color = '#fef2f2' WHERE header_color = :c"
                    ),
                    {"c": color},
                )
            db.session.execute(
                text(
                    "UPDATE column_preferences SET header_color = '#fef2f2' WHERE header_color IS NULL OR header_color = ''"
                )
            )
            db.session.commit()
        except Exception:
            db.session.rollback()

        # 迁移：last_export_preference_id -> last_export_template_id
        try:
            old_setting = AppSetting.query.get("last_export_preference_id")
            new_setting = AppSetting.query.get("last_export_template_id")
            if old_setting and old_setting.value and not new_setting:
                db.session.add(
                    AppSetting(key="last_export_template_id", value=old_setting.value)
                )
                db.session.commit()
        except Exception:
            db.session.rollback()

        # 插入默认模版（如果不存在）
        if ColumnTemplate.query.count() == 0:
            default_tpl = ColumnTemplate(
                name="默认",
                columns_json=json.dumps(DEFAULT_COLUMNS, ensure_ascii=False),
            )
            db.session.add(default_tpl)
            db.session.commit()

    app.logger.info(
        "Congratulations! the xmind2cases webtool database "
        "has initialized successfully!"
    )


def insert_record(xmind_name: str, note: str = "") -> None:
    """Insert a new record into the database.

    Args:
        xmind_name: Name of the XMind file.
        note: Optional note for the record.
    """
    now = str(arrow.now())
    record = Record(name=xmind_name, create_on=now, note=note)
    db.session.add(record)
    db.session.commit()


def _get_related_file_paths(filename: str) -> List[str]:
    """Get paths for related files (xmind, xml, csv).

    Args:
        filename: Base filename.

    Returns:
        List of file paths.
    """
    base_name = filename[:-6] if filename.endswith(".xmind") else filename
    upload_folder = app.config["UPLOAD_FOLDER"]
    return [
        join(upload_folder, filename),
        join(upload_folder, f"{base_name}.xml"),
        join(upload_folder, f"{base_name}.csv"),
    ]


def _delete_related_files(filename: str) -> None:
    """Delete related files (xmind, xml, csv) for a given filename.

    Args:
        filename: Base filename.
    """
    for file_path in _get_related_file_paths(filename):
        if exists(file_path):
            os.remove(file_path)


def delete_record(filename: str, record_id: int) -> None:
    """Delete a record and its related files.

    Args:
        filename: Name of the file to delete.
        record_id: Database record ID.
    """
    _delete_related_files(filename)
    record = Record.query.get(record_id)
    if record:
        record.is_deleted = 1
        db.session.commit()


def delete_records(keep: int = 20) -> None:
    """Clean up old files on server and mark records as deleted.

    Keeps the most recent 'keep' records and deletes the rest.

    Args:
        keep: Number of recent records to keep.
    """
    records = (
        Record.query.filter_by(is_deleted=0)
        .order_by(Record.id.desc())
        .offset(keep)
        .all()
    )
    for record in records:
        _delete_related_files(record.name)
        record.is_deleted = 1
    db.session.commit()


def _is_value_empty(val: Any) -> bool:
    """判断值是否为空（用于空值校验）"""
    if val is None:
        return True
    if isinstance(val, str):
        return (val or "").strip() == ""
    return False


def get_column_value(testcase: dict, column: dict, row_index: int) -> str:
    """根据列配置获取单元格值（row_index 为 0-based）"""
    col_id = column.get("id")
    is_custom = column.get("is_custom", False)
    default_value = column.get("default_value", "")

    if is_custom:
        values = column.get("values", {})
        return values.get(str(row_index), default_value)

    if col_id == "suite":
        return testcase.get("suite", "")
    if col_id == "name":
        return testcase.get("name", "")
    if col_id == "preconditions":
        return testcase.get("preconditions", "")
    if col_id == "steps":
        steps = testcase.get("steps", [])
        return "\n".join(
            [f"{i + 1}. {s.get('actions', '')}" for i, s in enumerate(steps)]
        )
    if col_id == "expectedresults":
        steps = testcase.get("steps", [])
        return "\n".join(
            [f"{i + 1}. {s.get('expectedresults', '')}" for i, s in enumerate(steps)]
        )
    if col_id == "importance":
        return str(testcase.get("importance", ""))
    if col_id == "execution_type":
        return default_value or str(testcase.get("execution_type", ""))
    if col_id == "stage":
        return default_value

    return default_value


def _format_cell_for_export(value: str, column: dict) -> str:
    """若列启用富文本换行处理，将换行符替换为 <br>"""
    if not value:
        return value
    if column.get("rich_text_break"):
        return value.replace("\n", "<br>")
    return value


def generate_csv_with_columns(testcases: list, columns: list) -> str:
    """根据列配置生成 CSV 内容（不含序号列）"""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    visible_columns = sorted(columns, key=lambda x: x.get("order", 0))
    header = [c.get("name", "") for c in visible_columns]
    writer.writerow(header)

    for row_index, tc in enumerate(testcases):
        row = [
            _format_cell_for_export(get_column_value(tc, c, row_index), c)
            for c in visible_columns
        ]
        writer.writerow(row)

    return output.getvalue()


def generate_xml_with_columns(testcases: list, columns: list) -> str:
    """根据列配置生成 TestLink XML 内容"""
    visible_columns = sorted(columns, key=lambda x: x.get("order", 0))
    root = Element("testcases")

    for row_index, tc in enumerate(testcases):
        testcase_el = SubElement(root, "testcase")
        testcase_el.set("name", tc.get("name", ""))

        summary = SubElement(testcase_el, "summary")
        summary.text = tc.get("name", "")

        preconditions = SubElement(testcase_el, "preconditions")
        preconditions.text = tc.get("preconditions", "")

        importance = SubElement(testcase_el, "importance")
        importance.text = str(tc.get("importance", 2))

        steps_el = SubElement(testcase_el, "steps")
        for step_idx, step in enumerate(tc.get("steps", []), 1):
            step_el = SubElement(steps_el, "step")
            step_number = SubElement(step_el, "step_number")
            step_number.text = str(step_idx)
            actions = SubElement(step_el, "actions")
            actions.text = step.get("actions", "")
            expected = SubElement(step_el, "expectedresults")
            expected.text = step.get("expectedresults", "")

        custom_columns = [c for c in visible_columns if c.get("is_custom")]
        if custom_columns:
            custom_fields_el = SubElement(testcase_el, "custom_fields")
            for col in custom_columns:
                cf_el = SubElement(custom_fields_el, "custom_field")
                name_el = SubElement(cf_el, "name")
                name_el.text = col.get("name", "")
                value_el = SubElement(cf_el, "value")
                value_el.text = _format_cell_for_export(
                    get_column_value(tc, col, row_index), col
                )

    rough_string = tostring(root, encoding="unicode")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def get_latest_record() -> Optional[Tuple[str, str, str, str, int]]:
    """Get the latest record from the database.

    Returns:
        Tuple of (short_name, name, create_on, note, record_id) or None.
    """
    record = Record.query.filter_by(is_deleted=0).order_by(Record.id.desc()).first()
    if record:
        short_name = (
            record.name[:120] + "..." if len(record.name) > 120 else record.name
        )
        create_on = arrow.get(record.create_on).humanize()
        return short_name, record.name, create_on, record.note or "", record.id
    return None


def get_records(
    limit: int = 8,
) -> Generator[Tuple[str, str, str, str, int], None, None]:
    """Get records from the database.

    Args:
        limit: Maximum number of records to retrieve.

    Yields:
        Tuples of (short_name, name, create_on, note, record_id).
    """
    records = (
        Record.query.filter_by(is_deleted=0)
        .order_by(Record.id.desc())
        .limit(limit)
        .all()
    )
    for record in records:
        short_name = (
            record.name[:120] + "..." if len(record.name) > 120 else record.name
        )
        create_on = arrow.get(record.create_on).humanize()
        yield short_name, record.name, create_on, record.note or "", record.id


def allowed_file(filename: str) -> bool:
    """Check if a filename has an allowed extension.

    Args:
        filename: Filename to check.

    Returns:
        True if the file extension is allowed, False otherwise.
    """
    return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS


def check_file_name(name: str) -> str:
    """Check and secure a filename.

    Args:
        name: Original filename.

    Returns:
        Secured filename with original extension.

    Raises:
        AssertionError: If unable to parse the filename.
    """
    secured = secure_filename(name)
    if not secured:
        # Only keep letters and digits from file name
        secured = re.sub(r"[^\w\d]+", "_", name)
        assert secured, f"Unable to parse file name: {name}!"

    # Preserve original extension
    _, ext = os.path.splitext(name)
    if ext.lower() in (".xmind", ".csv"):
        return secured if secured.endswith(ext) else secured + ext
    return secured + ".xmind"


def save_file(file: Any) -> Optional[str]:
    """Save an uploaded file to the upload folder.

    Args:
        file: Uploaded file object from Flask request.

    Returns:
        Filename if successful, None otherwise.
    """
    if file and allowed_file(file.filename):
        filename = file.filename
        upload_to = join(app.config["UPLOAD_FOLDER"], filename)

        if exists(upload_to):
            timestamp = arrow.now().strftime("%Y%m%d_%H%M%S")
            base, ext = os.path.splitext(filename)
            filename = f"{base}_{timestamp}{ext}"
            upload_to = join(app.config["UPLOAD_FOLDER"], filename)

        file.save(upload_to)
        insert_record(filename)
        g.is_success = True
        return filename

    elif file.filename == "":
        g.is_success = False
        g.error = "Please select a file!"

    else:
        g.is_success = False
        if not hasattr(g, "invalid_files"):
            g.invalid_files = []
        g.invalid_files.append(file.filename)

    return None


def verify_uploaded_files(files: List[Any]) -> None:
    """Verify uploaded files and set download flag if applicable.

    Args:
        files: List of uploaded file objects.
    """
    # Download the xml directly if only 1 file uploaded
    if len(files) == 1 and getattr(g, "is_success", False):
        latest = get_latest_record()
        if latest:
            g.download_xml = latest[1]

    if hasattr(g, "invalid_files") and g.invalid_files:
        g.error = f"Invalid file: {','.join(g.invalid_files)}"


@app.route("/", methods=["GET", "POST"])
def index(download_xml: Optional[str] = None) -> Any:
    """Main index route for file upload and listing.

    Args:
        download_xml: Optional XML filename for direct download.

    Returns:
        Rendered template or redirect response.
    """
    g.invalid_files = []
    g.error = None
    g.download_xml = download_xml
    g.filename = None

    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            return redirect(request.url)

        g.filename = save_file(file)
        verify_uploaded_files([file])
        delete_records()

    else:
        g.upload_form = True

    if g.filename:
        return redirect(url_for("preview_file", filename=g.filename))
    else:
        return render_template("index.html", records=list(get_records()))


@app.route("/uploads/<filename>")
def uploaded_file(filename: str) -> Any:
    """Serve uploaded files.

    Args:
        filename: Name of the file to serve.

    Returns:
        File response.
    """
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


def _download_converted_file(
    filename: str, converter_func: Any, file_extension: str
) -> Any:
    """Generic function to download converted files.

    Args:
        filename: Original XMind filename.
        converter_func: Function to convert XMind file.
        file_extension: Expected file extension (e.g., 'xml', 'csv').

    Returns:
        File download response or 404 error.
    """
    full_path = join(app.config["UPLOAD_FOLDER"], filename)

    if not exists(full_path):
        abort(404)

    converted_file = converter_func(full_path)
    if not converted_file:
        abort(404)

    output_filename = os.path.basename(converted_file)
    return send_from_directory(
        app.config["UPLOAD_FOLDER"], output_filename, as_attachment=True
    )


@app.route("/<filename>/to/xmind-from-csv")
def download_xmind_from_csv(filename: str) -> Any:
    """Convert an uploaded CSV file to XMind and download.

    Query params:
        sep: Repeatable. Each value is a delimiter used to split every
            ``用例标题`` into nested topics (any one acts as a cut point).
            Defaults to a single space when absent.
        flat: ``1`` keeps titles unsplit (one topic per case).

    Args:
        filename: Name of the CSV file.

    Returns:
        XMind file download response or 404 error.
    """
    full_path = join(app.config["UPLOAD_FOLDER"], filename)
    if not exists(full_path):
        abort(404)

    if request.args.get("flat") == "1":
        delimiters: list = []
    else:
        seps = request.args.getlist("sep")
        delimiters = seps if seps else [" "]

    xmind_path = zentao_csv_to_xmind_file(full_path, delimiters=delimiters)
    output_filename = os.path.basename(xmind_path)
    return send_from_directory(
        os.path.dirname(xmind_path), output_filename, as_attachment=True
    )


@app.route("/<filename>/to/testlink")
def download_testlink_file(filename: str) -> Any:
    """Download TestLink XML file for an uploaded XMind file.

    Args:
        filename: Name of the XMind file.

    Returns:
        File download response or 404 error.
    """
    return _download_converted_file(filename, xmind_to_testlink_xml_file, "xml")


@app.route("/<filename>/to/zentao")
def download_zentao_file(filename: str) -> Any:
    """Download Zentao CSV file for an uploaded XMind file.

    Args:
        filename: Name of the XMind file.

    Returns:
        File download response or 404 error.
    """
    return _download_converted_file(filename, xmind_to_zentao_csv_file, "csv")


@app.route("/preview/<path:filename>")
def preview_file(filename: str) -> Any:
    """Preview testcases from an uploaded XMind or CSV file.

    Args:
        filename: Name of the file (XMind or CSV).

    Returns:
        Rendered preview template or 404 error.
    """
    full_path = join(app.config["UPLOAD_FOLDER"], filename)

    if not exists(full_path):
        abort(404)

    is_csv = filename.lower().endswith(".csv")
    if is_csv:
        from xmind2cases.csv_to_xmind import csv_to_testcase_dicts

        testcases = csv_to_testcase_dicts(full_path)
        total = len(testcases)
        suite_count = len({tc.get("product", "") for tc in testcases})
    else:
        testsuites = get_xmind_testsuites(full_path)
        suite_count = sum(len(suite.sub_suites or []) for suite in testsuites)
        testcases = get_xmind_testcase_list(full_path)
        total = len(testcases)

    return render_template(
        "preview.html",
        name=filename,
        suite=[],
        suite_count=suite_count,
        total=total,
        is_csv=is_csv,
    )


@app.route("/api/preview/<path:filename>/empty-cells", methods=["GET"])
def get_empty_cells(filename: str) -> Any:
    """全局检测空值，返回所有空值单元格列表"""
    full_path = join(app.config["UPLOAD_FOLDER"], filename)
    if not exists(full_path):
        abort(404)

    # CSV 预览不支持空值检测（有别于 XMind 解析后的字段）
    if filename.lower().endswith(".csv"):
        return jsonify({"success": True, "data": {"empty_cells": []}})

    template_id = request.args.get("template_id", type=int)
    if not template_id:
        return jsonify({"success": True, "data": {"empty_cells": []}})

    tpl = ColumnTemplate.query.get(template_id)
    columns = tpl.columns if tpl else DEFAULT_COLUMNS
    sorted_columns = sorted(columns, key=lambda x: x.get("order", 0))
    empty_check_cols = [c for c in sorted_columns if c.get("empty_check") is True]

    if not empty_check_cols:
        return jsonify({"success": True, "data": {"empty_cells": []}})

    testcases = get_xmind_testcase_list(full_path)
    empty_cells = []
    for row_index, tc in enumerate(testcases):
        for col in empty_check_cols:
            val = get_column_value(tc, col, row_index)
            if _is_value_empty(val):
                empty_cells.append(
                    {
                        "colId": col.get("id", ""),
                        "rowIndex": row_index,
                        "colName": col.get("name", col.get("id", "")),
                    }
                )

    return jsonify(
        {
            "success": True,
            "data": {"empty_cells": empty_cells},
        }
    )


@app.route("/api/preview/<path:filename>/cases", methods=["GET"])
def get_preview_cases(filename: str) -> Any:
    """分页获取预览用例数据（支持 XMind 和 CSV）"""
    full_path = join(app.config["UPLOAD_FOLDER"], filename)

    if not exists(full_path):
        abort(404)

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 10, type=int)

    if page_size not in (10, 20, 50, 100):
        page_size = 10
    page = max(1, page)

    if filename.lower().endswith(".csv"):
        from xmind2cases.csv_to_xmind import csv_to_testcase_dicts

        testcases = csv_to_testcase_dicts(full_path)
    else:
        testcases = get_xmind_testcase_list(full_path)

    total = len(testcases)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = testcases[start:end]

    return jsonify(
        {
            "success": True,
            "data": {
                "testcases": page_data,
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        }
    )


@app.route("/delete/<filename>/<int:record_id>")
def delete_file(filename: str, record_id: int) -> Any:
    """Delete a file and its record.

    Args:
        filename: Name of the file to delete.
        record_id: Database record ID.

    Returns:
        Redirect to index page or 404 error.
    """
    full_path = join(app.config["UPLOAD_FOLDER"], filename)
    if not exists(full_path):
        abort(404)

    delete_record(filename, record_id)
    return redirect("/")


# ==================== 模版管理 API ====================


@app.route("/api/templates", methods=["GET"])
def get_templates():
    """获取所有模版列表，以及上次导出使用的模版 ID"""
    templates = ColumnTemplate.query.order_by(ColumnTemplate.id).all()
    last_tpl = AppSetting.query.get("last_export_template_id")
    last_tpl_id = int(last_tpl.value) if last_tpl and last_tpl.value else None

    return jsonify(
        {
            "success": True,
            "data": {
                "templates": [t.to_dict() for t in templates],
                "last_template_id": last_tpl_id,
            },
        }
    )


@app.route("/api/templates/<int:template_id>", methods=["GET"])
def get_template(template_id):
    """获取单个模版详情"""
    tpl = ColumnTemplate.query.get(template_id)
    if not tpl:
        return jsonify({"success": False, "message": "模版不存在"}), 404
    return jsonify(
        {
            "success": True,
            "data": tpl.to_dict(),
        }
    )


def _next_unnamed_template_name(base: str = "未命名模版") -> str:
    """当 base 已存在时，返回 base(2)、base(3) 等下一个可用名称"""
    import re

    existing = {t.name for t in ColumnTemplate.query.all()}
    if base not in existing:
        return base
    pattern = re.compile(r"^" + re.escape(base) + r"\((\d+)\)$")
    nums = []
    for n in existing:
        m = pattern.match(n)
        if m:
            nums.append(int(m.group(1)))
    next_num = max(nums, default=1) + 1
    return f"{base}({next_num})"


@app.route("/api/templates", methods=["POST"])
def create_template():
    """新建模版"""
    data = request.get_json() or {}
    name = data.get("name", "未命名模版")
    columns = data.get("columns", DEFAULT_COLUMNS)

    if name == "未命名模版":
        name = _next_unnamed_template_name("未命名模版")
    if len(name) > 20:
        return jsonify({"success": False, "message": "模版名称最多20个字符"}), 400
    if ColumnTemplate.query.filter_by(name=name).first():
        return jsonify({"success": False, "message": "模版名称已存在"}), 400

    tpl = ColumnTemplate(
        name=name,
        columns_json=json.dumps(columns, ensure_ascii=False),
        header_color=data.get("header_color", "#fef2f2"),
    )
    db.session.add(tpl)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "data": {"id": tpl.id},
        }
    )


@app.route("/api/templates/<int:template_id>", methods=["PUT"])
def update_template(template_id):
    """更新模版"""
    tpl = ColumnTemplate.query.get(template_id)
    if not tpl:
        return jsonify({"success": False, "message": "模版不存在"}), 404

    data = request.get_json() or {}
    if "name" in data:
        new_name = (data["name"] or "").strip()
        if len(new_name) > 20:
            return jsonify({"success": False, "message": "模版名称最多20个字符"}), 400
        if (
            new_name
            and ColumnTemplate.query.filter(
                ColumnTemplate.name == new_name,
                ColumnTemplate.id != template_id,
            ).first()
        ):
            return jsonify({"success": False, "message": "模版名称已存在"}), 400
        tpl.name = new_name or tpl.name
    if "columns" in data:
        tpl.columns_json = json.dumps(data["columns"], ensure_ascii=False)
    if "header_color" in data:
        tpl.header_color = data["header_color"] or "#fef2f2"

    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "模版已更新",
        }
    )


@app.route("/api/templates/<int:template_id>", methods=["DELETE"])
def delete_template(template_id):
    """删除模版"""
    tpl = ColumnTemplate.query.get(template_id)
    if not tpl:
        return jsonify({"success": False, "message": "模版不存在"}), 404

    db.session.delete(tpl)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "模版已删除",
        }
    )


# ==================== 上传 API ====================


@app.route("/api/upload", methods=["POST"])
def api_upload() -> Any:
    """单文件上传，返回 JSON 文件名，供前端驱动后续转换流程。"""
    if "file" not in request.files:
        return jsonify({"success": False, "message": "未收到文件"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "请选择文件"}), 400
    filename = save_file(file)  # 已含保存 / 去重 / insert_record
    if not filename:
        return jsonify({"success": False, "message": "仅支持 .xmind 或 .csv 文件"}), 400
    delete_records()
    return jsonify({"success": True, "filename": filename})


# ==================== 导出 API ====================


def _save_last_export_template(template_id: int) -> None:
    """保存上次导出使用的模版 ID"""
    setting = AppSetting.query.get("last_export_template_id")
    if setting:
        setting.value = str(template_id)
    else:
        setting = AppSetting(key="last_export_template_id", value=str(template_id))
        db.session.add(setting)
    db.session.commit()


def _content_disposition_attachment(display_filename: str) -> str:
    """生成 Content-Disposition 头，支持中文等非 ASCII 文件名（RFC 5987）。"""
    try:
        display_filename.encode("ascii")
        return f'attachment; filename="{display_filename}"'
    except UnicodeEncodeError:
        encoded = quote(display_filename, safe="")
        ext = display_filename.rsplit(".", 1)[-1] if "." in display_filename else "bin"
        return f"attachment; filename=download.{ext}; filename*=UTF-8''{encoded}"


@app.route("/api/export/<path:filename>/csv", methods=["POST"])
def export_csv_with_template(filename: str):
    """按指定模版导出 CSV（不含序号列）"""
    full_path = join(app.config["UPLOAD_FOLDER"], filename)
    if not exists(full_path):
        abort(404)

    data = request.get_json() or {}
    template_id = data.get("template_id")

    if template_id:
        tpl = ColumnTemplate.query.get(template_id)
        columns = tpl.columns if tpl else DEFAULT_COLUMNS
        _save_last_export_template(template_id)
    else:
        columns = DEFAULT_COLUMNS

    testcases = get_xmind_testcase_list(full_path)
    csv_content = generate_csv_with_columns(testcases, columns)

    base_name = filename[:-6] if filename.endswith(".xmind") else filename
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": _content_disposition_attachment(f"{base_name}.csv")
        },
    )


@app.route("/api/export/<path:filename>/xml", methods=["POST"])
def export_xml_with_template(filename: str):
    """按指定模版导出 XML"""
    full_path = join(app.config["UPLOAD_FOLDER"], filename)
    if not exists(full_path):
        abort(404)

    data = request.get_json() or {}
    template_id = data.get("template_id")

    if template_id:
        tpl = ColumnTemplate.query.get(template_id)
        columns = tpl.columns if tpl else DEFAULT_COLUMNS
        _save_last_export_template(template_id)
    else:
        columns = DEFAULT_COLUMNS

    testcases = get_xmind_testcase_list(full_path)
    xml_content = generate_xml_with_columns(testcases, columns)

    base_name = filename[:-6] if filename.endswith(".xmind") else filename
    return Response(
        xml_content,
        mimetype="application/xml",
        headers={
            "Content-Disposition": _content_disposition_attachment(f"{base_name}.xml")
        },
    )


@app.errorhandler(Exception)
def app_error(e: Exception) -> str:
    """Handle application errors.

    Args:
        e: Exception that occurred.

    Returns:
        Error message as string.
    """
    return str(e)


def launch(host: str = HOST, debug: bool = True, port: int = PORT) -> None:
    """Launch the Flask web application.

    Args:
        host: Host to bind to.
        debug: Enable debug mode.
        port: Port to listen on.
    """
    init()  # Initialize the database
    app.run(host=host, debug=debug, port=port)


if __name__ == "__main__":
    init()  # Initialize the database
    app.run(HOST, debug=DEBUG, port=PORT)
