# 文档系统更新设计文档

**日期:** 2026-03-04
**作者:** Claude
**状态:** 已批准
**主题:** 系统性更新项目文档，建立持续检查机制

---

## 📋 需求分析

### 当前问题

通过对项目文档的系统性检查，发现以下主要问题：

#### 1. README.md 问题
- **包名不一致** - 多处仍使用 `xmind2testcase`，应更新为 `xmind2cases`
- **版本信息过时** - 显示 v1.5.0 为最新，实际已到 v1.6.1
- **新功能缺失**：
  - Windows 脚本支持（init.bat/init.ps1）
  - 端口占用检测和交互式处理
  - UI 优化（图标、紧凑布局、长文件名截断）
  - 包重命名完成
- **内容重复** - "快速开始"部分出现两次（第18行和第157行）

#### 2. CHANGELOG.md 问题
- **版本混乱** - [Unreleased] 部分包含已发布内容
- **v1.6.1 缺失** - pyproject.toml 显示 1.6.1，但 CHANGELOG 中没有记录
- **格式不统一** - 中英文混杂，emoji 使用不一致

#### 3. api/README.md 问题
- **过于简单** - 缺少实际使用示例
- **信息不够简洁** - 不符合 "Keep It Simple" 原则

### 用户需求

- **目标受众**：最终用户（使用工具进行测试用例转换的测试人员）
- **更新范围**：全面更新（包重命名、新功能、版本信息、快速启动指南）
- **维护方式**：CI/CD 集成，防止文档与代码不同步
- **文档标准**：简洁实用，重点突出快速上手和核心功能（Keep It Simple）

---

## 🎯 设计方案

### 方案选择

经过分析，选择**方案 1：最小化更新 + CI 检查**

**理由：**
- ✅ 快速完成，风险最低
- ✅ 建立 CI 检查，防止再次过时
- ✅ 符合 "Keep It Simple" 原则
- ✅ 可持续维护

### 架构设计

```
┌─────────────────┐
│  代码变更       │
│  (feat/fix)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  提交 PR        │
│  包含文档更新?  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
   是         否
    │         │
    ▼         ▼
┌────────┐  ┌─────────────┐
│ 合并   │  │ CI 失败 ❌  │
└───┬────┘  │ (doc-check) │
    │       └─────────────┘
    ▼
┌─────────────────┐
│ CI 检查通过 ✅  │
│ - 包名一致性    │
│ - 版本匹配      │
│ - Markdown lint │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  自动合并       │
└─────────────────┘
```

---

## 📝 详细设计

### 阶段 1：文档修复（核心）

#### 1.1 README.md 更新

**删除重复内容**
- 删除第 157-277 行重复的"快速开始"部分

**全局替换**
- `xmind2testcase` → `xmind2cases`
- 版本号更新为 v1.6.1

**补充新功能说明**

在"一键启动"部分完善 Windows 脚本说明：
```markdown
**Windows 用户:**

```cmd
# 方式 1: 双击运行（推荐）
# 双击 init.bat 文件即可

# 方式 2: 命令行运行
init.bat

# 方式 3: PowerShell（更强大的功能）
.\init.ps1
```
```

在"功能特性"中添加：
```markdown
- 🆕 **多版本支持** - 同时支持 XMind 8 和 XMind 2026 文件格式
- 🔍 **智能检测** - 端口占用自动检测并提供交互式解决方案
- 🎨 **现代化 UI** - 图标化操作、紧凑布局、长文件名智能截断
```

#### 1.2 CHANGELOG.md 重构

**新格式结构：**
```markdown
# 更新日志

所有重要的项目变更都将记录在此文件中。

## [Unreleased]

## [1.6.1] - 2026-03-04

### Added
- ✨ 支持 Windows 一键启动（init.bat/init.ps1）
- ✨ 端口占用检测和交互式处理
- ✨ UI 优化：图标化操作、紧凑布局、长文件名智能截断

### Changed
- 🔄 包名从 xmind2testcase 重命名为 xmind2cases
- 📝 优化文档结构，删除重复内容

### Fixed
- 🐛 修复禅道 CSV 导出格式问题：所有字段用双引号包裹
- 🐛 修复前置条件中的换行符转换为 `<br>` 标签

## [1.6.0] - 2026-03-03

### Added
- ✨ 一键初始化脚本 init.sh，支持环境配置和发布流程
- 🐍 Python 最低版本提升至 3.12.12
- 🔧 集成现代化开发工具：ruff, pyright, pre-commit, rich
- ✨ 支持 XMind 2026 文件格式（JSON 格式）
- 🔄 同时兼容 XMind 8 及以前版本（XML 格式）
- 🧪 添加完整的测试套件（单元、集成、E2E）

### Changed
- 📦 使用 uv 替代 setuptools 进行构建和发布
- ♻️ 底层解析库从 xmind 切换到 xmindparser

### Removed
- 🗑️ 删除过时的配置文件：pytest.ini, requirements.txt

### Fixed
- 🐛 修复 xmind2026 文件解析乱码问题
```

#### 1.3 api/README.md 简化

**保留核心内容：**
- 快速开始（启动服务）
- 主要端点列表
- 基本使用示例

**删除冗余内容：**
- 过于详细的目录结构
- 重复的技术栈说明

---

### 阶段 2：CI 检查（保障）

#### 2.1 文档检查脚本

创建 `scripts/check_docs.py`：

