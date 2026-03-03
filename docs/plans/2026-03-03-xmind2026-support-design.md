# XMind2026 支持升级设计方案

**日期**: 2026-03-03
**作者**: Poco
**状态**: 已批准

---

## 📋 概述

### 目标

升级 xmind2testcase 项目，使其能够同时支持 XMind 8（XML 格式）和 XMind 2026（JSON 格式）版本的文件，通过替换底层 xmind 依赖为 xmindparser 实现。

### 背景

- **当前状态**: 仅支持 xmind8 及以前版本（XML 格式）
- **问题**: xmind2026 文件解析时出现乱码
- **解决方案**: 使用 xmindparser 库，它同时支持两种格式

### 设计决策

1. **依赖策略**: 完全替换 xmind → xmindparser（选择 A）
2. **API 兼容性**: 允许优化 API（选择 B）
3. **错误处理**: 严格模式，抛出明确异常（选择 A）
4. **测试策略**: 完整测试，80%+ 覆盖率（选择 B）
5. **输出验证**: 语义一致性（选择 B）

---

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────────────────────────────┐
│         CLI / Web Tool / API            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          xmind2testcase.utils           │
│  ┌───────────────────────────────────┐  │
│  │  get_xmind_testsuites()           │  │
│  │    - 替换 xmind.load()            │  │
│  │    - 使用 xmindparser.xmind_to_dict() │  │
│  │    - 调用 normalize_xmind_data()  │  │
│  └───────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         xmind2testcase.parser           │
│  (无需修改，接收标准化的数据结构)         │
└─────────────────────────────────────────┘
```

### 核心变化

- **移除**: `xmind>=1.2.0` 依赖
- **添加**: `xmindparser>=0.1.0` 依赖
- **新增**: `normalize_xmind_data()` 适配器函数
- **修改**: `get_xmind_testsuites()` 函数
- **不变**: `parser.py` 中的所有解析逻辑

---

## 🔧 核心组件设计

### 1. 适配器函数 `normalize_xmind_data()`

**位置**: `xmind2testcase/utils.py`

**职责**:
- 将 xmindparser 输出转换为旧 xmind 库格式
- 处理字段映射：`makers` → `markers`, `labels` → `label`
- 确保所有节点都有必需的字段（默认值）

**函数签名**:
```python
def normalize_xmind_data(
    xmind_dict: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Normalize xmindparser output to match legacy xmind library format.

    Args:
        xmind_dict: Raw output from xmindparser.xmind_to_dict()

    Returns:
        Normalized data structure matching old xmind library format

    Raises:
        ValueError: If input is invalid or empty
    """
```

**处理逻辑**:
1. 递归遍历所有 topic 节点
2. 字段映射：
   - `makers` → `markers`（保留原字段以防回退需要）
   - `labels` → `label`（取第一个元素或 None）
3. 默认值填充：
   - `markers`: 如果不存在，默认为 `[]`
   - `note`: 如果不存在，默认为 `None`
   - `label`: 如果不存在，默认为 `None`
   - `comment`: 默认为 `None`
   - `link`: 默认为 `None`
   - `id`: 默认为 `None`（虽然旧版本有此字段，但 parser.py 未使用）

### 2. 修改 `get_xmind_testsuites()`

**位置**: `xmind2testcase/utils.py:36`

**变更**:
```python
# 旧代码
import xmind
workbook = xmind.load(xmind_file)
xmind_content_dict = workbook.getData()

# 新代码
from xmindparser import xmind_to_dict
xmind_content_dict = xmind_to_dict(xmind_file)
xmind_content_dict = normalize_xmind_data(xmind_content_dict)
```

**错误处理**:
- 检查文件是否存在
- 验证返回数据非空
- 使用严格模式，抛出明确的异常

### 3. 依赖更新

**文件**: `pyproject.toml`

**变更**:
```toml
# 移除
- "xmind>=1.2.0"

# 添加
+ "xmindparser>=0.1.0"
```

---

## 🔄 数据流程

### 流程图

```
用户上传 xmind 文件
        │
        ▼
┌───────────────────────────────────┐
│  get_xmind_testsuites(file_path)  │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  xmindparser.xmind_to_dict()      │
│  - 解析 xmind8 (XML格式)          │
│  - 解析 xmind2026 (JSON格式)      │
│  返回: 原始字典数据                │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  normalize_xmind_data()           │
│  - makers → markers               │
│  - labels → label                 │
│  - 填充默认字段                    │
│  返回: 标准化字典数据              │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  xmind_to_testsuites()            │
│  (parser.py 中的现有逻辑)          │
│  - 解析测试集                      │
│  - 解析测试用例                    │
│  - 解析测试步骤                    │
└───────────────┬───────────────────┘
                │
                ▼
      返回 TestSuite 对象列表
```

### 关键数据转换示例

**xmindparser 原始输出**:
```python
{
    "title": "测试用例1",
    "makers": ["priority-1"],  # 注意是 makers
    "labels": ["自动"],
    "topics": [...]
}
```

**标准化后（适配器输出）**:
```python
{
    "title": "测试用例1",
    "makers": ["priority-1"],
    "markers": ["priority-1"],  # 新增映射字段
    "labels": ["自动"],
    "label": "自动",            # 新增映射字段
    "note": None,               # 新增默认字段
    "comment": None,            # 新增默认字段
    "link": None,               # 新增默认字段
    "topics": [...]
}
```

---

## ⚠️ 错误处理

### 严格模式实现

**1. 文件级错误**

```python
def get_xmind_testsuites(xmind_file: str) -> List[TestSuite]:
    xmind_file = get_absolute_path(xmind_file)

    # 文件存在性检查
    if not os.path.exists(xmind_file):
        raise FileNotFoundError(
            f"XMind file not found: {xmind_file}"
        )

    # 文件扩展名检查
    if not xmind_file.lower().endswith('.xmind'):
        raise ValueError(
            f"Invalid file format. Expected .xmind file, got: {xmind_file}"
        )

    # 解析文件
    try:
        xmind_content_dict = xmind_to_dict(xmind_file)
    except Exception as e:
        raise ValueError(
            f"Failed to parse XMind file: {xmind_file}. "
            f"Error: {str(e)}"
        ) from e

    # 数据验证
    if not xmind_content_dict:
        raise ValueError(
            f"Invalid XMind file: {xmind_file}. "
            "File is empty or contains no valid data."
        )
```

**2. 数据规范化错误**

```python
def normalize_xmind_data(xmind_dict: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(xmind_dict, list):
        raise ValueError(
            f"Expected list from xmindparser, got {type(xmind_dict).__name__}"
        )

    if len(xmind_dict) == 0:
        raise ValueError("XMind data is empty")

    # 递归处理...
```

---

## 🧪 测试策略

### 测试金字塔

```
        ┌────────────────┐
        │   E2E Tests    │  2 个
        │  (完整文件对比) │
        └────────┬───────┘
                 │
        ┌────────▼───────┐
        │ Integration    │  5 个
        │   Tests        │  (多格式解析)
        └────────┬───────┘
                 │
    ┌────────────▼──────────┐
    │   Unit Tests          │  15+ 个
    │  (适配器、边界情况)   │
    └───────────────────────┘
```

### 测试用例列表

**单元测试** (`tests/test_utils.py`):
1. `test_normalize_xmind_data_basic()` - 基本字段映射
2. `test_normalize_makers_to_markers()` - makers → markers 映射
3. `test_normalize_labels_to_label()` - labels → label 映射
4. `test_normalize_default_fields()` - 默认字段填充
5. `test_normalize_nested_topics()` - 嵌套结构处理
6. `test_normalize_empty_makers()` - 空 makers 处理
7. `test_normalize_empty_labels()` - 空 labels 处理
8. `test_get_xmind_testsuites_file_not_found()` - 文件不存在
9. `test_get_xmind_testsuites_invalid_format()` - 无效格式
10. `test_get_xmind_testsuites_empty_data()` - 空数据处理
11. `test_normalize_deeply_nested_structure()` - 深层嵌套
12. `test_normalize_preserves_original_data()` - 不修改原始数据
13. `test_normalize_with_markers_and_makers()` - 同时存在两个字段
14. `test_normalize_mixed_content_types()` - 混合内容类型

**集成测试** (`tests/test_integration.py`):
1. `test_parse_xmind8_file()` - 解析 xmind8 文件
2. `test_parse_xmind2026_file()` - 解析 xmind2026 文件
3. `test_both_formats_same_output()` - 两种格式输出一致
4. `test_convert_to_csv()` - CSV 转换功能
5. `test_convert_to_json()` - JSON 转换功能
6. `test_web_tool_functionality()` - Web 工具功能

**E2E 测试** (`tests/test_e2e.py`):
1. `test_xmind8_to_zentao_csv()` - 完整的 xmind8 到 CSV 流程
2. `test_xmind2026_to_zentao_csv()` - 完整的 xmind2026 到 CSV 流程

---

## 📝 实现细节

### 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `pyproject.toml` | 修改 | 替换依赖：xmind → xmindparser |
| `xmind2testcase/utils.py` | 修改 | 添加 `normalize_xmind_data()`, 更新 `get_xmind_testsuites()` |
| `xmind2testcase/parser.py` | **无变更** | 保持现有逻辑 |
| `tests/test_utils.py` | 新增 | 单元测试 |
| `tests/test_integration.py` | 新增 | 集成测试 |
| `tests/test_e2e.py` | 新增 | E2E 测试 |
| `README.md` | 修改 | 更新依赖说明和安装指南 |
| `CHANGELOG.md` | 修改 | 添加版本更新记录 |

### 核心代码实现

**`normalize_xmind_data()` 函数完整实现**:

```python
def normalize_xmind_data(xmind_dict: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize xmindparser output to match legacy xmind library format.

    Args:
        xmind_dict: Raw output from xmindparser.xmind_to_dict()

    Returns:
        Normalized data structure matching old xmind library format

    Raises:
        ValueError: If input is invalid or empty
    """
    if not isinstance(xmind_dict, list):
        raise ValueError(
            f"Expected list from xmindparser, got {type(xmind_dict).__name__}"
        )

    if len(xmind_dict) == 0:
        raise ValueError("XMind data is empty")

    def normalize_topic(topic: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single topic node."""
        # 确保 topic 是字典
        if not isinstance(topic, dict):
            return topic

        # 字段映射：makers → markers
        if 'makers' in topic:
            # 复制 makers 到 markers
            topic['markers'] = topic['makers']

        # 确保 markers 字段存在
        if 'markers' not in topic:
            topic['markers'] = []

        # 字段映射：labels → label
        if 'labels' in topic and isinstance(topic['labels'], list):
            # 取第一个 label，或 None
            topic['label'] = topic['labels'][0] if topic['labels'] else None
        elif 'label' not in topic:
            topic['label'] = None

        # 确保其他必需字段存在
        topic.setdefault('note', None)
        topic.setdefault('comment', None)
        topic.setdefault('link', None)
        topic.setdefault('id', None)

        # 递归处理子 topics
        if 'topics' in topic and isinstance(topic['topics'], list):
            topic['topics'] = [
                normalize_topic(sub_topic)
                for sub_topic in topic['topics']
            ]

        return topic

    # 深拷贝以避免修改原始数据
    import copy
    normalized_dict = copy.deepcopy(xmind_dict)

    # 标准化每个 sheet
    for sheet in normalized_dict:
        if 'topic' in sheet and isinstance(sheet['topic'], dict):
            sheet['topic'] = normalize_topic(sheet['topic'])

    return normalized_dict
```

**更新后的 `get_xmind_testsuites()`**:

```python
def get_xmind_testsuites(xmind_file: str) -> List[TestSuite]:
    """Load the XMind file and parse to TestSuite list.

    Args:
        xmind_file: Path to the XMind file.

    Returns:
        List of TestSuite objects parsed from the XMind file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid or parsing fails.
    """
    from xmindparser import xmind_to_dict

    xmind_file = get_absolute_path(xmind_file)

    # 文件存在性检查
    if not os.path.exists(xmind_file):
        raise FileNotFoundError(
            f"XMind file not found: {xmind_file}"
        )

    # 文件扩展名检查
    if not xmind_file.lower().endswith('.xmind'):
        raise ValueError(
            f"Invalid file format. Expected .xmind file, got: {xmind_file}"
        )

    logging.info('Parsing XMind file: %s', xmind_file)

    # 解析文件
    try:
        xmind_content_dict = xmind_to_dict(xmind_file)
    except Exception as e:
        raise ValueError(
            f"Failed to parse XMind file: {xmind_file}. "
            f"Error: {str(e)}"
        ) from e

    # 数据验证
    if not xmind_content_dict:
        raise ValueError(
            f"Invalid XMind file: {xmind_file}. "
            "File is empty or contains no valid data."
        )

    # 标准化数据格式
    try:
        xmind_content_dict = normalize_xmind_data(xmind_content_dict)
    except Exception as e:
        raise ValueError(
            f"Failed to normalize XMind data: {str(e)}"
        ) from e

    logging.debug("Normalized XMind data: %s", xmind_content_dict)

    # 解析为 TestSuite 对象
    testsuites = xmind_to_testsuites(xmind_content_dict)

    logging.info('Successfully parsed %d testsuite(s)', len(testsuites))
    return testsuites
```

---

## 🔄 向后兼容性

### API 兼容性

**保持不变的公共函数**:
- ✅ `get_xmind_testsuite_list(xmind_file: str)`
- ✅ `get_xmind_testcase_list(xmind_file: str)`
- ✅ `xmind_testsuite_to_json_file(xmind_file: str)`
- ✅ `xmind_testcase_to_json_file(xmind_file: str)`

**行为变化**:
- ❌ **错误处理更严格**: 文件不存在或格式错误时抛出异常而不是返回空列表
- ✅ **输出格式相同**: JSON 和 CSV 输出格式保持一致
- ✅ **数据结构相同**: TestCase、TestSuite、TestStep 对象结构不变

### 迁移指南

**对现有用户的影响**:

```python
# 旧代码（仍然有效）
from xmind2testcase.utils import get_xmind_testcase_list
testcases = get_xmind_testcase_list('test.xmind')  # 现在支持 xmind2026

# 唯一的变化：错误处理需要捕获异常
try:
    testcases = get_xmind_testcase_list('test.xmind')
except (FileNotFoundError, ValueError) as e:
    print(f"Error: {e}")
    testcases = []
```

---

## 📋 实施计划

### 阶段划分

**阶段 1：准备（1-2小时）**
- [ ] 设置测试框架（pytest）
- [ ] 准备测试数据（xmind8 和 xmind2026 文件）
- [ ] 创建测试文件结构

**阶段 2：核心实现（2-3小时）**
- [ ] 实现 `normalize_xmind_data()` 函数
- [ ] 更新 `get_xmind_testsuites()` 函数
- [ ] 更新依赖配置（pyproject.toml）

**阶段 3：测试（2-3小时）**
- [ ] 编写单元测试（目标：14+ 个测试）
- [ ] 编写集成测试（目标：6+ 个测试）
- [ ] 编写 E2E 测试（目标：2+ 个测试）
- [ ] 验证测试覆盖率达到 80%+

**阶段 4：验证（1小时）**
- [ ] 用 xmind8 文件测试，对比 CSV 输出
- [ ] 用 xmind2026 文件测试，验证正确解析
- [ ] 验证 Web 工具功能正常

**阶段 5：文档和发布（1小时）**
- [ ] 更新 README.md
- [ ] 更新 CHANGELOG.md
- [ ] 提交代码
- [ ] 发布新版本到 PyPI

**总预计时间**: 7-10 小时

---

## 🎯 成功标准

### 功能验收标准

- [ ] **xmind8 支持**: 能够成功解析 xmind8 版本的文件并转换为 CSV
- [ ] **xmind2026 支持**: 能够成功解析 xmind2026 版本的文件并转换为 CSV
- [ ] **输出一致性**: 两种版本文件转换后的测试用例内容语义一致
- [ ] **错误处理**: 文件不存在、格式错误时抛出明确异常
- [ ] **测试覆盖率**: 单元测试 + 集成测试覆盖率 ≥ 80%

### 性能标准

- [ ] **解析速度**: 解析 10MB xmind 文件时间 < 5 秒
- [ ] **内存占用**: 峰值内存 < 200MB（对于典型文件）

### 质量标准

- [ ] **代码规范**: 符合 PEP 8 和项目 coding-style.md
- [ ] **无控制台日志**: 移除所有 `console.log` 或调试输出
- [ ] **类型提示**: 所有公共函数添加类型注解
- [ ] **文档字符串**: 所有函数添加 docstring

---

## 📊 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| xmindparser 字段不完全兼容 | 高 | 中 | 适配器层处理字段映射 |
| 性能下降 | 中 | 低 | 性能基准测试 |
| 边界情况未覆盖 | 中 | 中 | 完整的单元测试 |
| 破坏现有 API | 高 | 低 | 保持公共函数签名不变 |
| xmindparser 库维护停滞 | 中 | 低 | 已是稳定版本，可考虑 fork |

---

## ✅ 设计总结

这个设计方案采用**适配器模式**，通过以下方式实现目标：

1. **完全替换** xmind → xmindparser
2. **适配器层**处理字段映射差异（`makers`→`markers`, `labels`→`label`）
3. **严格模式**错误处理，提供明确的错误信息
4. **完整测试**覆盖单元、集成、E2E 三个层次
5. **API 兼容**保持现有公共函数不变
6. **分阶段实施**降低风险

### 关键优势

- ✅ 最小化代码改动（parser.py 无需修改）
- ✅ 易于测试和维护
- ✅ 向后兼容现有 API
- ✅ 支持两种格式的 xmind 文件
- ✅ 严格的错误处理机制

---

## 🔗 相关资源

- [xmindparser GitHub](https://github.com/tobyqin/xmindparser)
- [xmindparser 文档](https://github.com/tobyqin/xmindparser/blob/master/README_CN.md)
- 测试文件位置: `docs/202602-数据资产v6.4.8(xmind8版本).xmind`
- 测试文件位置: `docs/202602-数据资产v6.4.8(xmind2026版本).xmind`
- 参考输出: `docs/202602-数据资产v6.4.8(xmind8版本).csv`

---

**审批**: ✅ 已批准
**下一步**: 调用 writing-plans skill 创建详细实施计划
