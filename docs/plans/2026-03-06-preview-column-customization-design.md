# 预览界面列自定义功能设计

## 概述

为 XMind2Cases 预览界面增加列自定义功能，支持多套偏好配置，用户可以自由调整列顺序、编辑列名、新增/删除列，并按选定偏好导出 CSV/XML。

---

## 功能需求

### 核心功能

| 功能 | 描述 |
|------|------|
| **偏好管理** | 创建、编辑、删除、切换多套偏好 |
| **偏好选择** | 预览和导出时可选择不同偏好 |
| 列名编辑 | 弹窗编辑列名 + 默认值 |
| 列拖拽排序 | 拖拽列标题调整顺序 |
| 新增自定义列 | 弹窗设置列名 + 默认值 |
| 删除列 | 任何列可删除（除序号列） |
| 编辑单元格 | 双击自定义列单元格编辑内容 |
| 自动保存 | 变更后防抖自动保存到 SQLite |
| 导出 CSV/XML | 按选定偏好导出，不含序号 |

---

## 技术方案

### 方案选择

**方案 A：纯前端实现**

- 前端使用原生 JS + HTML5 Drag & Drop API 实现拖拽
- 偏好设置通过 API 存储到 SQLite
- 导出时前端将列配置和数据一起提交给后端

### 依赖更新 (pyproject.toml)

```toml
dependencies = [
    "xmindparser>=0.1.0",
    "flask>=3.0.0",
    "flask-sqlalchemy>=3.0.0",  # 新增
    "arrow>=1.0.0",
    "click>=8.0.0",
]
```

---

## 数据库设计

### 使用 Flask-SQLAlchemy ORM

### 模型定义 (webtool/models.py)

```python
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Record(db.Model):
    """上传文件记录"""
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(500), nullable=False)
    create_on = db.Column(db.String(50), nullable=False)
    note = db.Column(db.Text)
    is_deleted = db.Column(db.Integer, default=0)


class ColumnPreference(db.Model):
    """列偏好配置"""
    __tablename__ = 'column_preferences'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    columns_json = db.Column(db.Text, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 默认配置

### 默认偏好列配置（6列）

| 序号 | 列名称 | 字段 id | 数据来源 |
|------|--------|---------|----------|
| 1 | 所属模块 | suite | test.suite |
| 2 | 用例标题 | name | test.name |
| 3 | 前置条件 | preconditions | test.preconditions |
| 4 | 步骤 | steps | test.steps[].actions |
| 5 | 预期 | expectedresults | test.steps[].expectedresults |
| 6 | 优先级 | importance | test.importance |

### columns_json 默认结构

```json
[
  {"id": "suite", "name": "所属模块", "visible": true, "order": 1, "is_custom": false},
  {"id": "name", "name": "用例标题", "visible": true, "order": 2, "is_custom": false},
  {"id": "preconditions", "name": "前置条件", "visible": true, "order": 3, "is_custom": false},
  {"id": "steps", "name": "步骤", "visible": true, "order": 4, "is_custom": false},
  {"id": "expectedresults", "name": "预期", "visible": true, "order": 5, "is_custom": false},
  {"id": "importance", "name": "优先级", "visible": true, "order": 6, "is_custom": false}
]
```

### 列配置字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 列唯一标识（原始列用字段名，自定义列用 `custom_N`） |
| name | string | 显示名称（可编辑） |
| visible | boolean | 是否显示 |
| order | int | 显示顺序 |
| is_custom | boolean | 是否为自定义列 |
| default_value | string | 默认值（可选，所有行填充此值） |
| values | object | 自定义列的单元格数据（key 为行号，value 为单元格值） |

---

## 前端设计

### 表头结构

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 序号 │ 所属模块 ▼ │ 用例标题 ▼ │ ... │ 未命名字段 ▼ │ + 新增列 │
│      │ [✏️][🗑️]   │ [✏️][🗑️]   │     │  [✏️][🗑️]    │          │
└─────────────────────────────────────────────────────────────────────────┘
```

