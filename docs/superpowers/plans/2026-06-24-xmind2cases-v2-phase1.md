# XMind2Cases v2 改版 — Phase 1 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把「转换台」与「用例预览」两屏重写成 v2 warm 设计语言，接好所有现有后端能力；批量 / 统计 / 版本对比 / 用例内容编辑按「暂未上线」占位。

**Architecture:** 沿用 Flask + Jinja + 原生 JS。弃用 Tailwind CDN 与旧 slate 主题，改为 CSS 变量驱动的自写设计系统（`theme.css` + 每屏 CSS）。后端仅新增 `POST /api/upload`，并把现有 `empty-cells` 端点扩成「体检摘要」（额外返回 `total` + `priority_counts`，全量解析本就发生）。其余路由 0 改动，`models.py` 不改。

**Tech Stack:** Flask、Flask-SQLAlchemy、Jinja2、原生 ES（无构建）、自写 CSS（CSS 变量）、Google Fonts（Newsreader + Noto Sans SC）、pytest（Flask test client）。

## 像素源真相（pixel source of truth）

`docs/design/v2-prototype/XMind2Cases-v2.dc.html` 是 v2 设计原型（Claude Design handoff）。所有精确视觉值（配色、间距、圆角、字号、SVG 图标、文案）以它为准。原型是 DC 框架的内联样式写法；**实现时把内联样式翻译成下方「CSS 类契约」里的命名类**。原型关键区段：

- CONVERT SCREEN：原型 `<sc-if value="{{ isConvert }}">` 段（约 50–189 行）
- PREVIEW SCREEN：`<sc-if value="{{ isPreview }}">` 段（约 192–346 行）
- COLUMN MODAL：约 407–433 行；TEMPLATE MODAL：约 435–485 行
- 设计 tokens / 字体 / 滚动条 / 聚焦态：原型 `<style>` 段（约 14–25 行）+ spec §4

设计 spec：`docs/superpowers/specs/2026-06-24-xmind2cases-v2-phase1-redesign-design.md`。

## Global Constraints

逐条 verbatim，每个任务都隐含适用：

- **配色 / 字体 / token**：见 spec §4 与原型。主品牌 `#C96442`，深色按钮 `#262624`/hover `#3A3835`/文字 `#F5F2EC`，背景 `#F0EEE6`，卡片白 `#FFFFFF` 边框 `#E7E3D8`。字体：标题/大数字 `'Newsreader',serif`，正文 `'Noto Sans SC',sans-serif`。
- **优先级映射（导出不变，仅显示）**：`importance` 1→`P1`（`#B5503A`/`#F6E7E2`），2→`P2`（`#9A7A2E`/`#F6EFDD`），3→`P3`（`#5E7355`/`#EBF0E6`），4/其它→`P4`（`#7A7868`/`#F0EDE4`）。
- **保留现有默认列**：不改库内「默认」模板的列集与顺序；视觉按列 `type` 套用。
- **编辑模式 Phase 1 = 仅列管理**：单元格内容编辑 / 优先级下拉 / 增删用例行 / 版本对比 → 渲染但禁用 + 「暂未上线」，不改 parsed 用例内容、不入库。
- **占位不放假数据**：统计卡片显示 `—` + 「暂未上线」；批量模式显示空状态占位。
- **不主动渲染/截图原型或应用**（除非用户要求）；以读源 + Flask test client 断言验证。
- **现有路由与导出字节不回归**：`/api/export`、`/<file>/to/xmind-from-csv`、模板 CRUD、分页行为不变。

## CSS 类契约（JS 与 CSS 必须一致）

JS render 函数发射、CSS 负责样式的关键类（各任务统一使用）：

- 顶栏：`.topbar`、`.topbar__inner`、`.brand`、`.brand__logo`、`.brand__name`、`.brand__sub`、`.topbar__nav`、`.nav-link`
- 按钮：`.btn`、`.btn--ink`（深色实心）、`.btn--outline`、`.btn--csv`、`.btn--xml`、`.btn--disabled`
- 分段开关：`.seg`、`.seg__btn`、`.seg__btn--on`
- 转换台：`.convert`、`.hero`、`.convert-card`、`.flow`、`.flow__node`、`.dropzone`、`.dropzone--over`、`.out-chip`、`.stat-grid`、`.stat-card`、`.stat-card--placeholder`、`.records`、`.rec-row`、`.rec-actions`、`.batch-empty`
- 预览：`.preview`、`.pv-head`、`.pv-title`、`.health`、`.health__count`、`.health__warn`、`.health__pri`、`.pri-dot`、`.edit-banner`、`.case-table`、`.case-table thead`、`.col-th`、`.drag-handle`、`.col-actions`、`.idx-cell`、`.pri-badge`、`.pri-badge--p1/p2/p3/p4`、`.steps-list`、`.step-n`、`.empty-chip`、`.cell-text`、`.pager`、`.pager__btn`
- 弹窗：`.modal-overlay`、`.modal`、`.modal__title`、`.modal__divider`、`.modal__field`、`.modal__label`、`.modal__input`、`.modal__check`、`.modal__actions`、`.swatch`、`.swatch--on`

JSON 契约：

- `POST /api/upload` → `{success: bool, filename?: str, message?: str}`
- `GET /api/preview/<file>/empty-cells?template_id=<int?>` → `{success: bool, data: {empty_cells: [{colId,rowIndex,colName}], total: int, priority_counts: {"1":int,"2":int,"3":int,"4":int}}}`

---

### Task 1: 后端 `POST /api/upload` + Flask 测试夹具

**Files:**
- Modify: `webtool/application.py`（在导出 API 区块前后新增路由）
- Create: `tests/test_webtool.py`（含可复用 `client` 夹具）

**Interfaces:**
- Produces: 路由 `POST /api/upload`，返回 `{success, filename?, message?}`；pytest 夹具 `client`（带临时 upload 目录 + 临时 sqlite），后续任务复用。

- [ ] **Step 1: 写失败测试 + 夹具**

创建 `tests/test_webtool.py`：

