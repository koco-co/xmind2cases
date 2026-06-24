# XMind2Cases v2 前端重设计 — Phase 1 设计

- 日期：2026-06-24
- 来源：Claude Design handoff（`XMind2Cases v2.dc.html`），warm cream / terracotta 设计语言
- 状态：已与用户确认范围与关键决策，待用户复核 spec

---

## 1. 背景与现状

`xmind2cases` 是一个 Flask Web 工具，做 XMind 思维导图 ↔ 测试用例（禅道 CSV / TestLink XML）双向转换。当前前端：

- 模板引擎 Jinja（`webtool/templates/index.html`、`preview.html`）
- 原生 JS（`upload.js`、`preview.js`），Tailwind CDN + 自写 CSS（`style.css`、`preview.css`、`custom.css`、`pure-min.css`）
- 主题为 slate/indigo 冷色

**关键架构事实：当前应用是无状态的。** 每次预览 / 导出都重新解析磁盘上的 XMind 文件；只有「模板 / 列配置」被持久化（表 `column_preferences` = `ColumnTemplate`，以及 `app_settings`、`records`）。用例内容本身从不入库。

现有后端能力（Phase 1 复用，不改）：

| 路由 | 作用 |
|---|---|
| `POST /` | 上传文件 → 保存 → 单文件成功时重定向 `/preview/<file>` |
| `GET /preview/<file>` | 渲染预览页（XMind 或 CSV 都支持） |
| `GET /api/preview/<file>/cases` | 分页取用例（page/page_size，size ∈ {10,20,50,100}） |
| `GET /api/preview/<file>/empty-cells?template_id=` | 全局空值检测（仅 XMind） |
| `GET/POST/PUT/DELETE /api/templates[/<id>]` | 模板增删改查 + 上次导出模板 |
| `POST /api/export/<file>/{csv,xml}` | 按模板导出（body: template_id） |
| `GET /<file>/to/xmind-from-csv?sep=&flat=` | CSV → XMind（分隔符拆层级） |
| `GET /<file>/to/{zentao,testlink}` | XMind → CSV / XML 直接下载 |
| `GET /uploads/<file>`、`GET /delete/<file>/<id>` | 取文件、删除记录 |

数据模型（`webtool/models.py`，Phase 1 不改）：`Record`、`ColumnTemplate`（`columns_json` + `header_color`）、`AppSetting`。`DEFAULT_COLUMNS` = `[所属模块, 用例标题, 前置条件, 步骤, 预期, 优先级]`。`importance` 取值 1=高 / 2=中 / 3=低（范围 1–4，缺省 2），由 XMind `priority-N` marker 得到。

---

## 2. 整体范围与分阶段（决策记录）

新版设计带来 **1 个视觉改版 + 4 个现有后端完全没有的新能力**。用户确认：4 个新能力都要做成真实可用，未实现的部分按设计还原 UI 但标「暂未上线」、不放假数据；**分阶段推进，先做 Phase 1**。

| # | 工作流 | 新后端 | 依赖 |
|---|---|---|---|
| **1（本 spec）** | 转换台 + 用例预览视觉改版，接现有后端 | 否（仅 1 个小 `/api/upload`） | — |
| 2 | 有状态用例存储 + 编辑持久化（编辑写回、影响导出） | 是（基石） | 1 |
| 3 | 版本对比 / Diff（快照 + diff 引擎 + 页面） | 是 | 2 |
| 4 | 批量转换队列（多文件上传 + 状态流转） | 是 | 1 |
| 5 | 转换台统计数字（本月文件 / 生成用例 / 体检通过率） | 是 | 2 |

构建顺序：1 → 2 → 3 → 5，4（批量）相对独立，择机插入。每阶段单独 spec → plan → 实现。

---

## 3. Phase 1 目标与非目标

**目标**：把「转换台」与「用例预览」两屏完整还原成 v2 warm 设计语言，并把**今天已经能工作的功能全部接好**：上传、双向转换、最近记录、模板/列管理、分页、用例体检（空值检测）、导出 CSV/XML、CSV→XMind（分隔符）。

**非目标（本阶段不做，按占位处理）**：