- 每列标题右侧有 **拖拽手柄 (⋮⋮)** 用于拖拽排序
- 悬停时显示 **编辑 (✏️)** 和 **删除 (🗑️)** 按钮
- 最右侧有 **"+ 新增列"** 按钮

### 偏好管理界面

顶部操作栏新增偏好选择器：

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ← 文件名.xmind                          [偏好: 默认 ▼] [+ 新建] [⚙️]   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 交互行为

| 操作 | 交互方式 |
|------|----------|
| 编辑列名 | 点击 ✏️ → 弹窗编辑列名和默认值 |
| 删除列 | 点击 🗑️ → 弹出确认 → 删除列并保存 |
| 拖拽排序 | 拖拽 ⋮⋮ 到目标位置 → 释放后保存 |
| 新增列 | 点击 "+ 新增列" → 弹窗设置列名和默认值 |
| 编辑单元格 | 双击自定义列单元格 → 变为输入框 → 回车/失焦保存 |

### 新增/编辑列弹窗

```
┌─────────────────────────────┐
│      新增列                 │
├─────────────────────────────┤
│  列名称：[未命名字段    ]   │
│                             │
│  默认值：[              ]   │
│  (可选，所有行填充此值)     │
│                             │
│      [取消]    [确定]       │
└─────────────────────────────┘
```

### 导出时选择偏好

```
┌─────────────────────────────┐
│      导出 CSV               │
├─────────────────────────────┤
│  选择偏好：                  │
│  ○ 默认 (6列)               │
│  ● 完整版 (8列)             │
│  ○ 精简版 (3列)             │
│                             │
│      [取消]    [导出]       │
└─────────────────────────────┘
```

---

## 后端 API 设计

### API 接口列表

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/preferences` | GET | 获取所有偏好列表 |
| `/api/preferences/<id>` | GET | 获取单个偏好详情 |
| `/api/preferences` | POST | 新建偏好 |
| `/api/preferences/<id>` | PUT | 更新偏好 |
| `/api/preferences/<id>` | DELETE | 删除偏好 |
| `/api/preferences/<id>/default` | POST | 设为默认偏好 |
| `/api/export/<filename>/csv` | POST | 按指定偏好导出 CSV |
| `/api/export/<filename>/xml` | POST | 按指定偏好导出 XML |

### API 详情

**GET `/api/preferences`**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "默认",
      "columns": [...],
      "is_default": true,
      "updated_at": "2026-03-06T10:30:00"
    }
  ]
}
```

**POST `/api/preferences`**
```json
// 请求体
{
  "name": "完整版",
  "columns": [...]
}
// 响应
{
  "success": true,
  "data": {"id": 2}
}
```

**POST `/api/export/<filename>/csv`**
```json
// 请求体
{
  "preference_id": 1
}
// 响应: CSV 文件下载
```

---

## 导出逻辑

### 导出数据映射

| 列类型 | 导出处理 |
|--------|----------|
| 原始列 (is_custom: false) | 从 test 对象取对应字段值 |
| 有 default_value | 所有行填充默认值 |
| 自定义列 (is_custom: true) | 使用 values 中存储的单元格数据，无值则为空 |

### CSV 导出格式

```csv
所属模块,用例标题,前置条件,步骤,预期,优先级,未命名字段
模块A,登录测试,已注册,输入用户名,登录成功,1,
模块A,注册测试,,,注册成功,2,用户填写的值
```

**注意：导出不包含序号列**

### XML 导出格式 (TestLink)

```xml
<testcases>
  <testcase name="登录测试">
    <summary>登录测试</summary>
    <preconditions>已注册</preconditions>
    <importance>1</importance>
    <custom_fields>
      <custom_field>
        <name>未命名字段</name>
        <value>自定义值</value>
      </custom_field>
    </custom_fields>
    <steps>
      <step>
        <step_number>1</step_number>
        <actions>输入用户名</actions>
        <expectedresults>登录成功</expectedresults>
      </step>
    </steps>
  </testcase>
</testcases>
```