```python
# tests/test_webtool.py
import io
import os
import shutil
import tempfile

import pytest

from webtool import application as appmod


@pytest.fixture
def client():
    """Flask test client，使用临时 upload 目录与临时 sqlite。"""
    tmp = tempfile.mkdtemp(prefix="x2c_test_")
    upload = os.path.join(tmp, "uploads")
    os.makedirs(upload, exist_ok=True)
    app = appmod.app
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = upload
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(tmp, 'test.db3')}"
    appmod.db.init_app(app)
    with app.app_context():
        appmod.db.create_all()
        if appmod.ColumnTemplate.query.count() == 0:
            import json
            appmod.db.session.add(appmod.ColumnTemplate(
                name="默认",
                columns_json=json.dumps(appmod.DEFAULT_COLUMNS, ensure_ascii=False),
            ))
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
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_webtool.py -v`
Expected: FAIL（`/api/upload` 返回 404）。

- [ ] **Step 3: 实现路由（复用 `save_file`）**

在 `webtool/application.py` 的「导出 API」区块前加入：

```python
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
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest tests/test_webtool.py -v`
Expected: 4 passed。

- [ ] **Step 5: 提交**

```bash
git add webtool/application.py tests/test_webtool.py
git commit -m "feat(webtool): 新增 POST /api/upload 单文件上传 JSON 接口"
```

---

### Task 2: 后端 `empty-cells` 扩成「体检摘要」（+ total + priority_counts）

**Files:**
- Modify: `webtool/application.py:621-659`（`get_empty_cells`）
- Modify: `tests/test_webtool.py`（追加测试）

**Interfaces:**
- Consumes: 夹具 `client`（Task 1）。
- Produces: `GET /api/preview/<file>/empty-cells` 响应新增 `data.total` 与 `data.priority_counts`（`{"1","2","3","4"}`→int），`empty_cells` 行为不变。前端体检 bar 依赖此。

- [ ] **Step 1: 写失败测试**

在 `tests/test_webtool.py` 追加：

```python
def _seed_upload(client, name="demo.xmind"):
    with open(DOCS_XMIND, "rb") as f:
        client.post("/api/upload",
                    data={"file": (io.BytesIO(f.read()), name)},
                    content_type="multipart/form-data")
    return name


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
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_webtool.py::test_empty_cells_returns_health_summary -v`
Expected: FAIL（KeyError `total`）。

- [ ] **Step 3: 重写 `get_empty_cells`**

将 `webtool/application.py` 的 `get_empty_cells` 整体替换为：

```python
@app.route("/api/preview/<path:filename>/empty-cells", methods=["GET"])
def get_empty_cells(filename: str) -> Any:
    """体检摘要：全量优先级分布 + 总数 + 空值单元格列表。"""
    full_path = join(app.config["UPLOAD_FOLDER"], filename)
    if not exists(full_path):
        abort(404)

    if filename.lower().endswith(".csv"):
        from xmind2cases.csv_to_xmind import csv_to_testcase_dicts
        testcases = csv_to_testcase_dicts(full_path)
    else:
        testcases = get_xmind_testcase_list(full_path)

    priority_counts = {"1": 0, "2": 0, "3": 0, "4": 0}
    for tc in testcases:
        imp = str(tc.get("importance", 2))
        if imp not in priority_counts:
            imp = "4"
        priority_counts[imp] += 1

    empty_cells: list = []
    if not filename.lower().endswith(".csv"):
        template_id = request.args.get("template_id", type=int)
        if template_id:
            tpl = ColumnTemplate.query.get(template_id)
            columns = tpl.columns if tpl else DEFAULT_COLUMNS
            sorted_columns = sorted(columns, key=lambda x: x.get("order", 0))
            empty_check_cols = [c for c in sorted_columns if c.get("empty_check") is True]
            for row_index, tc in enumerate(testcases):
                for col in empty_check_cols:
                    val = get_column_value(tc, col, row_index)
                    if _is_value_empty(val):
                        empty_cells.append({
                            "colId": col.get("id", ""),
                            "rowIndex": row_index,
                            "colName": col.get("name", col.get("id", "")),
                        })

    return jsonify({
        "success": True,
        "data": {
            "empty_cells": empty_cells,
            "total": len(testcases),
            "priority_counts": priority_counts,
        },
    })
```

- [ ] **Step 4: 运行确认通过（含原有测试不回归）**

Run: `pytest tests/test_webtool.py -v && pytest -q`
Expected: 全部 passed。

- [ ] **Step 5: 提交**

```bash
git add webtool/application.py tests/test_webtool.py
git commit -m "feat(webtool): empty-cells 端点返回体检摘要（total + 优先级分布）"
```

---

### Task 3: `theme.css` 设计系统（tokens + 共享组件）

**Files:**
- Create: `webtool/static/css/theme.css`

**Interfaces:**
- Produces: CSS 变量 + 共享类 `.topbar*`、`.brand*`、`.nav-link`、`.btn*`、`.seg*`、`.modal*`、滚动条 `.x-scroll`、表单聚焦态。转换台与预览均依赖。

- [ ] **Step 1: 写 `theme.css`**

创建 `webtool/static/css/theme.css`（tokens 来自 spec §4 / 原型；组件样式对照原型顶栏与按钮）：