```python
#!/usr/bin/env python3
"""文档一致性检查脚本"""

import re
import sys
from pathlib import Path

def check_readme():
    """检查 README.md 中的包名一致性"""
    readme = Path("README.md").read_text()

    # 不应出现旧的包名
    if "xmind2testcase" in readme:
        print("❌ README.md 中包含旧包名 'xmind2testcase'")
        return False

    # 应包含新包名
    if "xmind2cases" not in readme:
        print("❌ README.md 中缺少包名 'xmind2cases'")
        return False

    print("✅ README.md 包名检查通过")
    return True

def check_changelog_version():
    """检查 CHANGELOG 与 pyproject.toml 版本匹配"""
    try:
        import toml
    except ImportError:
        print("⚠️  跳过版本检查（toml 未安装）")
        return True

    pyproject = toml.load("pyproject.toml")
    version = pyproject["project"]["version"]

    changelog = Path("CHANGELOG.md").read_text()

    # 检查最新版本是否在 CHANGELOG 中
    if f"[{version}]" not in changelog:
        print(f"❌ CHANGELOG.md 中缺少版本 [{version}]")
        return False

    print(f"✅ CHANGELOG.md 版本 {version} 检查通过")
    return True

def main():
    """主函数"""
    all_passed = True

    all_passed &= check_readme()
    all_passed &= check_changelog_version()

    if all_passed:
        print("\n✅ 所有文档检查通过")
        return 0
    else:
        print("\n❌ 文档检查失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

#### 2.2 GitHub Actions 配置

创建 `.github/workflows/doc-check.yml`：

```yaml
name: Documentation Check

on:
  pull_request:
    paths:
      - 'README.md'
      - 'CHANGELOG.md'
      - 'api/README.md'
      - 'pyproject.toml'

jobs:
  doc-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install toml

      - name: Run documentation checks
        run: |
          python scripts/check_docs.py
```

---

## ⚠️ 错误处理

### 常见问题

#### 问题 1：版本号不一致

**检测：**
```bash
grep version pyproject.toml
grep "## \[" CHANGELOG.md | head -1
grep "v1\." README.md | head -1
```

**解决：** 手动同步或使用脚本

#### 问题 2：包名替换遗漏

**检测：**
```bash
grep -r "xmind2testcase" --include="*.md" --include="*.py" .
```

**解决：**
```bash
find . -name "*.md" -type f -exec sed -i '' 's/xmind2testcase/xmind2cases/g' {} +
```

---

## 📊 实施计划

### 第一步：文档修复（优先级：高）

- [ ] 删除 README.md 重复内容（第157-277行）
- [ ] 全局替换包名 `xmind2testcase` → `xmind2cases`
- [ ] 更新 README.md 版本号为 v1.6.1
- [ ] 补充 Windows 脚本说明
- [ ] 添加端口占用检测说明
- [ ] 添加 UI 优化说明
- [ ] 重构 CHANGELOG.md
- [ ] 简化 api/README.md

### 第二步：创建检查脚本（优先级：中）

- [ ] 创建 `scripts/check_docs.py`
- [ ] 添加执行权限
- [ ] 本地测试脚本

### 第三步：配置 CI（优先级：中）

- [ ] 创建 `.github/workflows/doc-check.yml`
- [ ] 测试 CI 工作流
- [ ] 合并到 main 分支

### 第四步：验证和发布（优先级：低）

- [ ] 完整运行检查脚本
- [ ] 创建测试 PR
- [ ] 发布 v1.6.2

---

## ✅ 验收标准

### 功能验收

- [ ] README.md 中不包含 `xmind2testcase`
- [ ] README.md 版本号显示为 v1.6.1
- [ ] CHANGELOG.md 包含完整的 v1.6.1 记录
- [ ] CHANGELOG.md 版本号与 pyproject.toml 匹配
- [ ] 检查脚本可以正常运行
- [ ] CI 工作流可以在 PR 时触发

### 质量验收

- [ ] 文档简洁明了，符合"Keep It Simple"原则
- [ ] 新用户可以在 5 分钟内完成安装和首次使用
- [ ] 开发者可以在 PR 时及时发现文档问题
- [ ] 版本发布时文档不会遗漏

---

## 📈 工作量评估

| 任务 | 预计时间 | 风险 |
|------|---------|------|
| README.md 修复 | 30分钟 | 低 |
| CHANGELOG.md 重构 | 20分钟 | 低 |
| api/README.md 简化 | 15分钟 | 低 |
| 检查脚本开发 | 45分钟 | 中 |
| CI 配置和测试 | 30分钟 | 中 |
| **总计** | **2.5小时** | - |

---

## 🔄 未来增强（非本次实施）

### 可能的增强

1. **自动化文档生成** - 从代码 docstring 生成 API 文档
2. **版本自动更新** - 发布脚本自动更新所有版本号
3. **文档预览** - PR 时预览文档渲染效果
4. **多语言支持** - 添加英文文档

### 不做的事项（YAGNI 原则）

- ❌ 不创建复杂的文档生成系统
- ❌ 不添加自动翻译工具
- ❌ 不过度设计文档结构
- ❌ 不为了完美而拖延更新

---

## 📚 参考资料

- 项目仓库: https://github.com/koco-co/xmind2cases
- 现有文档: README.md, CHANGELOG.md, api/README.md
- 最近提交: git log --oneline -20

---

**设计状态:** ✅ 已批准
**下一步:** 调用 writing-plans skill 创建详细实施计划
