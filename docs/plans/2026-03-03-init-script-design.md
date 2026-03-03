# 项目初始化脚本设计方案

**日期:** 2026-03-03
**版本:** 1.0.0
**作者:** Poco

---

## 1. 概述

### 1.1 目标

创建一个一键式项目初始化脚本 `init.sh`，实现：

- 自动配置开发环境（Python 3.12.12+）
- 检查并安装现代化开发工具（uv, ruff, pyright, pre-commit, rich）
- 使用 uv 管理 Python 依赖
- 自动清理项目冗余文件
- 启动 Web 工具进行功能验证
- 支持一键发布到 GitHub 和 PyPI

### 1.2 验收标准

- ✅ 他人克隆代码后，运行 `./init.sh` 即可直接启动项目
- ✅ 所有环境、配置由脚本自动完成
- ✅ Web 工具可正常访问和转换 XMind 文件
- ✅ 通过 `./init.sh --release` 可完成完整的发布流程

---

## 2. 脚本架构设计

### 2.1 整体结构

```bash
#!/bin/bash
# xmind2cases 项目初始化脚本
# 支持: macOS, Linux, Windows (WSL/Git Bash)

main() {
  parse_arguments "$@"

  if [[ "$RELEASE_MODE" == "true" ]]; then
    release_flow
  else
    dev_flow
  fi
}

# 开发流程
dev_flow() {
  check_prerequisites
  cleanup_project
  install_tools
  setup_environment
  verify_setup
  start_webtool
}

# 发布流程
release_flow() {
  check_prerequisites
  cleanup_project
  install_tools
  setup_environment
  verify_setup
  verify_xmind_conversion
  run_linter
  run_type_check
  verify_version
  confirm_release
  update_version_docs
  git_commit_changes
  create_git_tag
  uv_build
  uv_publish
  create_gh_release
  print_success
}
```

### 2.2 参数控制

| 参数 | 功能 |
|------|------|
| 无参数 | 配置环境并启动 Web 工具 |
| `--release` | 完整发布流程（GitHub + PyPI） |
| `--no-webtool` | 仅配置环境，不启动 Web 工具 |
| `--help` | 显示帮助信息 |

---

## 3. 核心功能模块

### 3.1 环境检查模块

#### `check_prerequisites()`

**检查项：**

1. **操作系统识别**
   ```bash
   detect_os() {
     case "$(uname -s)" in
       Linux*)     OS="Linux" ;;
       Darwin*)    OS="macOS" ;;
       MINGW*)     OS="Windows" ;;
       *)          OS="Unknown" ;;
     esac
   }
   ```

2. **Python 版本检查**
   - 最低要求: Python 3.12.12
   - 检查命令: `python3 --version`
   - 版本比较: 使用 `sort -V`

3. **uv 包管理器检查**
   - 检查命令: `command -v uv`
   - 未安装则自动安装: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3.2 工具安装模块

#### `install_tools()`

**自动安装的工具：**

| 工具 | 用途 | 安装方式 |
|------|------|----------|
| `uv` | Python 包管理 | 官方安装脚本 |
| `ruff` | 代码检查和格式化 | `uv tool install ruff` |
| `pyright` | 类型检查 | `uv tool install pyright` |
| `pre-commit` | Git hooks 管理 | `uv tool install pre-commit` |
| `rich` | 终端美化输出 | 已在 dependencies 中 |

**安装逻辑：**

```bash
install_tool() {
  local tool=$1
  if ! command -v "$tool" &> /dev/null; then
    print_step "安装 $tool..."
    uv tool install "$tool"
    print_success "$tool 安装完成"
  else
    print_success "$tool 已安装"
  fi
}
```

### 3.3 环境配置模块

#### `setup_environment()`

**执行步骤：**

1. **创建虚拟环境**
   ```bash
   uv venv --python 3.12
   source .venv/bin/activate
   ```

2. **安装项目依赖**
   ```bash
   uv sync
   ```

3. **安装 pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

4. **配置 git hooks** (如果不存在)
   ```bash
   # .pre-commit-config.yaml
   repos:
     - repo: local
       hooks:
         - id: ruff
           name: ruff check
           entry: uv run ruff check
           language: system
         - id: ruff-format
           name: ruff format
           entry: uv run ruff format --check
           language: system
   ```

### 3.4 项目清理模块

#### `cleanup_project()`

**删除的文件/目录：**

| 类型 | 文件/目录 |
|------|----------|
| 构建产物 | `dist/`, `*.egg-info/` |
| 测试报告 | `htmlcov/`, `.coverage`, `.pytest_cache/` |
| 开发环境 | `.venv/`, `__pycache__/`, `*.pyc` |
| IDE 配置 | `.idea/`, `.vscode/` |
| 日志文件 | `logs/`, `*.log` |
| 临时文件 | `.DS_Store`, `Thumbs.db` |
| 旧配置 | `pytest.ini`, `requirements.txt`, `samples.py` |