```css
:root{
  --bg:#F0EEE6; --surface:#FFFFFF;
  --border:#E7E3D8; --border-2:#E4E0D5; --divider:#EDE9DF; --row-divider:#F1EDE3;
  --text:#2B2A27; --text-strong:#22211F; --text-2:#6B6A63; --text-3:#8A887E; --text-4:#A4A299;
  --accent:#C96442; --accent-ink:#A4623F;
  --ink:#262624; --ink-hover:#3A3835; --on-ink:#F5F2EC;
  --toggle-track:#F3EFE6; --field-bg:#FBFAF6;
  --selection:#E7D3C7; --scrollbar:#DBD6C9;
  --p1-fg:#B5503A; --p1-bg:#F6E7E2;
  --p2-fg:#9A7A2E; --p2-bg:#F6EFDD;
  --p3-fg:#5E7355; --p3-bg:#EBF0E6;
  --p4-fg:#7A7868; --p4-bg:#F0EDE4;
  --warn-fg:#9A7A2E; --warn-bg:#F6EFDD; --warn-border:#E6D9B6; --warn-dash:#E2CF94;
  --ok-fg:#5E7355; --ok-bg:#EFF3E9;
  --radius-card:16px; --radius-btn:10px; --radius-chip:8px;
}
*{ box-sizing:border-box; }
body{ margin:0; min-height:100vh; background:var(--bg);
  font-family:'Noto Sans SC','Helvetica Neue',sans-serif; color:var(--text);
  -webkit-font-smoothing:antialiased; }
::selection{ background:var(--selection); }
.serif{ font-family:'Newsreader',serif; }
a{ color:inherit; text-decoration:none; }

.x-scroll::-webkit-scrollbar{ height:10px; width:10px; }
.x-scroll::-webkit-scrollbar-thumb{ background:var(--scrollbar); border-radius:8px;
  border:2px solid transparent; background-clip:padding-box; }
.x-scroll::-webkit-scrollbar-track{ background:transparent; }
@keyframes blink{ 0%,100%{opacity:1} 50%{opacity:.25} }

/* 顶栏 */
.topbar{ border-bottom:1px solid var(--border-2); background:rgba(240,238,230,0.85);
  backdrop-filter:blur(8px); position:sticky; top:0; z-index:20; }
.topbar__inner{ max-width:1320px; margin:0 auto; padding:16px 32px;
  display:flex; align-items:center; justify-content:space-between; }
.brand{ display:flex; align-items:center; gap:12px; cursor:pointer; }
.brand__logo{ width:38px; height:38px; border-radius:10px; background:var(--accent);
  display:flex; align-items:center; justify-content:center; box-shadow:0 1px 2px rgba(43,42,39,.18);
  font-family:'Newsreader',serif; font-size:22px; font-weight:600; color:#FBF6EF; }
.brand__name{ font-family:'Newsreader',serif; font-size:22px; font-weight:600; letter-spacing:-.01em; }
.brand__sub{ font-size:12px; color:var(--text-3); }
.topbar__nav{ display:flex; align-items:center; gap:22px; font-size:13.5px; color:var(--text-2); }
.nav-link{ cursor:pointer; } .nav-link:hover{ color:var(--text); }

/* 按钮 */
.btn{ border:none; font-family:inherit; font-size:13.5px; font-weight:500; cursor:pointer;
  border-radius:var(--radius-btn); padding:9px 14px; display:inline-flex; align-items:center; gap:7px; }
.btn--ink{ background:var(--ink); color:var(--on-ink); } .btn--ink:hover{ background:var(--ink-hover); }
.btn--outline{ background:var(--surface); color:#5A584F; border:1px solid var(--border-2); }
.btn--outline:hover{ background:#F7F4EC; }
.btn--csv{ background:#EFF3E9; color:#4F6248; border:1px solid #D3DDC9; }
.btn--xml{ background:#F6EFDD; color:#9A7A2E; border:1px solid #E6D9B6; }
.btn--disabled{ opacity:.5; cursor:not-allowed; }

/* 分段开关 */
.seg{ display:flex; background:var(--toggle-track); border-radius:11px; padding:4px; }
.seg__btn{ border:none; background:transparent; color:#7A7868; font-family:inherit;
  font-size:13.5px; font-weight:500; padding:9px 16px; border-radius:8px; cursor:pointer; }
.seg__btn--on{ background:var(--ink); color:var(--on-ink); box-shadow:0 1px 2px rgba(43,42,39,.2); }

/* 表单聚焦 */
.modal__input:focus, textarea:focus, input:focus{ outline:none; }
.modal__input:focus{ border-color:var(--accent); box-shadow:0 0 0 3px rgba(201,100,66,.12); }

/* 弹窗 */
.modal-overlay{ position:fixed; inset:0; background:rgba(43,42,39,.32);
  display:flex; align-items:center; justify-content:center; z-index:50; padding:24px; }
.modal{ background:var(--surface); border-radius:18px; padding:28px; width:440px; max-width:100%;
  box-shadow:0 20px 50px rgba(43,42,39,.25); }
.modal__title{ font-family:'Newsreader',serif; font-weight:600; font-size:21px; margin:0 0 6px; color:var(--text-strong); }
.modal__divider{ height:1px; background:var(--divider); margin:0 0 20px; }
.modal__field{ margin-bottom:18px; }
.modal__label{ display:block; font-size:13px; font-weight:500; color:#4A4843; margin-bottom:7px; }
.modal__input{ width:100%; border:1px solid var(--border-2); border-radius:10px; padding:11px 13px;
  font-size:14px; color:var(--text); font-family:'Noto Sans SC',sans-serif; }
.modal__check{ display:flex; gap:12px; cursor:pointer; align-items:flex-start; }
.modal__actions{ display:flex; justify-content:flex-end; gap:10px; }
.swatch{ width:30px; height:30px; border-radius:8px; border:1px solid var(--border-2); cursor:pointer; }
.swatch--on{ border:2px solid var(--accent); }
```

- [ ] **Step 2: 校验语法**

Run: `npx --yes csstree-validator webtool/static/css/theme.css 2>/dev/null || python -c "open('webtool/static/css/theme.css').read(); print('readable')"`
Expected: 无报错（或打印 `readable`）。

- [ ] **Step 3: 提交**

```bash
git add webtool/static/css/theme.css
git commit -m "feat(webtool): 新增 v2 设计系统 theme.css（tokens + 共享组件）"
```

---

### Task 4: 转换台 — `index.html` + `convert.css` + `upload.js`

**Files:**
- Modify: `webtool/templates/index.html`（整页重写）
- Create: `webtool/static/css/convert.css`
- Modify: `webtool/static/js/upload.js`（整文件重写）
- Modify: `tests/test_webtool.py`（追加渲染冒烟测试）

**Interfaces:**
- Consumes: `theme.css` 类；`POST /api/upload`；既有 `get_records()` 模板上下文；既有路由 `uploaded_file`/`download_zentao_file`/`download_testlink_file`/`preview_file`/`delete_file`/`download_xmind_from_csv`。
- Produces: 转换台页面（含 `data-screen="convert"` 标记）。

像素参考：原型 CONVERT SCREEN 段（约 50–189 行）。`max-width:780px`。

- [ ] **Step 1: 写失败冒烟测试**

在 `tests/test_webtool.py` 追加：

```python
def test_index_renders_v2_convert(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "一处转换，两个方向" in html
    assert "theme.css" in html and "convert.css" in html
    assert 'data-screen="convert"' in html
```

Run: `pytest tests/test_webtool.py::test_index_renders_v2_convert -v` → FAIL。

- [ ] **Step 2: 重写 `index.html`**

整页结构（Jinja）；顶栏用 `theme.css` 共享类；转换卡片含方向/模式分段开关、flow-viz、dropzone、输出 chip、CTA；统计卡片占位；最近记录用 Jinja 渲染（保留今天的 CSV/XMind 条件图标逻辑，restyle 成 `.rec-*`）。具体内联样式值照原型翻译进 `convert.css`。骨架：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>XMind2Cases</title>
  <link rel="shortcut icon" href="{{ url_for('static',filename='favicon.ico') }}" type="image/x-icon"/>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static',filename='css/theme.css') }}">
  <link rel="stylesheet" href="{{ url_for('static',filename='css/convert.css') }}">