---

## 前端实现

### 文件结构

| 文件 | 用途 |
|------|------|
| `webtool/static/js/preview.js` | 预览页面交互逻辑（拖拽、编辑、保存） |
| `webtool/static/css/preview.css` | 预览页面自定义样式 |

### preview.js 模块结构

```javascript
const ColumnManager = {
  // 初始化：加载列配置
  init(),

  // 渲染
  renderHeader(columns),
  renderBody(testcases, columns),

  // 拖拽相关
  drag: {
    handleDragStart(e),
    handleDragOver(e),
    handleDrop(e),
  },

  // 编辑相关
  edit: {
    openModal(columnId),       // 打开编辑弹窗
    saveColumn(columnId, name, defaultValue),
  },

  // 列操作
  addColumn(name, defaultValue),
  deleteColumn(columnId),

  // 单元格编辑
  editCell(columnId, rowIndex),
  saveCell(columnId, rowIndex, value),

  // 偏好管理
  preference: {
    loadList(),
    switch(prefId),
    create(name),
    delete(prefId),
    setDefault(prefId),
  },

  // API 交互
  api: {
    loadPreferences(),
    savePreference(pref),
    exportCSV(filename, preferenceId),
    exportXML(filename, preferenceId),
  },

  // 防抖保存
  debounceSave(),
};
```

### 自动保存策略

- 列配置变更后 **防抖 500ms** 自动保存到后端
- 自定义单元格数据变更后 **防抖 300ms** 自动保存
- 导出前强制保存一次，确保数据一致

---

## 后端实现

### application.py 变更

```python
from flask import Flask
from webtool.models import db, Record, ColumnPreference

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


def init():
    """初始化应用"""
    if not exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)

    with app.app_context():
        db.create_all()

        # 插入默认偏好
        if ColumnPreference.query.count() == 0:
            default_pref = ColumnPreference(
                name="默认",
                columns_json=json.dumps(DEFAULT_COLUMNS, ensure_ascii=False),
                is_default=True
            )
            db.session.add(default_pref)
            db.session.commit()
```

### 默认列配置常量

```python
DEFAULT_COLUMNS = [
    {"id": "suite", "name": "所属模块", "visible": True, "order": 1, "is_custom": False},
    {"id": "name", "name": "用例标题", "visible": True, "order": 2, "is_custom": False},
    {"id": "preconditions", "name": "前置条件", "visible": True, "order": 3, "is_custom": False},
    {"id": "steps", "name": "步骤", "visible": True, "order": 4, "is_custom": False},
    {"id": "expectedresults", "name": "预期", "visible": True, "order": 5, "is_custom": False},
    {"id": "importance", "name": "优先级", "visible": True, "order": 6, "is_custom": False},
]
```

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `pyproject.toml` | 修改 | 新增 flask-sqlalchemy 依赖 |
| `webtool/models.py` | 新增 | Flask-SQLAlchemy 模型定义 |
| `webtool/schema.sql` | 删除 | 不再需要，由 ORM 自动创建表 |
| `webtool/application.py` | 修改 | 使用 Flask-SQLAlchemy 重构 |
| `webtool/templates/preview.html` | 修改 | 重构表格，新增偏好选择器 |
| `webtool/static/js/preview.js` | 新增 | 前端交互逻辑 |
| `webtool/static/css/preview.css` | 新增 | 拖拽/编辑/弹窗样式 |

---

## 数据流程

```
用户操作 → 前端 preview.js → API 请求 → SQLite (Flask-SQLAlchemy)
                ↓
         预览表格实时更新
                ↓
    选择偏好 → 导出 CSV/XML
```

---

## 兼容性说明

- **TestLink XML**：自定义列将作为 `custom_field` 导出，请确认 TestLink 是否支持这些字段
- **禅道 CSV**：自定义列直接追加到 CSV 末尾，导入时需确认禅道是否支持
