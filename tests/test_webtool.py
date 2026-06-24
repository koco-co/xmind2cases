# tests/test_webtool.py
import io
import os
import shutil
import tempfile

# IMPORTANT: set the DB env-var BEFORE importing the application module so that
# the Flask app singleton binds to a temp DB at import time (not to data.db3).
os.environ.setdefault(
    "XMIND2CASES_DB",
    os.path.join(tempfile.mkdtemp(prefix="x2c_testdb_"), "test.db3"),
)

import pytest

from webtool import application as appmod


@pytest.fixture
def client():
    """Flask test client，使用临时 upload 目录与隔离的临时 sqlite。

    Note: db is already bound via db.init_app(app) at module import time, so we
    do NOT call db.init_app(app) a second time (that would raise
    "A 'SQLAlchemy' instance has already been registered on this Flask application").
    Instead we just ensure tables exist in the temp DB, and isolate uploads
    to a per-test temp directory (UPLOAD_FOLDER is read at request time).
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


def _seed_upload(client, name="demo.xmind"):
    with open(DOCS_XMIND, "rb") as f:
        client.post(
            "/api/upload",
            data={"file": (io.BytesIO(f.read()), name)},
            content_type="multipart/form-data",
        )
    return name


def test_index_renders_v2_convert(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "一处转换，两个方向" in html
    assert "theme.css" in html and "convert.css" in html
    assert 'data-screen="convert"' in html


def test_empty_cells_returns_health_summary(client):
    name = _seed_upload(client)
    resp = client.get(f"/api/preview/{name}/empty-cells")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "empty_cells" in data
    assert isinstance(data["total"], int) and data["total"] > 0
    pc = data["priority_counts"]
    assert set(pc.keys()) == {"1", "2", "3", "4"}
    assert sum(pc.values()) == data["total"]


def test_preview_renders_v2(client):
    name = _seed_upload(client, "preview_demo.xmind")
    resp = client.get(f"/preview/{name}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "用例体检" in html
    assert "preview.css" in html and "theme.css" in html
    assert 'id="case-table"' in html


def _seed_csv(client, name="zentao.csv"):
    rows = (
        "用例编号,所属产品,所属模块,用例标题,前置条件,步骤,预期,优先级,用例类型\n"
        "TC001,产品A,/模块1,登录,已注册,1. 输入,1. 成功,1,功能测试\n"
    )
    client.post(
        "/api/upload",
        data={"file": (io.BytesIO(rows.encode("utf-8")), name)},
        content_type="multipart/form-data",
    )
    return name


def test_preview_csv_shows_download_xmind(client):
    name = _seed_csv(client)
    html = client.get(f"/preview/{name}").get_data(as_text=True)
    assert "下载 XMind" in html
    assert "用例体检" not in html  # CSV 不显示体检
    assert 'id="csv-download-btn"' in html
    assert "download_xmind_from_csv" in html or "/to/xmind-from-csv" in html