</head>
<body data-screen="convert">
  <header class="topbar"> ... brand（点击 location='/'）+ nav（使用指南/反馈问题/GitHub） ... </header>
  <main class="convert">
    <div class="hero">
      <h1 class="serif">一处转换，两个方向</h1>
      <p>XMind 思维导图与禅道 / TestLink 用例之间自由互转，全程本地完成，数据不出本机。</p>
    </div>
    <div class="convert-card">
      <div class="seg" data-toggle="dir">
        <button class="seg__btn seg__btn--on" data-dir="x2c">XMind → 用例</button>
        <button class="seg__btn" data-dir="c2x">CSV → XMind</button>
      </div>
      <div class="seg" data-toggle="mode">
        <button class="seg__btn seg__btn--on" data-mode="single">单文件</button>
        <button class="seg__btn" data-mode="batch">批量转换</button>
      </div>
      <div class="flow"> ... 源/箭头/目标，文案用 data-flow-src / data-flow-tgt ... </div>
      <div id="single-panel">
        <div class="dropzone" id="dropzone"> ... 上传图标 + #drop-title + #drop-sub ... </div>
        <input id="file" type="file" accept=".xmind" hidden>
        <div class="out-chips" id="out-chips"></div>
        <button class="btn btn--ink" id="convert-btn" style="width:100%;margin-top:20px;">
          <span id="convert-label">转换为测试用例</span>
        </button>
      </div>
      <div id="batch-panel" hidden>
        <div class="batch-empty">批量转换 · 暂未上线</div>
      </div>
    </div>
    <div class="stat-grid">
      <div class="stat-card stat-card--placeholder"><div class="serif">—</div><div>本月转换文件 · 暂未上线</div></div>
      <div class="stat-card stat-card--placeholder"><div class="serif">—</div><div>生成测试用例 · 暂未上线</div></div>
      <div class="stat-card stat-card--placeholder"><div class="serif">—</div><div>用例体检通过率 · 暂未上线</div></div>
    </div>
    <section class="records">
      <div class="records__head"><h2 class="serif">最近转换记录</h2></div>
      {% if records %}
        {% for record in records %}
          <div class="rec-row"> ... 文件名 record[0]/title record[1] · 时间 record[2] · 操作图标 ... </div>
        {% endfor %}
      {% else %}
        <div class="records__empty">欢迎使用 XMind2Cases！上传 XMind 文件，快速转换为测试用例。</div>
      {% endif %}
    </section>
    <footer class="convert__footer">Powered by XMind2Cases · 本地优先的测试用例转换工具</footer>
  </main>
  <script src="{{ url_for('static',filename='js/upload.js') }}"></script>
</body>
</html>
```

记录行操作图标条件逻辑（保留今天行为，见现 `index.html:114-172`）：CSV 记录 → 下载 XMind（`download_xmind_from_csv`，默认分隔符直链）+ 预览 + 删除；XMind 记录 → 下载 XMind（`uploaded_file`）+ 导出 CSV（`download_zentao_file`）+ 导出 XML（`download_testlink_file`）+ 预览（`preview_file`）+ 删除（`delete_file`，`onclick="return confirm(...)"`）。SVG 图标照原型记录行（原型约 174–178 行）。

- [ ] **Step 3: 写 `convert.css`**

把原型 CONVERT 段内联样式翻译成 `.convert/.hero/.convert-card/.flow/.dropzone/.out-chip/.stat-grid/.stat-card/.records/.rec-row/.rec-actions/.batch-empty` 等类。`.dropzone--over` 为拖拽高亮（`border-color:var(--accent); background:#FBF4EE`）。`.stat-card--placeholder` 文字用 `var(--text-3)`。

- [ ] **Step 4: 重写 `upload.js`**

完整逻辑：

