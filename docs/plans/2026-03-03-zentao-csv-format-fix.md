# 禅道 CSV 格式化修复设计文档

**日期:** 2026-03-03
**作者:** Claude Code
**状态:** 已批准

---

## 📋 概述

修复 xmind2cases 项目中禅道 CSV 导出功能的三个格式化问题，确保生成的 CSV 文件能够正确导入禅道系统。

---

## 🔍 问题描述

当前生成的 CSV 文件存在以下问题：

1. **缺少双引号包裹** - 单元格内容没有被双引号 `""` 包裹
2. **前置条件换行错误** - 前置条件中的换行符 `\n` 没有转换为 `<br>` 标签
3. **步骤换行丢失** - 步骤中的换行符在转换为 CSV 后消失

**影响范围：** 仅影响 `xmind2testcase/zentao.py` 模块的 CSV 输出功能

---

## ✅ 解决方案

采用**最小修改方案**，仅修改 `xmind2testcase/zentao.py` 文件，共 4 处关键改动：

### 1. 启用 CSV 全字段引号包裹

**位置:** `xmind_to_zentao_csv_file()` 函数

```python
# 修改前
writer = csv.writer(f)

# 修改后
writer = csv.writer(f, quoting=csv.QUOTE_ALL)
```

**效果:** 所有字段都会被双引号包裹，符合禅道 CSV 导入格式要求。

---

### 2. 前置条件换行符转换

**位置:** `gen_a_testcase_row()` 函数

```python
# 修改前
case_precondition = testcase_dict['preconditions']

# 修改后
case_precondition = testcase_dict['preconditions'].replace('\n', '<br>')
```

**效果:** 前置条件中的 `\n` 会被替换为 `<br>` 标签，在禅道中正确显示换行。

---

### 3. 步骤换行保留

**位置:** `gen_case_step_and_expected_result()` 函数

```python
# 修改前
actions = step_dict['actions'].replace('\n', '').strip()
case_step += f'{step_num}. {actions}\n'

# 修改后
actions = step_dict['actions'].strip()
case_step += f'{step_num}. {actions}\n'
```

**效果:** 步骤中的换行符会被正确保留，与预期结果的处理逻辑一致。

---

### 4. 确保预期结果保持不变

预期结果的现有逻辑已经正确处理换行，无需修改：

```python
# 保持现有逻辑不变
expected_results = step_dict.get('expectedresults', '')
if expected_results:
    expected_results = expected_results.replace('\n', '\n').strip()
    case_expected_result += f'{step_num}. {expected_results}\n'
```

---

## 🏗️ 数据流

```
XMind 文件
    ↓
get_xmind_testcase_list()  [现有逻辑，不变]
    ↓
testcase_dict (包含 preconditions 和 steps)
    ↓
gen_a_testcase_row()  [修改点 1 & 2]
    ├── case_precondition: replace('\n', '<br>')
    └── gen_case_step_and_expected_result()  [修改点 3]
         ├── 步骤: 移除 .replace('\n', '')
         └── 预期: 保持现有逻辑
    ↓
zentao_testcase_rows
    ↓
csv.writer(f, quoting=csv.QUOTE_ALL)  [修改点 4]
    ↓
CSV 文件（所有字段用双引号包裹）
```

---

## 🧪 测试策略

### 回归测试

使用现有测试文件验证修复效果：

1. **测试文件:** `docs/test.xmind`
2. **期望输出:** `docs/test_expect.csv`
3. **验证命令:**

```bash
# 激活虚拟环境
source .venv/bin/activate

# 转换测试文件
python -m xmind2testcase.cli docs/test.xmind -csv

# 对比输出
diff docs/test.csv docs/test_expect.csv
```

### 验收标准

✅ **必须满足以下所有条件：**

1. **双引号包裹** - 所有非空字段都被双引号包裹
2. **前置条件格式** - 前置条件中的 `\n` 被替换为 `<br>`
3. **步骤换行保留** - 步骤中的换行符正确显示
4. **预期结果不变** - 预期结果的格式保持与修改前一致
5. **无副作用** - 其他格式（XML、JSON）输出不受影响

### 边界情况测试

- 空前置条件
- 多个连续换行符
- 已包含 `<br>` 标签的文本
- 特殊字符（引号、逗号等）

---

## 🔄 向后兼容性

- ✅ **无破坏性变更** - 仅修改 CSV 输出格式
- ✅ **无新依赖** - 使用 Python 标准库 `csv` 模块
- ✅ **API 不变** - 函数签名和返回值保持不变
- ✅ **其他格式不受影响** - TestLink XML 和 JSON 输出保持原样

---

## 📝 实现检查清单

- [ ] 修改 `xmind2testcase/zentao.py` 中的 4 处代码
- [ ] 运行回归测试验证输出
- [ ] 确认 CSV 文件格式符合预期
- [ ] 验证其他格式（XML、JSON）输出正常
- [ ] 更新相关文档（如需要）

---

## 🎯 预期成果

修复后，生成的 CSV 文件将完全符合禅道导入格式要求，用户可以直接将转换后的 CSV 文件导入禅道系统，无需手动调整格式。

---

## 📚 参考资料

- [禅道 CSV 导入官方文档](https://www.zentao.net/book/zentaopmshelp/243.mhtml)
- Python csv 模块文档: https://docs.python.org/3/library/csv.html
