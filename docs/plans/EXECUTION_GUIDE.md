# 在新会话中执行实施计划

## 📋 前置准备

### Step 1: 确认工作目录

当前工作目录应该是项目根目录：
```bash
pwd
# 应该显示: /Users/poco/Projects/xmind2testcase
```

### Step 2: 确认实施计划存在

```bash
ls -lh docs/plans/2026-03-03-xmind2026-support-implementation.md
```

---

## 🚀 在新会话中执行

### 方式 A: 使用 Claude Code（推荐）

**Step 1: 打开新的终端/会话**

```bash
# 在项目根目录打开新的终端
cd /Users/poco/Projects/xmind2testcase
```

**Step 2: 启动新的 Claude Code 会话**

```bash
# 在新终端中
claude
```

**Step 3: 在新会话中输入以下指令**

```
/superpowers:executing-plans
```

然后按提示输入实施计划路径：

```
请执行实施计划: docs/plans/2026-03-03-xmind2026-support-implementation.md
```

---

### 方式 B: 使用已有的会话

如果你已经在另一个会话中，直接输入：

```
/superpowers:executing-plans
```

然后指定计划文件。

---

## 📊 执行监控

### 检查点验证

实施计划包含以下检查点，每个阶段完成后应验证：

**检查点 1**: 阶段 1 完成后（任务 0-2）
- [ ] 测试框架已搭建
- [ ] pytest 配置完成
- [ ] fixtures 可用

**检查点 2**: 阶段 2 完成后（任务 3-8）
- [ ] `normalize_xmind_data()` 已实现
- [ ] 所有单元测试通过（14+ 个）
- [ ] 覆盖率 > 50%

**检查点 3**: 阶段 3 完成后（任务 9）
- [ ] `get_xmind_testsuites()` 已更新
- [ ] 错误处理测试通过

**检查点 4**: 阶段 4 完成后（任务 10-13）
- [ ] 集成测试通过（6+ 个）
- [ ] xmind8 和 xmind2026 都能解析

**检查点 5**: 阶段 5 完成后（任务 14-15）
- [ ] E2E 测试通过（2 个）
- [ ] CSV 转换功能正常

**检查点 6**: 阶段 6 完成后（任务 16-18）
- [ ] 依赖已更新
- [ ] 文档已完善

**检查点 7**: 阶段 7 完成后（任务 19-20）
- [ ] 所有测试通过
- [ ] 覆盖率 ≥ 80%
- [ ] 已发布到 PyPI

---

## 🔍 进度追踪

### 查看测试进度

```bash
# 运行所有测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov=xmind2testcase --cov-report=term-missing
```

### 查看 Git 提交历史

```bash
# 查看最近的提交
git log --oneline -10

# 查看详细提交信息
git log --stat -5
```

### 查看当前任务

```bash
# 查看实施计划
cat docs/plans/2026-03-03-xmind2026-support-implementation.md | grep "^### Task"
```

---

## ⚠️ 常见问题

### Q1: 测试失败怎么办？

```bash
# 查看详细错误信息
pytest tests/test_utils.py::test_name -v -s

# 进入调试模式
pytest tests/test_utils.py::test_name --pdb
```

### Q2: xmindparser 未安装？

```bash
source .venv/bin/activate
uv pip install xmindparser
```

### Q3: 需要回滚某个任务？

```bash
# 查看提交历史
git log --oneline

# 回滚到指定提交
git reset --hard <commit-hash>

# 或回滚单个文件
git checkout HEAD~1 -- path/to/file
```

### Q4: 如何跳过某个任务？

编辑实施计划，注释掉不需要的任务，或直接从下一个任务开始。

---

## 📞 需要帮助？

如果在执行过程中遇到问题：

1. **查看设计文档**: `docs/plans/2026-03-03-xmind2026-support-design.md`
2. **查看错误日志**: `pytest tests/ -v --tb=long`
3. **回到主会话**: 在这个会话中询问问题

---

## ✅ 完成后验证

实施完成后，运行以下命令验证：

```bash
# 1. 所有测试通过
pytest tests/ -v

# 2. 覆盖率达标
pytest tests/ --cov=xmind2testcase --cov-report=term

# 3. 测试 xmind8 文件
python -m xmind2testcase.cli "docs/202602-数据资产v6.4.8(xmind8版本).xmind" -csv

# 4. 测试 xmind2026 文件
python -m xmind2testcase.cli "docs/202602-数据资产v6.4.8(xmind2026版本).xmind" -csv

# 5. 启动 Web 工具测试
python -m xmind2testcase.cli webtool
# 在浏览器访问 http://127.0.0.1:5002
```

---

## 🎉 成功标准

完成所有 20 个任务后，你应该能够：

- ✅ 同时解析 xmind8 和 xmind2026 文件
- ✅ 正确转换为 CSV、JSON 格式
- ✅ 所有 22+ 个测试通过
- ✅ 代码覆盖率 ≥ 80%
- ✅ Web 工具正常运行
- ✅ 已发布新版本到 PyPI

---

**祝实施顺利！** 🚀

如有任何问题，随时回到这个会话询问。
