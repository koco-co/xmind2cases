# tests/test_webtool.py
import io
import os
import shutil
import tempfile
import zipfile

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
    # 回归保护：suite_count 必须传给前端（体检栏「N 个模块」依赖它）
    assert "dataset.suiteCount" in html
    # 回归保护：页脚/顶栏的 GitHub 仓库链接已恢复
    assert "github.com/koco-co/xmind2cases" in html


def test_preview_cell_fixed_size_and_hover_title_markers():
    """回归保护：单元格固定宽高（限高裁剪）+ 悬浮 title 看全文。

    历史版表格单元格为 table-cell-truncate（固定宽高、超出悬浮看全文），v2 改版后
    丢失。表格由 preview.js 客户端渲染、pytest 不执行 JS，故对静态资源做标记断言。
    """
    base = os.path.dirname(os.path.dirname(__file__))
    with open(
        os.path.join(base, "webtool", "static", "js", "preview.js"), encoding="utf-8"
    ) as f:
        js = f.read()
    with open(
        os.path.join(base, "webtool", "static", "css", "preview.css"), encoding="utf-8"
    ) as f:
        css = f.read()
    # 每个 td 渲染 title（步骤/预期合并全文），鼠标悬浮可看全文
    assert "getCellTitle" in js
    # 限高后标记溢出单元格以加渐隐提示
    assert "markClippedCells" in js
    assert "is-clipped" in js
    # CSS：单元格限高裁剪 + 渐隐
    assert "is-clipped" in css
    assert "max-height: 132px" in css


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


def test_api_upload_sanitizes_path_traversal(client):
    """带 ../ 的文件名必须被清洗，文件落在 UPLOAD_FOLDER 内、不逃逸到上层目录。"""
    upload_dir = appmod.app.config["UPLOAD_FOLDER"]
    with open(DOCS_XMIND, "rb") as f:
        data = {"file": (io.BytesIO(f.read()), "../../evil.xmind")}
    resp = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    filename = resp.get_json()["filename"]

    # 返回的文件名不得包含路径分隔符或父目录引用
    assert ".." not in filename
    assert "/" not in filename and "\\" not in filename
    assert filename.endswith(".xmind")

    # 文件确实落在 UPLOAD_FOLDER 内
    saved = os.path.join(upload_dir, filename)
    assert os.path.exists(saved)
    # 规范化后的真实路径仍在 UPLOAD_FOLDER 之下（没有逃逸）
    assert os.path.realpath(saved).startswith(os.path.realpath(upload_dir) + os.sep)
    # UPLOAD_FOLDER 内只应有这一个被清洗后的文件，且其目录正是 UPLOAD_FOLDER
    assert os.path.dirname(os.path.realpath(saved)) == os.path.realpath(upload_dir)


def test_check_file_name_preserves_chinese_and_strips_traversal():
    """中文名原样保留，目录成分 / ../ 被剥离。"""
    c = appmod.check_file_name
    # 中文与中英混合名应原样保留
    assert c("用例.xmind") == "用例.xmind"
    assert c("测试用例_v2.xmind") == "测试用例_v2.xmind"
    assert c("报告.csv") == "报告.csv"
    # 普通 ASCII 名不受影响
    assert c("normal.xmind") == "normal.xmind"
    assert c("dup.xmind") == "dup.xmind"
    # 路径穿越（两种分隔符）只保留基础名
    assert c("../../evil.xmind") == "evil.xmind"
    assert c("..\\..\\evil.xmind") == "evil.xmind"
    assert c("/etc/passwd.xmind") == "passwd.xmind"


def test_api_upload_preserves_chinese_filename(client):
    """中文文件名上传后应原样落盘，不被 mangle 成 xmind.xmind。"""
    upload_dir = appmod.app.config["UPLOAD_FOLDER"]
    with open(DOCS_XMIND, "rb") as f:
        data = {"file": (io.BytesIO(f.read()), "用例报告.xmind")}
    resp = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    filename = resp.get_json()["filename"]
    assert filename == "用例报告.xmind"
    assert os.path.exists(os.path.join(upload_dir, filename))


def test_create_template_normalizes_invalid_header_color(client):
    """create_template 收到非法 header_color 时回退为默认浅红色。"""
    resp = client.post(
        "/api/templates",
        json={"name": "恶意模版", "header_color": "red;}</style><script>"},
    )
    assert resp.status_code == 200
    tpl_id = resp.get_json()["data"]["id"]

    detail = client.get(f"/api/templates/{tpl_id}").get_json()["data"]
    assert detail["header_color"] == "#fef2f2"


