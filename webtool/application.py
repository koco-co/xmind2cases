#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Flask web application for XMind to testcase conversion."""

import logging
import os
import re
import sqlite3
from contextlib import closing
from os.path import exists, join
from typing import Any, Generator, List, Optional, Tuple

import arrow
from flask import (
    Flask,
    abort,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from xmind2cases.testlink import xmind_to_testlink_xml_file
from xmind2cases.utils import get_xmind_testcase_list, get_xmind_testsuites
from xmind2cases.zentao import xmind_to_zentao_csv_file

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
ALLOWED_EXTENSIONS = ["xmind"]
DEBUG = True
DATABASE = os.path.join(here, "data.db3")
HOST = "0.0.0.0"
PORT = int(os.environ.get("FLASK_PORT", "5002"))

# Flask app
app = Flask(__name__)
app.config.from_object(__name__)


def connect_db() -> sqlite3.Connection:
    """Connect to the SQLite database.

    Returns:
        SQLite database connection.
    """
    return sqlite3.connect(app.config["DATABASE"])


def init_db() -> None:
    """Initialize the database with schema from schema.sql."""
    with closing(connect_db()) as db:
        with app.open_resource("schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()


def init() -> None:
    """Initialize the application: create directories and database."""
    app.logger.info("Start initializing the database...")
    if not exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)

    if not exists(DATABASE):
        init_db()
    app.logger.info(
        "Congratulations! the xmind2cases webtool database "
        "has initialized successfully!"
    )


@app.before_request
def before_request() -> None:
    """Set up database connection before each request."""
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception: Optional[Exception]) -> None:
    """Close database connection after each request.

    Args:
        exception: Optional exception that occurred during request.
    """
    db = getattr(g, "db", None)
    if db is not None:
        db.close()


def insert_record(xmind_name: str, note: str = "") -> None:
    """Insert a new record into the database.

    Args:
        xmind_name: Name of the XMind file.
        note: Optional note for the record.
    """
    cursor = g.db.cursor()
    now = str(arrow.now())
    sql = "INSERT INTO records (name,create_on,note) VALUES (?,?,?)"
    cursor.execute(sql, (xmind_name, now, str(note)))
    g.db.commit()


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

    cursor = g.db.cursor()
    sql = "UPDATE records SET is_deleted=1 WHERE id = ?"
    cursor.execute(sql, (record_id,))
    g.db.commit()


def delete_records(keep: int = 20) -> None:
    """Clean up old files on server and mark records as deleted.

    Keeps the most recent 'keep' records and deletes the rest.

    Args:
        keep: Number of recent records to keep.
    """
    assert isinstance(g.db, sqlite3.Connection)
    cursor = g.db.cursor()
    sql = (
        "SELECT * from records where is_deleted<>1 ORDER BY id desc LIMIT -1 offset {}"
    ).format(keep)
    cursor.execute(sql)
    rows = cursor.fetchall()

    for row in rows:
        name = row[1]
        _delete_related_files(name)

        sql = "UPDATE records SET is_deleted=1 WHERE id = ?"
        cursor.execute(sql, (row[0],))
        g.db.commit()


def get_latest_record() -> Optional[Tuple[str, str, str, str, int]]:
    """Get the latest record from the database.

    Returns:
        Tuple of (short_name, name, create_on, note, record_id) or None.
    """
    found = list(get_records(1))
    if found:
        return found[0]
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
    short_name_length = 120
    cursor = g.db.cursor()
    sql = (
        "select * from records where is_deleted<>1 order by id desc limit {}"
    ).format(int(limit))
    cursor.execute(sql)
    rows = cursor.fetchall()

    for row in rows:
        name = row[1]
        short_name = name
        create_on = row[2]
        note = row[3]
        record_id = row[0]

        # Shorten the name for display
        if len(name) > short_name_length:
            short_name = name[:short_name_length] + "..."

        # More readable time format
        create_on = arrow.get(create_on).humanize()
        yield short_name, name, create_on, note, record_id


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
        Secured filename with .xmind extension.

    Raises:
        AssertionError: If unable to parse the filename.
    """
    secured = secure_filename(name)
    if not secured:
        # Only keep letters and digits from file name
        secured = re.sub(r"[^\w\d]+", "_", name)
        assert secured, f"Unable to parse file name: {name}!"
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
            filename = f"{filename[:-6]}_{timestamp}.xmind"
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


@app.route("/preview/<filename>")
def preview_file(filename: str) -> Any:
    """Preview testcases from an uploaded XMind file.

    Args:
        filename: Name of the XMind file.

    Returns:
        Rendered preview template or 404 error.
    """
    full_path = join(app.config["UPLOAD_FOLDER"], filename)

    if not exists(full_path):
        abort(404)

    testsuites = get_xmind_testsuites(full_path)
    suite_count = sum(len(suite.sub_suites or []) for suite in testsuites)
    testcases = get_xmind_testcase_list(full_path)

    return render_template(
        "preview.html", name=filename, suite=testcases, suite_count=suite_count
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