- 批量转换（队列）→ 「批量转换」模式 tab 渲染但标「暂未上线」
- 转换台统计数字 → 卡片渲染但显示占位（`—` + 「暂未上线」），不放假数 128/2,341/96%
- 版本对比 → 预览页「版本对比」按钮渲染但禁用 / 「暂未上线」
- 用例内容编辑持久化 → 见 §6 编辑模式：Phase 1 编辑模式只开放「已可持久化的列管理」；单元格内容 / 优先级下拉 / 增删行标「暂未上线」，留给 Phase 2

---

## 4. 技术与设计系统

沿用 Flask + Jinja + 原生 JS。两张页面**弃用 Tailwind CDN 与旧 slate 主题**，改为自写、CSS 变量驱动的设计系统（v2 配色与字体具体且统一，自写 CSS 比 Tailwind 任意值更贴、更易维护）。

**文件结构（建议）**

- `webtool/static/css/theme.css` — 设计 tokens（CSS 变量）、base、字体、共享组件（顶栏、按钮、chip、modal、滚动条、表单聚焦态）
- `webtool/static/css/convert.css` — 转换台
- `webtool/static/css/preview.css` — 用例预览（重写）
- `webtool/templates/index.html`（转换台）、`preview.html`（用例预览）— 重写
- `webtool/static/js/upload.js`（转换台交互）、`preview.js`（预览交互）— 重写
- 退场：`pure-min.css`、`style.css`、旧 `preview.css`、`custom.css`（确认无其它引用后删除）

**字体**：`Newsreader`（serif，400/500/600 + italic 400）用于标题 / logo / 大数字；`Noto Sans SC`（400/500/700）正文。Google Fonts 引入（与 v2 一致）。

**设计 tokens（CSS 变量）**

```
--bg:#F0EEE6;  --surface:#FFFFFF;
--border:#E7E3D8;  --border-2:#E4E0D5;  --divider:#EDE9DF; --row-divider:#F1EDE3;
--text:#2B2A27;  --text-strong:#22211F;  --text-2:#6B6A63;  --text-3:#8A887E;  --text-4:#A4A299;
--accent:#C96442;        /* 主品牌（logo 底、聚焦） */
--accent-ink:#A4623F;    /* 链接 / hover 文字 */
--ink-btn:#262624;  --ink-btn-hover:#3A3835;  --on-ink:#F5F2EC;
--toggle-track:#F3EFE6;  --field-bg:#FBFAF6;
--selection:#E7D3C7;  --scrollbar:#DBD6C9;
/* 优先级（badge：前景/背景） */
--p-high:#B5503A / #F6E7E2;  --p-mid:#9A7A2E / #F6EFDD;  --p-low:#5E7355 / #EBF0E6;  --p-other:#7A7868 / #F0EDE4;
/* 体检图例点 */ --dot-p0:#B5503A; --dot-p1:#C9A24A; --dot-p2:#7E9166;
/* 待补充 / 警示 */ --warn-fg:#9A7A2E; --warn-bg:#F6EFDD; --warn-border:#E6D9B6; --warn-dash:#E2CF94;
/* 体检通过图标 */ --ok-fg:#5E7355; --ok-bg:#EFF3E9;
/* 批量队列状态（Phase 4 用，先定义） done/running/queued/error */
```

圆角：卡片 14–18px、按钮 8–11px、chip 6–9px。聚焦态：`border-color:var(--accent)` + `box-shadow:0 0 0 3px rgba(201,100,66,.12)`。表头模板色板（模板 modal）：`['#FAF8F2','#FEF2F2','#F3F4F6','#DBEAFE','#DCFCE7','#FEF9C3','#FDE68A','#FCE7F3','#EDE9FE','#F0E4F5']`（库内既有模板的 `header_color` 默认 `#fef2f2` 仍是有效色板项，不迁移）。

---

## 5. 转换台（`index.html` + `upload.js`）

布局 `max-width:780px` 居中。区块自上而下：

1. **顶栏（两屏共享）**：logo（terracotta 圆角 `X` + 「XMind2Cases」+ 副标题「思维导图 · 测试用例 双向转换」，点击回转换台）；右侧 使用指南（→ `static/guide/index.html`）/ 反馈问题（→ GitHub issues）/ GitHub（→ 仓库）。
2. **Hero**：标题「一处转换，两个方向」+ 副文案。
3. **转换卡片**：
   - **方向 toggle**：`XMind → 用例` / `CSV → XMind`（客户端状态，驱动 flow-viz 标签、dropzone 文案、输出 chip、CTA）。
   - **模式 toggle**：`单文件` / `批量转换`。批量 = 占位（点了切到「暂未上线」空状态，不渲染假队列）。
   - **flow-viz**：源 → 目标图标 + 文案随方向变化。
   - **dropzone**：按方向限制后缀（XMind→用例 收 `.xmind`；CSV→XMind 收 `.csv`），点击或拖拽。
   - **单文件 / 输出格式 chip**：XMind→用例 显示「禅道 CSV」「TestLink XML」；CSV→XMind 显示「XMind 思维导图 (.xmind)」（信息性）。
   - **CTA**：「转换为测试用例」/「转换为 XMind」。