def test_update_template_normalizes_invalid_header_color(client):
    """update_template 收到非法 header_color 时回退为默认浅红色。"""
    created = client.post(
        "/api/templates",
        json={"name": "可改模版", "header_color": "#abcdef"},
    ).get_json()
    tpl_id = created["data"]["id"]

    resp = client.put(
        f"/api/templates/{tpl_id}",
        json={"header_color": "#zzz; background:url(x)"},
    )
    assert resp.status_code == 200

    detail = client.get(f"/api/templates/{tpl_id}").get_json()["data"]
    assert detail["header_color"] == "#fef2f2"


def test_update_template_keeps_valid_header_color(client):
    """合法的 6 位十六进制 header_color 应原样保留。"""
    created = client.post(
        "/api/templates",
        json={"name": "颜色模版", "header_color": "#fef2f2"},
    ).get_json()
    tpl_id = created["data"]["id"]

    client.put(f"/api/templates/{tpl_id}", json={"header_color": "#A1B2C3"})
    detail = client.get(f"/api/templates/{tpl_id}").get_json()["data"]
    assert detail["header_color"] == "#A1B2C3"


# ==================== 批量转换 ====================


def _batch_convert(client, name, fmt="zentao"):
    with open(DOCS_XMIND, "rb") as f:
        return client.post(
            "/api/batch/convert",
            data={"file": (io.BytesIO(f.read()), name), "format": fmt},
            content_type="multipart/form-data",
        )


def test_batch_convert_zentao_returns_output(client):
    upload_dir = appmod.app.config["UPLOAD_FOLDER"]
    resp = _batch_convert(client, "batch1.xmind", "zentao")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["output_filename"].endswith(".csv")
    assert os.path.exists(os.path.join(upload_dir, body["output_filename"]))


def test_batch_convert_testlink_returns_xml(client):
    resp = _batch_convert(client, "batch2.xmind", "testlink")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["output_filename"].endswith(".xml")


