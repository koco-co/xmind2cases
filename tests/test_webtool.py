# tests/test_webtool.py
import io
import os
import shutil
import tempfile

import pytest

from webtool import application as appmod


@pytest.fixture
def client():
    """Flask test client，使用临时 upload 目录与临时 sqlite。

    Note: db is already bound via db.init_app(app) at module import time, so we
    do NOT call db.init_app(app) a second time (that would raise
    "A 'SQLAlchemy' instance has already been registered on this Flask application").
    Instead we just ensure tables exist in the existing DB, and isolate uploads
    to a temp directory (UPLOAD_FOLDER is read at request time, so this is reliable).
    Tests assert on response JSON only, not on DB rows, so shared DB state is fine.
    """
    tmp = tempfile.mkdtemp(prefix="x2c_test_")
    upload = os.path.join(tmp, "uploads")
    os.makedirs(upload, exist_ok=True)
    app = appmod.app
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = upload
    with app.app_context():
        appmod.db.create_all()
        if appmod.ColumnTemplate.query.count() == 0:
            import json

            appmod.db.session.add(
                appmod.ColumnTemplate(
                    name="默认",
                    columns_json=json.dumps(appmod.DEFAULT_COLUMNS, ensure_ascii=False),
                )
            )
            appmod.db.session.commit()
    yield app.test_client()
    shutil.rmtree(tmp, ignore_errors=True)


DOCS_XMIND = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "docs", "test.xmind"
)


def test_api_upload_xmind_returns_filename(client):
    with open(DOCS_XMIND, "rb") as f:
        data = {"file": (io.BytesIO(f.read()), "demo.xmind")}
    resp = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["filename"].endswith(".xmind")


def test_api_upload_rejects_bad_extension(client):
    data = {"file": (io.BytesIO(b"hello"), "notes.txt")}
    resp = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_api_upload_empty_filename(client):
    data = {"file": (io.BytesIO(b""), "")}
    resp = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_api_upload_dedupes_same_name(client):
    def up():
        with open(DOCS_XMIND, "rb") as f:
            return client.post(
                "/api/upload",
                data={"file": (io.BytesIO(f.read()), "dup.xmind")},
                content_type="multipart/form-data",
            ).get_json()["filename"]

    first = up()
    second = up()
    assert first == "dup.xmind"
    assert second != first and second.endswith(".xmind")