```javascript
// 转换台交互：方向 / 模式开关、上传、XMind→预览、CSV→分隔符→下载
document.addEventListener('DOMContentLoaded', () => {
  const state = { dir: 'x2c', mode: 'single', file: null };
  const $ = (s) => document.querySelector(s);
  const dropzone = $('#dropzone'), fileInput = $('#file');
  const convertBtn = $('#convert-btn'), convertLabel = $('#convert-label');
  const dropTitle = $('#drop-title'), dropSub = $('#drop-sub'), outChips = $('#out-chips');

  const COPY = {
    x2c: { accept: '.xmind', label: '转换为测试用例',
           title: '点击或拖拽上传 .xmind 文件', sub: '解析思维导图结构，生成结构化测试用例',
           src: 'XMind', tgt: '用例表格', chips: ['禅道 CSV', 'TestLink XML'] },
    c2x: { accept: '.csv', label: '转换为 XMind',
           title: '点击或拖拽上传禅道导出的 .csv', sub: '还原为可在 XMind 中打开的思维导图',
           src: '禅道 CSV', tgt: 'XMind', chips: ['XMind 思维导图 (.xmind)'] },
  };

  function applyDir() {
    const c = COPY[state.dir];
    fileInput.setAttribute('accept', c.accept);
    convertLabel.textContent = c.label;
    if (dropTitle) dropTitle.textContent = c.title;
    if (dropSub) dropSub.textContent = c.sub;
    const sEl = document.querySelector('[data-flow-src]'); if (sEl) sEl.textContent = c.src;
    const tEl = document.querySelector('[data-flow-tgt]'); if (tEl) tEl.textContent = c.tgt;
    if (outChips) outChips.innerHTML = c.chips.map(
      (l) => `<span class="out-chip">${l}</span>`).join('');
    state.file = null; resetDropzone();
  }

  function resetDropzone() {
    if (dropTitle) dropTitle.textContent = COPY[state.dir].title;
  }

  // 分段开关
  document.querySelector('[data-toggle="dir"]').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-dir]'); if (!btn) return;
    state.dir = btn.dataset.dir;
    document.querySelectorAll('[data-toggle="dir"] .seg__btn').forEach(
      (b) => b.classList.toggle('seg__btn--on', b === btn));
    applyDir();
  });
  document.querySelector('[data-toggle="mode"]').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-mode]'); if (!btn) return;
    state.mode = btn.dataset.mode;
    document.querySelectorAll('[data-toggle="mode"] .seg__btn').forEach(
      (b) => b.classList.toggle('seg__btn--on', b === btn));
    document.querySelector('#single-panel').hidden = state.mode !== 'single';
    document.querySelector('#batch-panel').hidden = state.mode !== 'batch';
  });

  // 选择文件
  const extOk = (name) => name.toLowerCase().endsWith(COPY[state.dir].accept);
  dropzone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files[0]) setFile(fileInput.files[0]);
  });
  ['dragover', 'dragenter'].forEach((ev) => dropzone.addEventListener(ev, (e) => {
    e.preventDefault(); dropzone.classList.add('dropzone--over');
  }));
  ['dragleave', 'drop'].forEach((ev) => dropzone.addEventListener(ev, (e) => {
    e.preventDefault(); dropzone.classList.remove('dropzone--over');
  }));
  dropzone.addEventListener('drop', (e) => {
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) setFile(f);
  });
  function setFile(f) {
    if (!extOk(f.name)) { alert('请上传 ' + COPY[state.dir].accept + ' 文件'); return; }
    state.file = f;
    if (dropTitle) dropTitle.textContent = '已选择：' + f.name;
  }

  // 转换
  convertBtn.addEventListener('click', async () => {
    if (!state.file) { dropzone.classList.add('dropzone--over');
      setTimeout(() => dropzone.classList.remove('dropzone--over'), 600); return; }
    const fd = new FormData(); fd.append('file', state.file);
    convertBtn.disabled = true;
    try {
      const r = await fetch('/api/upload', { method: 'POST', body: fd });
      const body = await r.json();
      if (!body.success) { alert(body.message || '上传失败'); return; }
      const name = encodeURIComponent(body.filename);
      if (state.dir === 'x2c') { window.location = '/preview/' + name; }
      else { openSepModal(body.filename); }
    } catch (err) { alert('上传失败，请重试'); }
    finally { convertBtn.disabled = false; }
  });

  // CSV → XMind 分隔符弹窗（照原型 sep 逻辑）
  function openSepModal(filename) {
    const base = '/' + encodeURIComponent(filename) + '/to/xmind-from-csv';
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <div class="modal__title serif">选择标题分隔符</div>
        <div class="modal__divider"></div>
        <p style="font-size:13px;color:var(--text-2);margin:0 0 14px;">用例标题将按勾选的符号拆成 XMind 层级，任一符号都作为切分点。</p>
        <label class="modal__check"><input type="checkbox" class="sep-opt" value=" " checked><span>空格</span></label>
        <label class="modal__check"><input type="checkbox" class="sep-opt" value=">"><span>&gt; 大于号</span></label>
        <label class="modal__check"><input type="checkbox" class="sep-opt" value="-"><span>- 连字符</span></label>
        <label class="modal__check"><span>自定义</span><input type="text" id="sep-custom" maxlength="10" class="modal__input" style="width:160px;"></label>
        <p style="font-size:12px;color:var(--text-4);margin:10px 0 0;">不勾选任何符号则不拆分，每条用例直接挂在模块下。</p>
        <div class="modal__actions" style="margin-top:20px;">
          <button class="btn btn--outline" id="sep-cancel">取消</button>
          <button class="btn btn--ink" id="sep-confirm">下载</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    const close = () => overlay.remove();
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    overlay.querySelector('#sep-cancel').addEventListener('click', close);
    overlay.querySelector('#sep-confirm').addEventListener('click', () => {
      const seps = Array.from(overlay.querySelectorAll('.sep-opt:checked')).map((c) => c.value);
      const custom = overlay.querySelector('#sep-custom').value;
      if (custom) seps.push(custom);
      const url = seps.length === 0 ? base + '?flat=1'
        : base + '?' + seps.map((s) => 'sep=' + encodeURIComponent(s)).join('&');
      close(); window.location = url;
    });
  }

  applyDir();
});
```

- [ ] **Step 5: 运行冒烟测试 + 全量回归**

Run: `pytest tests/test_webtool.py -v && pytest -q`
Expected: 全部 passed。

- [ ] **Step 6: 提交**

```bash
git add webtool/templates/index.html webtool/static/css/convert.css webtool/static/js/upload.js tests/test_webtool.py
git commit -m "feat(webtool): 转换台 v2 改版（双向开关/上传/CSV分隔符/记录/占位）"
```

---

### Task 5: 用例预览（核心）— `preview.html` + `preview.css` + `preview.js`（渲染/体检/分页/导出）

**Files:**
- Modify: `webtool/templates/preview.html`（整页重写，XMind 主路径；CSV 适配在 Task 7）
- Create: `webtool/static/css/preview.css`
- Modify: `webtool/static/js/preview.js`（重写渲染层，复用既有数据流）
- Modify: `tests/test_webtool.py`（追加预览渲染冒烟测试）

**Interfaces:**
- Consumes: `theme.css`；`GET /api/templates`、`GET /api/preview/<file>/cases`、`GET /api/preview/<file>/empty-cells`（体检摘要）、`POST /api/export/<file>/{csv,xml}`。
- Produces: 全局对象 `PreviewApp`（沿用既有 `ColumnManager` 数据流函数名：`init/fetchPage/renderTable/renderPagination/doExport/saveCurrentTemplate/debounceSave/swapColumnOrder` 等），新增 `fetchHealth/renderHealth/priorityMeta/escapeHtml`。Task 6 在其上加编辑模式与弹窗。

像素参考：原型 PREVIEW SCREEN 段（约 192–346 行）。`max-width:1320px`。**保留现有默认列**，按列 `type` 套 v2 视觉。

- [ ] **Step 1: 写失败冒烟测试**

```python
def test_preview_renders_v2(client):
    name = _seed_upload(client, "preview_demo.xmind")
    resp = client.get(f"/preview/{name}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "用例体检" in html
    assert "preview.css" in html and "theme.css" in html
    assert 'id="case-table"' in html
```

Run: `pytest tests/test_webtool.py::test_preview_renders_v2 -v` → FAIL。

- [ ] **Step 2: 重写 `preview.html`**

骨架（XMind 主路径；`is_csv` 适配留 Task 7，用 `{% if not is_csv %}` 包裹体检/编辑/导出按钮，`{% if is_csv %}` 留下载 XMind 占位 + sep modal 钩子，Task 7 完成）：