def test_batch_convert_rejects_bad_format(client):
    resp = _batch_convert(client, "batch3.xmind", "nope")
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_batch_convert_rejects_non_xmind(client):
    resp = client.post(
        "/api/batch/convert",
        data={"file": (io.BytesIO(b"a,b\n1,2\n"), "data.csv"), "format": "zentao"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_batch_zip_packages_outputs(client):
    outputs = [
        _batch_convert(client, n, "zentao").get_json()["output_filename"]
        for n in ("zipa.xmind", "zipb.xmind")
    ]
    resp = client.post("/api/batch/zip", json={"files": outputs})
    assert resp.status_code == 200
    assert resp.mimetype == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(resp.data))
    assert set(zf.namelist()) == set(outputs)


def test_batch_zip_rejects_empty(client):
    resp = client.post("/api/batch/zip", json={"files": []})
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_batch_zip_rejects_traversal(client):
    # basename 化 + realpath 校验：穿越路径取不到 UPLOAD_FOLDER 内真实文件 → 无可打包项
    resp = client.post(
        "/api/batch/zip",
        json={"files": ["../../etc/passwd", "../../../secret.txt"]},
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


# ==================== 转换台统计 ====================


def test_convert_stats_counts_month_and_cases(client):
    _seed_upload(client, "stats1.xmind")
    with appmod.app.app_context():
        stats = appmod._compute_convert_stats()
    assert stats["month_files"] >= 1
    assert stats["total_cases"] > 0
    assert stats["pass_rate"] is None or 0 <= stats["pass_rate"] <= 100


def test_index_renders_real_stats_no_placeholder(client):
    _seed_upload(client, "stats2.xmind")
    html = client.get("/").get_data(as_text=True)
    assert "本月转换文件" in html
    assert "生成测试用例" in html
    # 统计卡 + 批量占位均已落地，首页不应再有「暂未上线」
    assert "暂未上线" not in html


# ==================== 预览编辑持久化 ====================


def _first_case(client, name):
    return client.get(f"/api/preview/{name}/cases?page=1&page_size=10").get_json()[
        "data"
    ]["testcases"][0]


def test_case_edit_persists_name(client):
    name = _seed_upload(client, "edit1.xmind")
    assert _first_case(client, name)  # 确有用例
    r = client.patch(
        f"/api/preview/{name}/cases/0",
        json={"field": "name", "value": "编辑后的标题XYZ"},
    )
    assert r.status_code == 200 and r.get_json()["success"] is True
    assert _first_case(client, name)["name"] == "编辑后的标题XYZ"


def test_case_edit_steps_multiline(client):
    name = _seed_upload(client, "edit2.xmind")
    r = client.patch(
        f"/api/preview/{name}/cases/0",
        json={"field": "steps", "value": "第一步\n第二步\n第三步"},
    )
    assert r.status_code == 200
    actions = [s["actions"] for s in _first_case(client, name)["steps"]]
    assert actions[:3] == ["第一步", "第二步", "第三步"]


def test_case_edit_reflects_in_export(client):
    name = _seed_upload(client, "edit3.xmind")
    client.patch(
        f"/api/preview/{name}/cases/0",
        json={"field": "name", "value": "导出应含此标题ABC"},
    )
    resp = client.post(f"/api/export/{name}/csv", json={})
    assert resp.status_code == 200
    assert "导出应含此标题ABC" in resp.get_data(as_text=True)


def test_case_edit_rejects_bad_field(client):
    name = _seed_upload(client, "edit4.xmind")
    r = client.patch(
        f"/api/preview/{name}/cases/0", json={"field": "evil", "value": "x"}
    )
    assert r.status_code == 400
    assert r.get_json()["success"] is False


def test_case_edit_rejects_out_of_range(client):
    name = _seed_upload(client, "edit5.xmind")
    r = client.patch(
        f"/api/preview/{name}/cases/99999", json={"field": "name", "value": "x"}
    )
    assert r.status_code == 400


def test_case_edit_rejects_csv(client):
    name = _seed_csv(client, "edit.csv")
    r = client.patch(
        f"/api/preview/{name}/cases/0", json={"field": "name", "value": "x"}
    )
    assert r.status_code == 400


# ==================== 版本对比 Diff ====================


def test_diff_empty_when_unedited(client):
    name = _seed_upload(client, "diff1.xmind")
    client.get(f"/api/preview/{name}/cases")  # 触发快照初始化
    res = client.get(f"/api/preview/{name}/diff").get_json()
    assert res["success"] is True
    assert res["data"]["changes"] == []
    assert res["data"]["changed_rows"] == 0


def test_diff_shows_edit_after_patch(client):
    name = _seed_upload(client, "diff2.xmind")
    client.patch(
        f"/api/preview/{name}/cases/0",
        json={"field": "name", "value": "改了标题DIFF"},
    )
    res = client.get(f"/api/preview/{name}/diff").get_json()
    assert res["success"] is True
    changes = res["data"]["changes"]
    assert any(c["field"] == "name" and c["new"] == "改了标题DIFF" for c in changes)
    assert res["data"]["changed_rows"] >= 1


def test_diff_rejects_csv(client):
    name = _seed_csv(client, "diff.csv")
    r = client.get(f"/api/preview/{name}/diff")
    assert r.status_code == 400
    assert r.get_json()["success"] is False


# ==================== 相关需求列（内置 requirements） ====================


def test_migrate_custom_requirements_column():
    """自定义「相关需求」列迁移为内置 requirements 列（保留位次、其余列不动）"""
    import json

    with appmod.app.app_context():
        tpl = appmod.ColumnTemplate(
            name="迁移测试",
            columns_json=json.dumps(
                [
                    {"id": "suite", "name": "所属模块", "order": 1, "is_custom": False},
                    {
                        "id": "custom_9",
                        "name": "相关需求",
                        "order": 2,
                        "is_custom": True,
                        "default_value": "(#15911)",
                        "values": {"0": "(#15911)"},
                    },
                    {"id": "name", "name": "用例标题", "order": 5, "is_custom": False},
                ],
                ensure_ascii=False,
            ),
        )
        appmod.db.session.add(tpl)
        appmod.db.session.commit()

        appmod._migrate_requirements_column()

        tpl = appmod.ColumnTemplate.query.filter_by(name="迁移测试").first()
        cols = tpl.columns
        assert cols[0]["id"] == "suite"
        assert cols[1]["id"] == "requirements"
        assert cols[1]["name"] == "相关需求"
        assert cols[1]["is_custom"] is False
        assert cols[1]["order"] == 2  # 保留原列位次
        assert "values" not in cols[1]  # 逐行硬编码值被丢弃
        assert cols[2]["id"] == "name"
        # 无自定义相关需求列的模版不受影响
        other = appmod.ColumnTemplate(name="其他", columns_json="[]")
        appmod.db.session.add(other)
        appmod.db.session.commit()
        appmod._migrate_requirements_column()
        assert appmod.ColumnTemplate.query.filter_by(name="其他").first().columns == []


def test_export_csv_requirements_and_fullwidth_parens():
    """导出 CSV：相关需求列取值 + 全角括号统一转半角"""
    cols = [
        {"id": "suite", "name": "所属模块", "order": 1, "is_custom": False},
        {"id": "requirements", "name": "相关需求", "order": 2, "is_custom": False},
        {"id": "name", "name": "用例标题", "order": 3, "is_custom": False},
    ]
    testcases = [
        {
            "suite": "模块（自动化）(#10629)",
            "requirements": "(#15889)",
            "name": "验证（登录）",
            "steps": [{"actions": "1）点（确定）", "expectedresults": "2）成功）"}],
        }
    ]
    content = appmod.generate_csv_with_columns(testcases, cols)
    import csv
    import io

    rows = list(csv.reader(io.StringIO(content)))
    assert rows[0] == ["所属模块", "相关需求", "用例标题"]
    assert rows[1][0] == "(#10629)"
    assert rows[1][1] == "(#15889)"
    assert rows[1][2] == "验证(登录)"
    assert "（" not in content and "）" not in content


def test_get_column_value_simplifies_suite_and_reads_requirements():
    with appmod.app.app_context():
        col_suite = {"id": "suite", "is_custom": False}
        col_req = {"id": "requirements", "is_custom": False}
        tc = {"suite": "模块(#10629)", "requirements": "(#15889)"}
        assert appmod.get_column_value(tc, col_suite, 0) == "(#10629)"
        assert appmod.get_column_value(tc, col_req, 0) == "(#15889)"


def test_get_cases_backfills_requirements_from_stale_snapshot(client):
    """升级前的旧快照缺 requirements 字段，读取时按行序回填且不覆盖既有编辑"""
    import json

    from webtool.models import CaseSnapshot

    name = _seed_upload(client, "stale.xmind")
    app = appmod.app
    with app.app_context():
        fresh = appmod.get_xmind_testcase_list(
            os.path.join(app.config["UPLOAD_FOLDER"], name)
        )
        # 构造缺 requirements 的旧快照（模拟升级前落库）
        stale = [{k: v for k, v in tc.items() if k != "requirements"} for tc in fresh]
        appmod.db.session.add(
            CaseSnapshot(
                filename=name, cases_json=json.dumps(stale, ensure_ascii=False)
            )
        )
        appmod.db.session.commit()

        cases = appmod.get_cases(name)
        assert all("requirements" in tc for tc in cases)
        assert [tc["requirements"] for tc in cases] == [
            tc.get("requirements", "") for tc in fresh
        ]


def test_migrate_default_custom_columns_appends_case_type_and_stage():
    """缺失「用例类型」「适用阶段」的模版，初始化迁移自动补上自定义列"""
    import json

    with appmod.app.app_context():
        tpl = appmod.ColumnTemplate(
            name="迁移测试2",
            columns_json=json.dumps(
                [
                    {"id": "suite", "name": "所属模块", "order": 1, "is_custom": False},
                    {"id": "name", "name": "用例标题", "order": 2, "is_custom": False},
                ],
                ensure_ascii=False,
            ),
        )
        appmod.db.session.add(tpl)
        appmod.db.session.commit()

        appmod._migrate_default_custom_columns()

        tpl = appmod.ColumnTemplate.query.filter_by(name="迁移测试2").first()
        cols = tpl.columns
        assert len(cols) == 4
        case_type = cols[2]
        stage = cols[3]
        assert case_type["name"] == "用例类型"
        assert case_type["is_custom"] is True
        assert case_type["default_value"] == "功能测试"
        assert case_type["order"] == 3
        assert stage["name"] == "适用阶段"
        assert stage["is_custom"] is True
        assert stage["default_value"] == "功能测试阶段"
        assert stage["order"] == 4
        # 自定义列 id 不冲突
        assert case_type["id"] != stage["id"]
        # 已含这两列的模版不被改动
        existing = appmod.ColumnTemplate(
            name="迁移测试3",
            columns_json=json.dumps(
                [
                    {"id": "custom_1", "name": "用例类型", "is_custom": True},
                    {"id": "custom_2", "name": "适用阶段", "is_custom": True},
                ],
                ensure_ascii=False,
            ),
        )
        appmod.db.session.add(existing)
        appmod.db.session.commit()
        before = json.dumps(existing.columns, ensure_ascii=False)
        appmod._migrate_default_custom_columns()
        assert json.dumps(existing.columns, ensure_ascii=False) == before