4. **统计卡片** ×3：占位（`—` + 「暂未上线」），Phase 5 接真值。
5. **最近转换记录**：`get_records()`；每行图标沿用今天的条件逻辑——CSV 记录显示「转换为 XMind」+ 预览 + 删除；XMind 记录显示 下载 XMind / 导出 CSV / 导出 XML / 预览 / 删除（路由不变）。
6. **页脚**。

**上传 / 转换流程**

为让两个方向都在转换台内自洽且与 mock 一致，新增**唯一一个小后端**：

- `POST /api/upload`（multipart，单文件）→ 复用 `save_file()` 保存 → 返回 JSON `{ success, filename }`（沿用既有去重/扩展名校验；非法返回 `{success:false, message}`）。

CTA 行为：

- **XMind → 用例（单文件）**：`/api/upload` 上传 `.xmind` → 成功后 `window.location = /preview/<filename>`。（保留 `<form>` 原生 POST 作为无 JS 回退：`POST /` 本就会重定向到 preview。）
- **CSV → XMind（单文件）**：`/api/upload` 上传 `.csv` → 弹既有**分隔符 modal**（空格 / `>` / `-` / 自定义 / flat）→ `window.location = /<filename>/to/xmind-from-csv?sep=...|flat=1` 触发下载。

不引入任何用例级新后端；`/api/upload` 仅为上传 plumbing。

---

## 6. 用例预览（`preview.html` + `preview.js`）

布局 `max-width:1320px`。

1. **页头**：返回箭头（→ 转换台）；文件名；「用例预览 · 模版：{当前模板名}」；右侧按钮：
   - **编辑模式** toggle（见下）
   - **版本对比**：渲染但禁用 + 「暂未上线」（Phase 3）
   - **导出 CSV** / **导出 XML**：打开既有「选择导出模板」弹窗 → `POST /api/export/<file>/{csv,xml}` 下载（逻辑不变，重绘样式）
   - **模版设置**：打开模板管理弹窗（见 §7）
2. **用例体检 bar**：体检图标；`{total} 条用例`；`{emptyCount} 处待补充`（来自 `empty-cells` API，仅 XMind）；优先级分布——按真实 `importance` 计数，**自适应**显示存在的等级（P1=高/红、P2=中/金、P3=低/绿、P4/其它=灰），用 v2 配色。标签沿用 `P{importance}`（与现状一致，导出不受影响）。
3. **编辑模式 banner**（编辑模式开启时）：操作提示（按 Phase 1 实际可用项措辞）。
4. **表格**（按列 **type** 套用 v2 视觉，不改列数据模型）：
   - 固定首列 **序号**（Newsreader 数字）。
   - 列由当前模板驱动（`ColumnTemplate.columns`，保留现有默认列：`所属模块/用例标题/前置条件/步骤/预期/优先级`）。
   - **优先级列**：v2 彩色 badge（按 `importance` → 颜色映射）。
   - **步骤列**：带序号小方块的有序列表（`steps[].actions`）。
   - **文本列**（标题/前置/预期/自定义）：普通文本；命中 `empty_check` 空值时显示 v2「待补充」chip（dashed 警示）。标题过长（>100）仍标红提示（沿用现状）。
   - 表头：可拖拽排序 + 拖拽手柄 + 编辑列 / 新增列图标（见编辑模式）+ 模板 `header_color` 底色。
5. **分页**：`/api/preview/<file>/cases`，每页 10/20/50/100，首/上/下/末页（重绘 v2 样式，逻辑不变）。
6. **CSV 文件预览适配**：v2 预览以 XMind 用例为中心。CSV 文件（`is_csv`）预览时，页头把「导出 CSV/XML / 版本对比 / 编辑模式」替换为单个 **下载 XMind**（走既有分隔符 modal + `/<file>/to/xmind-from-csv`），体检/优先级/编辑相关隐藏；表格仍渲染解析出的用例。保持现有 CSV 能力不丢。
7. **页脚**。