```html
<!DOCTYPE html><html lang="zh-CN"><head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ name }} | XMind2Cases Preview</title>
  <link rel="shortcut icon" href="{{ url_for('static',filename='favicon.ico') }}" type="image/x-icon"/>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static',filename='css/theme.css') }}">
  <link rel="stylesheet" href="{{ url_for('static',filename='css/preview.css') }}">
</head>
<body data-screen="preview">
  <header class="topbar"><div class="topbar__inner"> ... brand ... </div></header>
  <main class="preview">
    <div class="pv-head">
      <div class="pv-title">
        <a class="pv-back" href="{{ url_for('index') }}"> ← </a>
        <div><h1 class="serif" id="pv-filename">{{ name }}</h1>
          <p class="pv-sub">用例预览 · 模版：<span id="pv-tpl-name">默认</span></p></div>
      </div>
      <div class="pv-actions">
        <button class="btn btn--outline" id="edit-toggle">编辑模式</button>
        <button class="btn btn--outline btn--disabled" id="diff-btn" title="暂未上线" disabled>版本对比</button>
        <button class="btn btn--csv export-btn" data-type="csv">导出 CSV</button>
        <button class="btn btn--xml export-btn" data-type="xml">导出 XML</button>
        <button class="btn btn--ink" id="tpl-settings-btn">模版设置</button>
      </div>
    </div>
    <div class="health" id="health"></div>
    <div class="edit-banner" id="edit-banner" hidden></div>
    <div class="case-card">
      <div class="x-scroll" style="overflow-x:auto;">
        <table class="case-table" id="case-table"><thead><tr></tr></thead><tbody></tbody></table>
      </div>
      <div class="pager" id="pagination-bar"></div>
    </div>
    <footer class="preview__footer">Powered by XMind2Cases · 本地优先的测试用例转换工具</footer>
  </main>
  <script>
    document.body.dataset.filename = "{{ name }}";
    document.body.dataset.total = "{{ total }}";
    document.body.dataset.isCsv = "{{ '1' if is_csv else '0' }}";
  </script>
  <script src="{{ url_for('static',filename='js/preview.js') }}"></script>
</body></html>
```

- [ ] **Step 3: 重写 `preview.js` 渲染层**

保留既有 `ColumnManager` 的数据流（`init` 拉模板/分页、`fetchPage`、`renderPagination` 逻辑、`doExport`、`openExportModal`、`saveCurrentTemplate`/`debounceSave`、拖拽 `handleDrag*`/`swapColumnOrder`），把渲染替换为 v2 markup，并把 `fetchEmptyCells` 升级为 `fetchHealth`。新增/替换的完整函数：

```javascript
const PRIORITY = {
  1: { label: 'P1', cls: 'p1' }, 2: { label: 'P2', cls: 'p2' },
  3: { label: 'P3', cls: 'p3' }, 4: { label: 'P4', cls: 'p4' },
};
function priorityMeta(importance) {
  const n = parseInt(importance, 10);
  return PRIORITY[n] || PRIORITY[4];
}

// 体检摘要（全量）：total + 优先级分布 + 空值
async function fetchHealth() {
  const tplId = this.currentTemplate && this.currentTemplate.id;
  const q = tplId ? `?template_id=${tplId}` : '';
  try {
    const r = await fetch(`/api/preview/${encodeURIComponent(this.filename)}/empty-cells${q}`);
    const res = await r.json();
    if (res.success) {
      this.emptyCells = res.data.empty_cells || [];
      this.total = res.data.total != null ? res.data.total : this.total;
      this.priorityCounts = res.data.priority_counts || { '1':0,'2':0,'3':0,'4':0 };
    }
  } catch (e) { this.emptyCells = []; this.priorityCounts = { '1':0,'2':0,'3':0,'4':0 }; }
}

function renderHealth() {
  const el = document.getElementById('health'); if (!el) return;
  const pc = this.priorityCounts || { '1':0,'2':0,'3':0,'4':0 };
  const empty = (this.emptyCells || []).length;
  const dots = [['1','#B5503A'],['2','#C9A24A'],['3','#7E9166'],['4','#7A7868']]
    .filter(([k]) => pc[k] > 0)
    .map(([k, c]) => `<span class="health__pri"><span class="pri-dot" style="background:${c}"></span>${priorityMeta(k).label} · ${pc[k]}</span>`)
    .join('');
  el.innerHTML = `
    <div class="health__brand"><span class="health__icon">✓</span>
      <div><div class="health__t">用例体检</div><div class="health__s">导出前自动检查质量</div></div></div>
    <span class="health__div"></span>
    <div class="health__count"><span class="serif">${this.total}</span> 条用例</div>
    ${empty > 0 ? `<div class="health__warn">⚠ ${empty} 处待补充</div>` : ''}
    <div class="health__pris">优先级 ${dots}</div>`;
}

// 表头 + 表体（按列 type 套 v2 视觉；编辑态控件 Task 6 接管）
function renderTable() {
  const table = document.getElementById('case-table'); if (!table) return;
  const cols = [...((this.currentTemplate && this.currentTemplate.columns) || [])]
    .sort((a, b) => (a.order || 0) - (b.order || 0));
  const headerColor = (this.currentTemplate && this.currentTemplate.header_color) || '#FAF8F2';
  const start = (this.page - 1) * this.pageSize;
  const emptySet = new Set((this.emptyCells || []).map((c) => `${c.colId}:${c.rowIndex}`));
  const edit = !!this.editMode;

  const thead = table.querySelector('thead tr');
  thead.innerHTML =
    `<th class="col-th idx-th" style="background:${headerColor}">序号</th>` +
    cols.map((col) => `
      <th class="col-th" data-col-id="${this.escapeHtml(col.id)}" ${edit ? 'draggable="true"' : ''} style="background:${headerColor}">
        <div class="col-th__inner">
          ${edit ? '<span class="drag-handle" title="拖动调整列顺序">⠿</span>' : ''}
          <span class="col-title">${this.escapeHtml(col.name)}</span>
          ${edit && col.type !== 'index' ? `
            <span class="col-actions">
              <button class="edit-col" title="编辑列">✎</button>
              <button class="add-col" title="新增列">＋</button>
              ${col.is_custom ? '<button class="del-col" title="删除列">🗑</button>' : ''}
            </span>` : ''}
        </div>
      </th>`).join('') +
    (edit ? '<th class="col-th op-th">操作</th>' : '');

  const tbody = table.querySelector('tbody');
  tbody.innerHTML = this.testcases.map((tc, i) => {
    const gi = start + i;
    return `<tr>
      <td class="idx-cell"><span class="serif">${gi + 1}</span></td>
      ${cols.map((col) => `<td data-col-id="${this.escapeHtml(col.id)}" data-row="${gi}">${this.renderCell(tc, col, gi, emptySet)}</td>`).join('')}
      ${edit ? `<td class="op-cell"><button class="del-row btn--disabled" title="暂未上线" disabled>🗑</button></td>` : ''}
    </tr>`;
  }).join('');
}

function renderCell(tc, col, rowIndex, emptySet) {
  if (col.type === 'index') return '';
  if (col.id === 'importance' || col.type === 'priority') {
    const m = priorityMeta(tc.importance || 2);
    return `<span class="pri-badge pri-badge--${m.cls}">${m.label}</span>`;
  }
  if (col.id === 'steps' || col.type === 'steps') {
    const steps = tc.steps || [];
    return `<ol class="steps-list">${steps.map((s, i) =>
      `<li><span class="step-n">${i + 1}</span>${this.escapeHtml(s.actions || '')}</li>`).join('')}</ol>`;
  }
  if (col.id === 'expectedresults') {
    const steps = tc.steps || [];
    return `<ol class="steps-list steps-list--exp">${steps.map((s, i) =>
      `<li><span class="step-n">${i + 1}</span>${this.escapeHtml(s.expectedresults || '')}</li>`).join('')}</ol>`;
  }
  const raw = this.getColumnValueRaw(tc, col, rowIndex);   // 复用既有取值
  const isEmpty = emptySet.has(`${col.id}:${rowIndex}`);
  if (isEmpty && col.empty_check) {
    return `<span class="empty-chip">⚠ 待补充</span>`;
  }
  const tooLong = col.id === 'name' && (tc.name || '').length > 100;
  return `<span class="cell-text${tooLong ? ' cell-text--long' : ''}">${this.escapeHtml(raw)}</span>${
    tooLong ? '<span class="cell-warn">标题过长</span>' : ''}`;
}
```