**清理逻辑：**

```bash
cleanup_project() {
  print_step "清理项目文件..."

  local remove_list=(
    "dist" "*.egg-info"
    "htmlcov" ".coverage" ".pytest_cache"
    ".venv" "__pycache__" "*.pyc"
    ".idea" ".vscode"
    "logs" "*.log"
    ".DS_Store" "Thumbs.db"
    "pytest.ini" "requirements.txt" "samples.py"
  )

  for item in "${remove_list[@]}"; do
    find . -name "$item" -prune -o -name "$item" -exec rm -rf {} + 2>/dev/null || true
  done

  print_success "项目清理完成"
}
```

### 3.5 测试验证模块

#### `verify_setup()`

**验证步骤：**

1. **虚拟环境检查**
   ```bash
   [[ -d ".venv" ]] || { print_error "虚拟环境未创建"; exit 1; }
   ```

2. **依赖检查**
   ```bash
   uv run python -c "import xmindparser, flask, arrow"
   ```

3. **测试套件**
   ```bash
   uv run pytest tests/ -v --cov=xmind2testcase --cov-report=term-missing
   ```

4. **Web 工具启动测试**
   ```bash
   start_webtool_background
   sleep 3
   curl -s http://127.0.0.1:5002 > /dev/null
   stop_webtool
   ```

#### `verify_xmind_conversion()`

**E2E 测试：**

- CSV 转换: `uv run python -m xmind2testcase.cli test.xmind -csv`
- XML 转换: `uv run python -m xmind2testcase.cli test.xmind -xml`
- JSON 转换: `uv run python -m xmind2testcase.cli test.xmind -json`

### 3.6 Web 工具启动模块

#### `start_webtool()`

**启动逻辑：**

```bash
start_webtool() {
  print_step "启动 Web 工具..."
  print_info "访问地址: http://127.0.0.1:5002"
  print_info "按 Ctrl+C 停止服务"

  uv run python webtool/application.py
}
```

### 3.7 发布流程模块

#### `release_flow()`

**完整流程：**

1. **环境准备** → `check_prerequisites`, `cleanup_project`, `install_tools`, `setup_environment`
2. **质量检查** → `run_linter`, `run_type_check`, `verify_setup`, `verify_xmind_conversion`
3. **版本确认** → `verify_version`, `confirm_release`
4. **文档更新** → `update_version_docs`
5. **代码提交** → `git_commit_changes`
6. **标签创建** → `create_git_tag`
7. **构建发布** → `uv_build`, `uv_publish`
8. **GitHub 发布** → `create_gh_release`

#### 版本验证逻辑

```bash
verify_version() {
  local pyproject_ver=$(grep "^version = " pyproject.toml | sed 's/version = "\(.*\)"/\1/')
  local changelog_ver=$(grep "^\[.*\]" CHANGELOG.md | head -1 | sed 's/\[\(.*\)\]/\1/')

  if [[ "$pyproject_ver" != "$changelog_ver" ]]; then
    print_error "版本不一致"
    exit 1
  fi
}
```

#### PyPI 发布

```bash
uv_build() {
  print_step "构建项目..."
  uv build
}

uv_publish() {
  print_step "发布到 PyPI..."
  if [[ -z "$UV_PUBLISH_TOKEN" ]]; then
    print_error "未设置 UV_PUBLISH_TOKEN"
    exit 1
  fi
  uv publish
}
```

#### GitHub 发布

```bash
create_git_tag() {
  print_step "创建 Git 标签..."
  local version=$(grep "^version = " pyproject.toml | sed 's/version = "\(.*\)"/\1/')
  git tag -a "v$version" -m "Release v$version"
}

create_gh_release() {
  print_step "创建 GitHub Release..."
  local version=$(grep "^version = " pyproject.toml | sed 's/version = "\(.*\)"/\1/')
  gh release create "v$version" --notes-from-tag
  git push --tags
}
```

---

## 4. 文档更新策略

### 4.1 项目重命名

**xmind2testcase → xmind2cases**

**需要修改的文件：**

| 文件 | 修改内容 |
|------|----------|
| `pyproject.toml` | name, keywords, URLs, scripts |
| `README.md` | 所有 xmind2testcase → xmind2cases |
| `CHANGELOG.md` | 添加重命名记录 |
| `xmind2testcase/cli.py` | 命令名称 |

### 4.2 pyproject.toml 关键修改