**编辑模式（Phase 1 范围 = 仅列管理，已确认）**

编辑模式 toggle 控制「列管理」可见性（今天这些操作已经能通过模板持久化）：

- 列拖拽排序、表头内联改列名、新增列 / 编辑列（弹 §7 列弹窗）、删除自定义列、表头底色（经模版设置）、空值校验开关；改动经 `debounceSave` → `PUT /api/templates/<id>` 持久化。

**标「暂未上线」、留给 Phase 2 的**：单元格内容内联编辑、优先级下拉 `<select>`、新增/删除用例**行**——这些需要用例存储层。编辑模式下这些控件以禁用 / 提示态呈现，不可改 parsed 用例内容。（既有「自定义列单元格双击编辑」属于模板 `values`，可持久化，保留。）

---

## 7. 弹窗

1. **列弹窗（新增列 / 编辑列）**：列名称、默认值、「富文本换行处理」「空值校验处理」两个复选项；确定 → 改当前模板列配置 → `debounceSave`。对应既有 `addColumn/updateColumn/showModal`，重绘成 v2 样式。
2. **模版设置 / 编辑模版**：模板名称、标题行字段（可展开改名 / 改默认值 / 删除自定义字段 / 新增字段 / 恢复默认）、标题行颜色（色板 + hex）。对应既有模板管理弹窗群（`openTemplateSettingsModal`/`openTemplateEditModal`），接 `GET/POST/PUT/DELETE /api/templates`，重绘成 v2 样式。

弹窗交互：遮罩点击关闭、内容区 `stopPropagation`、聚焦态用 accent 环。

---

## 8. 后端改动汇总

- **新增**：`POST /api/upload`（保存单文件 + 返回 `{success, filename}`，复用 `save_file()`）。
- **扩展**：`GET /api/preview/<file>/empty-cells` 响应额外返回 `total` 与 `priority_counts`（`{"1".."4"}`→int），用于体检 bar 的全量优先级分布（全量解析本就发生，非新路由、非新能力）。`empty_cells` 行为保持不变，向后兼容。
- **其余全部复用**现有路由，**0 改动**。`models.py` 不改。

---

## 9. 优先级颜色映射

| importance | 标签 | 前景 / 背景 |
|---|---|---|
| 1（高） | P1 | `#B5503A` / `#F6E7E2` |
| 2（中） | P2 | `#9A7A2E` / `#F6EFDD` |
| 3（低） | P3 | `#5E7355` / `#EBF0E6` |
| 4 / 其它 | P4 | `#7A7868` / `#F0EDE4` |

体检 bar 的图例点用 v2 三色（`#B5503A/#C9A24A/#7E9166`），分布计数自适应真实数据存在的等级。

---

## 10. 测试策略

- **后端**：为 `POST /api/upload` 加 pytest（合法 xmind/csv 返回 filename；空文件名 / 非法后缀返回失败；同名去重）。现有 `tests/test_e2e.py` 等保持通过（既有路由未改）。
- **前端 / 渲染**：保证 `index.html`、`preview.html` 在有 / 无记录、XMind / CSV、空值有 / 无、分页边界下正确渲染；导出 / 分隔符 / 模板 CRUD 流程手动走查（README 要求不主动截图，除非用户要求）。
- **回归基线**：导出 CSV/XML 字节级不变（列模型与导出逻辑未改）；CSV→XMind 分隔符行为不变。

---

## 11. 风险与未决

- v2 mock 的列集（优先级在前、无所属模块）与库内既有「默认」模板不同——已确认**保留现有默认列**，视觉样式按列 type 套用，不迁移数据。
- 编辑模式在 Phase 1 是「半张能力」（只列管理），banner 文案需如实说明，避免用户误以为能改用例内容。
- 弃用 Tailwind 后需确认无其它页面依赖被删 CSS（`guide/index.html` 独立，不受影响）。
- 无阻塞性未决问题。

---

## 12. 交付物（Phase 1）

- `theme.css` + `convert.css` + `preview.css`（新/重写）
- `index.html`、`preview.html`（重写）
- `upload.js`、`preview.js`（重写）
- `application.py` 新增 `POST /api/upload` + 其 pytest
- 退场旧 CSS（确认无引用后）