`init` 末尾改为：先 `await this.fetchHealth()`，再 `renderHealth`、`fetchPage`（`fetchPage` 内部页变化后调用 `renderTable`+`renderPagination`，不重复拉体检——体检全量只在 init/模板变化时拉）。`renderPagination` 复用既有逻辑，输出 `.pager`/`.pager__btn` markup（照原型分页 330–341 行）。`doExport`/`openExportModal` 复用既有，弹窗用 `theme.css` 的 `.modal*` 重绘。SVG 图标用原型对应图标替换上面占位字符（✓/⚠/⠿/✎/＋/🗑/←）。

- [ ] **Step 4: 写 `preview.css`**

把原型 PREVIEW 段内联样式翻译成类：`.preview/.pv-head/.pv-title/.pv-back/.pv-sub/.pv-actions/.health*/.pri-dot/.case-card/.case-table/.col-th/.drag-handle/.col-actions/.idx-cell/.pri-badge(--p1..p4)/.steps-list/.step-n/.empty-chip/.cell-text(--long)/.cell-warn/.pager/.pager__btn`。优先级 badge 颜色用 `--p1..p4` 变量。`.col-th.drag-over{ box-shadow:inset 3px 0 0 var(--accent); }`。

- [ ] **Step 5: 运行冒烟测试 + 回归**

Run: `pytest tests/test_webtool.py -v && pytest -q`
Expected: passed。

- [ ] **Step 6: 提交**

```bash
git add webtool/templates/preview.html webtool/static/css/preview.css webtool/static/js/preview.js tests/test_webtool.py
git commit -m "feat(webtool): 用例预览 v2 改版核心（体检/表格/分页/导出）"
```

---

### Task 6: 用例预览 — 编辑模式（仅列管理）+ 列弹窗 + 模版设置弹窗 + 占位

**Files:**
- Modify: `webtool/static/js/preview.js`（加编辑模式与弹窗）
- Modify: `webtool/static/css/preview.css`（编辑态/banner/弹窗补充）

**Interfaces:**
- Consumes: Task 5 的 `PreviewApp`/`renderTable`/`debounceSave`/`saveCurrentTemplate`；`GET/POST/PUT/DELETE /api/templates`。
- Produces: 编辑模式 toggle 行为；列弹窗、模版设置/编辑模版弹窗（v2 样式）。

- [ ] **Step 1: 编辑模式 toggle**

`#edit-toggle` 切 `this.editMode`，更新按钮文案（编辑模式 ↔ 完成编辑）与 `--ink`/`--outline` 态，显隐 `#edit-banner`（文案：「编辑模式：拖动表头可调列顺序、✎ 改列、＋ 加列；单元格内容编辑与增删行将在后续版本开放」——如实说明 Phase 1 范围），并 `renderTable()`（重渲染出/收起拖拽手柄与列操作图标、操作列）。

- [ ] **Step 2: 列管理事件（复用既有逻辑）**

`thead` 绑定 dragstart/dragover/drop/dragend（复用既有 `handleDrag*` + `swapColumnOrder` + `debounceSave`）；点击 `.edit-col`→`openColumnModal('edit', colId)`、`.add-col`→`openColumnModal('add', colId)`、`.del-col`→`deleteColumn(colId)`、`.col-title`（非按钮）→ 内联改名（复用 `editColumnTitleInline`）。`tbody` 自定义列单元格双击编辑（复用 `editCell`，写 `column.values`，`debounceSave`，保留）。`.del-row`/优先级 badge 不绑定（占位禁用）。

- [ ] **Step 3: 列弹窗（新增列/编辑列，v2）**

`openColumnModal(mode, colId)` 用 `.modal*` 类渲染：列名称、默认值、两个复选（富文本换行处理 / 空值校验处理，文案照原型 420/425 行），确定 → 复用既有 `addColumn`/`updateColumn`（参数：name, default_value, rich_text_break, empty_check[, afterColId]）→ `debounceSave`。对照原型 COLUMN MODAL（407–433 行）。

- [ ] **Step 4: 模版设置 + 编辑模版弹窗（v2）**