```toml
[project]
name = "xmind2cases"
version = "1.6.0"
requires-python = ">=3.12.12"

[project.scripts]
xmind2cases = "xmind2testcase.cli:cli_main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 4.3 README.md 新增内容

```markdown
## 快速启动

```bash
# 克隆项目
git clone https://github.com/koco-co/xmind2cases.git
cd xmind2cases

# 一键启动
./init.sh
```

## 发布流程

```bash
# 完整发布流程（GitHub + PyPI）
./init.sh --release
```
```

### 4.4 CHANGELOG.md 新增内容

```markdown
## [1.6.0] - 2026-03-03

### Added
- 一键初始化脚本 init.sh，支持环境配置和发布流程
- Python 最低版本提升至 3.12.12
- 集成现代化开发工具：ruff, pyright, pre-commit, rich

### Changed
- 项目重命名为 xmind2cases（原 xmind2testcase）
- 使用 uv 替代 setuptools 进行构建和发布
- 更新所有文档和命令名称

### Removed
- 删除过时的配置文件：pytest.ini, requirements.txt
```

---

## 5. 用户体验设计

### 5.1 Rich 输出格式化

**使用 Rich 库美化终端输出：**

- `print_step()` - 蓝色，显示当前步骤
- `print_success()` - 绿色，显示成功信息
- `print_error()` - 红色，显示错误信息
- `print_warning()` - 黄色，显示警告信息

**示例输出：**

```
➜ 检查 Python 版本...
✓ Python 版本检查通过: 3.12.12
➜ 检查 uv 包管理器...
✓ uv 已安装
➜ 清理项目文件...
✓ 项目清理完成
```

### 5.2 进度显示

**长时间操作使用进度条：**

```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task('[cyan]安装依赖...[/cyan]', total=100)
    # 安装过程
```

### 5.3 用户交互

**重要操作需要确认：**

```bash
confirm_release() {
  print_warning "准备发布以下版本: $VERSION"
  echo "将会："
  echo "  1. 构建并发布到 PyPI"
  echo "  2. 创建 GitHub Release"
  echo "  3. 推送 git tag"
  echo ""
  read -p "确认发布？(yes/no): " confirm

  if [[ "$confirm" != "yes" ]]; then
    print_info "发布已取消"
    exit 0
  fi
}
```

### 5.4 错误处理

**全局错误处理：**

```bash
set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时退出
set -o pipefail  # 管道命令失败时退出

trap 'print_error "脚本执行失败"; exit 1' ERR
```

**日志记录：**

```bash
LOG_FILE="init-$(date +%Y%m%d-%H%M%S).log"

log_message() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}
```

---

## 6. 技术栈

### 6.1 核心技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Bash | - | 脚本语言 |
| Python | 3.12.12+ | 项目运行时 |
| uv | 最新 | Python 包管理 |
| ruff | 最新 | 代码检查和格式化 |
| pyright | 最新 | 类型检查 |
| pre-commit | 最新 | Git hooks 管理 |
| rich | 最新 | 终端美化 |

### 6.2 构建工具

| 工具 | 用途 |
|------|------|
| `uv build` | 构建项目 |
| `uv publish` | 发布到 PyPI |
| `gh` | GitHub CLI |

---

## 7. 安全考虑

### 7.1 环境变量

- `UV_PUBLISH_TOKEN` - PyPI 发布令牌
- 脚本检查变量是否存在，不存在则终止发布

### 7.2 权限检查

- 发布前验证 GitHub 认证状态: `gh auth status`
- 验证 PyPI 令牌有效性

### 7.3 代码签名

- Git tag 使用 GPG 签名（可选）
- PyPI 包使用 trusted publishers（推荐）

---

## 8. 后续改进

### 8.1 可能的增强

1. **Docker 支持** - 添加 Dockerfile 和 docker-compose.yml
2. **CI/CD 集成** - GitHub Actions 自动化测试和发布
3. **多环境支持** - 开发/测试/生产环境配置
4. **性能监控** - 集成性能测试和监控工具
5. **文档生成** - 自动生成 API 文档

### 8.2 可维护性

- 脚本模块化，每个函数职责单一
- 添加详细注释和使用文档
- 定期更新依赖版本
- 收集用户反馈持续改进

---

## 9. 总结

本设计方案提供了一个完整的项目初始化和发布解决方案：

✅ **一键启动** - `./init.sh` 即可配置并启动项目
✅ **自动化发布** - `./init.sh --release` 完成完整发布流程
✅ **现代化工具链** - 使用 uv, ruff, pyright 等最新工具
✅ **良好的用户体验** - Rich 美化输出，进度显示，交互确认
✅ **完整的错误处理** - 全局错误捕获，详细日志记录

该方案将显著提升项目的开发体验和发布效率。