`#tpl-settings-btn` → `openTemplateSettingsModal`（模板列表 + 新建/编辑/删除/应用，复用既有 API 调用）；编辑模版弹窗 `openTemplateEditModal`（模板名、标题行字段展开编辑/增删/恢复默认、标题行颜色色板 `PAL` + hex）。色板 `PAL = ['#FAF8F2','#FEF2F2','#F3F4F6','#DBEAFE','#DCFCE7','#FEF9C3','#FDE68A','#FCE7F3','#EDE9FE','#F0E4F5']`，选中 `.swatch--on`。保存 → `PUT /api/templates/<id>` → 更新 `pv-tpl-name`、`renderTable`、`fetchHealth`+`renderHealth`。对照原型 TEMPLATE MODAL（435–485 行）。逻辑可直接移植现 `preview.js` 同名函数，仅换 markup/类。

- [ ] **Step 5: CSS 补充**

`.edit-banner`、`.col-actions button`、`.del-row`、`.modal__check` 选中态、`.tpl-field`（可折叠字段行）、`.swatch` 等。

- [ ] **Step 6: 验证（渲染冒烟仍过 + 手动走查）**

Run: `pytest tests/test_webtool.py -v`
Expected: passed。手动走查：编辑模式开/关、列拖拽、改列名、增删自定义列、模版增删改应用、导出。（不截图，除非用户要求。）

- [ ] **Step 7: 提交**

```bash
git add webtool/static/js/preview.js webtool/static/css/preview.css
git commit -m "feat(webtool): 用例预览编辑模式（列管理）与模版/列弹窗 v2"
```

---

### Task 7: CSV 预览适配 + 退场旧 CSS + 回归

**Files:**
- Modify: `webtool/templates/preview.html`（CSV 分支）
- Modify: `webtool/static/js/preview.js`（CSV 早退分支）
- Delete: `webtool/static/css/{pure-min.css,style.css,custom.css}` + 旧 `preview.css` 已被 Task 5 覆盖
- Modify: `tests/test_webtool.py`（CSV 预览冒烟）

**Interfaces:**
- Consumes: 既有 `download_xmind_from_csv` 路由 + Task 4 的 sep 弹窗逻辑。
- Produces: CSV 文件预览页（下载 XMind + sep modal，无体检/编辑/导出 CSV/XML/版本对比）。

- [ ] **Step 1: 写 CSV 预览冒烟测试**

```python
def _seed_csv(client, name="zentao.csv"):
    rows = ("用例编号,所属产品,所属模块,用例标题,前置条件,步骤,预期,优先级,用例类型\n"
            "TC001,产品A,/模块1,登录,已注册,1. 输入,1. 成功,1,功能测试\n")
    client.post("/api/upload",
                data={"file": (io.BytesIO(rows.encode("utf-8")), name)},
                content_type="multipart/form-data")
    return name

def test_preview_csv_shows_download_xmind(client):
    name = _seed_csv(client)
    html = client.get(f"/preview/{name}").get_data(as_text=True)
    assert "下载 XMind" in html
    assert "用例体检" not in html  # CSV 不显示体检
```

Run → FAIL。

- [ ] **Step 2: preview.html CSV 分支**

用 `{% if is_csv %}` 在 `.pv-actions` 渲染单个「下载 XMind」按钮（`id="csv-download-btn"` + `data-download-base="{{ url_for('download_xmind_from_csv', filename=name) }}"`），隐藏体检/编辑/导出/版本对比；`{% else %}` 保留 Task 5 的完整按钮组。表格仍渲染（cases API 支持 CSV）。

- [ ] **Step 3: preview.js CSV 适配**

`init` 开头读 `document.body.dataset.isCsv`；为 `'1'` 时：不渲染体检（`#health` 隐藏）、不绑定编辑/导出模板逻辑；为 `#csv-download-btn` 绑定 Task 4 的 `openSepModal`（按 `data-download-base` 复用）。表格渲染照常（优先级/步骤/文本，按 cases API 返回的 CSV dict）。

- [ ] **Step 4: 退场旧 CSS + 校验无残留引用**

Run:
```bash
grep -rn "pure-min.css\|style.css\|custom.css" webtool/templates/ || echo "no refs"
git rm webtool/static/css/pure-min.css webtool/static/css/style.css webtool/static/css/custom.css
```
Expected: `no refs` 后再删除（若 `guide/` 等有独立引用则保留对应文件）。

- [ ] **Step 5: 全量回归**

Run: `pytest -q`
Expected: 全部 passed（含既有 `test_e2e.py`/`test_utils.py`/`test_integration.py`）。

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "feat(webtool): CSV 预览适配 + 退场旧 slate 主题 CSS"
```

---

## Self-Review（对照 spec）

**1. Spec coverage**

- §4 设计系统 → Task 3（theme.css）✓
- §5 转换台（顶栏/Hero/方向·模式开关/flow/dropzone/输出 chip/CTA/统计占位/记录/页脚 + `/api/upload` + XMind→preview / CSV→sep 下载）→ Task 1 + Task 4 ✓
- §6 用例预览（页头/体检 bar/表格按 type/分页/导出/编辑模式=仅列管理/CSV 适配/占位）→ Task 5 + Task 6 + Task 7 ✓
- §6.2 体检优先级分布需全量 → Task 2（empty-cells 体检摘要）✓
- §7 列弹窗 + 模版设置弹窗 → Task 6 ✓
- §8 后端仅 `/api/upload` —— **偏差记录**：为让体检 bar 用真实全量优先级分布，额外扩了既有 `empty-cells` 端点响应（Task 2），非新增路由、非新能力，属「体检接真数据」的最小实现。已在交付时向用户标注。
- §9 优先级映射 → Global Constraints + `priorityMeta` ✓
- §10 测试 → 每后端任务 TDD + 每前端任务 Flask 冒烟 + Task 7 全量回归 ✓
- §3 占位（批量/统计/版本对比/编辑持久化）→ Task 4 batch-empty + stat-placeholder、Task 5 diff 禁用、Task 6 banner 文案 + del-row/优先级禁用 ✓

**2. Placeholder scan**：计划内「占位/暂未上线」为设计要求的 UI 文案，非计划缺口；无 TBD/TODO/“类似 TaskN”。✓

**3. Type consistency**：`priorityMeta(importance)→{label,cls}`、`fetchHealth` 写 `this.{emptyCells,total,priorityCounts}`、`renderCell(tc,col,rowIndex,emptySet)`、JSON 契约 `{success,filename}` / `{empty_cells,total,priority_counts}` 全计划一致；CSS 类名与「CSS 类契约」一致。✓

唯一对 spec 的偏差（Task 2 扩端点）已记录并将向用户说明。
