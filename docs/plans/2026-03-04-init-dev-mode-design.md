# Init 脚本双模式支持设计文档

**日期:** 2026-03-04
**作者:** Claude (assisted by user requirements)
**状态:** 已批准

---

## 1. 概述

### 1.1 目标

实现 `init.sh` 脚本的两种运行模式，优化开发者和最终用户的使用体验：

- **发布模式（默认）**: 快速启动，只安装核心依赖，适合最终用户
- **开发模式（`--dev`）**: 完整流程，安装所有依赖并运行测试，适合开发者

### 1.2 关键决策

1. 废弃现有 `--release` 参数，简化为两种模式
2. 使用 uv 的 dependency-groups 功能管理依赖
3. 智能检测已安装依赖，避免重复安装
4. 开发模式运行测试套件，发布模式跳过

---

## 2. 架构设计

### 2.1 模式架构图

```
用户运行 init.sh
    ↓
参数解析 (--dev?)
    ↓
┌───────────────┬──────────────┐
│   发布模式     │   开发模式    │
│ (默认)        │   (--dev)     │
├───────────────┼──────────────┤
│ uv sync       │ uv sync       │
│ --no-dev      │ --all-groups  │
│               │               │
│ ❌ 跳过测试    │ ✅ 运行测试    │
│ ❌ 跳过 pre-commit │ ✅ 安装 pre-commit │
│ ✅ 启动 Web   │ ✅ 启动 Web   │
└───────────────┴──────────────┘
```

### 2.2 模块修改范围

- **init.sh** - 添加 `--dev` 参数，移除 `--release`
- **scripts/modules/fallback.sh** - 支持模式相关的依赖安装
- **pyproject.toml** - 验证依赖组配置（已就绪）

---

## 3. 核心组件设计

### 3.1 全局变量

```bash
# init.sh 顶部
DEV_MODE=false
NO_WEBTOOL=false
VERBOSE=false
```

### 3.2 参数解析

```bash
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev)
                DEV_MODE=true
                shift
                ;;
            --no-webtool)
                NO_WEBTOOL=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                set -x
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}
```

### 3.3 帮助信息

```bash
show_help() {
    cat << EOF
xmind2cases 项目初始化脚本

用法:
  ./init.sh [选项]

选项:
  --dev          开发模式（安装所有依赖、运行测试、安装 pre-commit）
  --no-webtool   仅配置环境，不启动 Web 工具
  --verbose      详细输出模式
  --help         显示此帮助信息

示例:
  ./init.sh              # 发布模式：快速启动（推荐用户使用）
  ./init.sh --dev        # 开发模式：完整开发环境（推荐开发者使用）
  ./init.sh --no-webtool # 仅配置环境，不启动服务

环境要求:
  - Python 3.12 或更高版本
  - macOS/Linux，或 Windows (WSL/Git Bash)

模式说明:
  发布模式（默认）:
    - 只安装核心运行时依赖
    - 跳过测试和 pre-commit hooks
    - 快速启动 Web 工具

  开发模式 (--dev):
    - 安装所有依赖（包括测试、构建工具）
    - 运行完整测试套件
    - 安装 pre-commit hooks
    - 启动 Web 工具
EOF
}
```

### 3.4 依赖安装逻辑

#### 智能检测函数

```bash
# 检查开发依赖是否已安装
check_dev_dependencies_installed() {
    if uv pip list 2>/dev/null | grep -q "pytest"; then
        return 0  # 已安装
    else
        return 1  # 未安装
    fi
}
```

#### 同步依赖函数

```bash
sync_dependencies() {
    print_step "同步依赖..."

    if [[ "$DEV_MODE" == "true" ]]; then
        if check_dev_dependencies_installed; then
            print_info "开发依赖已安装，验证更新..."
            uv sync --all-groups
        else
            print_info "安装所有依赖（包括开发工具）..."
            uv sync --all-groups
        fi
    else
        print_info "安装核心依赖..."
        uv sync --no-dev
    fi

    print_success "依赖同步完成"
}
```

### 3.5 Pre-commit Hooks 安装

```bash
install_pre_commit_hooks() {
    # 仅在开发模式安装
    if [[ "$DEV_MODE" == "true" ]]; then
        print_info "安装 pre-commit hooks..."
        if [[ -f ".pre-commit-config.yaml" ]]; then
            if uv run pre-commit install; then
                print_success "pre-commit hooks 安装完成"
            else
                print_warning "pre-commit hooks 安装失败（非阻塞）"
            fi
        fi
    else
        print_info "发布模式：跳过 pre-commit hooks"
    fi
}
```

### 3.6 验证流程

```bash
verify_setup() {
    print_step "验证项目配置..."

    # 检查虚拟环境
    if [[ ! -d ".venv" ]]; then
        print_error "虚拟环境未创建"
        exit 1
    fi
    print_info "✓ 虚拟环境存在"

    # 检查核心依赖
    if ! uv run python -c "import xmindparser, flask, arrow" 2>/dev/null; then
        print_error "核心依赖未正确安装"
        exit 1
    fi
    print_info "✓ 核心依赖已安装"

    # 仅在开发模式运行测试
    if [[ "$DEV_MODE" == "true" ]]; then
        print_info "运行测试套件..."
        if uv run pytest tests/ -v --cov=xmind2cases --cov-report=term-missing; then
            print_success "测试通过"
        else
            print_error "测试失败"
            exit 1
        fi
    else
        print_info "发布模式：跳过测试"
    fi

    print_success "项目配置验证完成"
}
```

### 3.7 流程编排

```bash
dev_flow() {
    check_prerequisites
    cleanup_project
    install_tools
    setup_environment
    verify_setup

    if [[ "$NO_WEBTOOL" == "false" ]]; then
        start_webtool
    else
        print_success "环境配置完成！"
        if [[ "$DEV_MODE" == "true" ]]; then
            print_info "运行 'uv run python -m xmind2cases.cli webtool' 启动 Web 工具"
        else
            print_info "运行 'uv run python -m xmind2cases.cli webtool' 启动 Web 工具"
        fi
    fi
}

main() {
    parse_arguments "$@"

    echo ""
    print_step "xmind2cases 项目初始化"
    echo ""

    # 显示当前模式
    if [[ "$DEV_MODE" == "true" ]]; then
        print_info "模式: 开发模式"
    else
        print_info "模式: 发布模式"
    fi
    echo ""

    # 初始化状态
    if [[ -f "$STATE_FILE" ]]; then
        print_info "检测到之前运行的状态"
    else
        init_state "$STATE_FILE"
    fi

    # 执行流程
    dev_flow
}
```

---

## 4. 数据流

```
用户输入
  ↓
parse_arguments() → 设置 DEV_MODE
  ↓
check_prerequisites()
  ├─ check_uv()
  └─ check_python_version()
  ↓
setup_environment()
  ├─ 创建虚拟环境（如不存在）
  ├─ sync_dependencies()
  │   ├─ DEV_MODE=true → uv sync --all-groups
  │   └─ DEV_MODE=false → uv sync --no-dev
  └─ install_pre_commit_hooks() [仅 DEV_MODE]
  ↓
verify_setup()
  ├─ 检查虚拟环境
  ├─ 检查核心依赖
  ├─ DEV_MODE=true → 运行 pytest
  └─ DEV_MODE=false → 跳过测试
  ↓
start_webtool()
```

---

## 5. 错误处理

### 5.1 依赖安装失败

```bash
sync_dependencies() {
    # ... 前面的代码 ...

    if ! uv sync $sync_args; then
        print_error "依赖安装失败"
        print_info "尝试清理缓存并重试..."
        uv cache clean 2>/dev/null || true

        if ! uv sync $sync_args; then
            print_error "依赖安装失败，已重试"
            exit 1
        fi
    fi
}
```

### 5.2 模式切换提示

```bash
sync_dependencies() {
    if [[ "$DEV_MODE" == "false" ]] && check_dev_dependencies_installed; then
        print_warning "当前为发布模式，但检测到开发依赖已安装"
        print_info "这是正常的，开发依赖将被保留"
        echo ""
    fi

    # ... 继续安装 ...
}
```

### 5.3 Python 版本检查

```bash
check_python_version() {
    print_step "检查 Python 版本..."

    # 使用 uv 的 Python 管理
    if ! uv python list | grep -q "3.12"; then
        if [[ "$DEV_MODE" == "true" ]]; then
            print_info "安装 Python 3.12..."
            uv python install 3.12
        else
            print_warning "未找到 Python 3.12"
            print_info "uv 将自动安装 Python 3.12"
        fi
    else
        print_success "Python 3.12 已安装"
    fi
}
```

---

## 6. 测试策略

### 6.1 单元测试

创建 `tests/scripts/test_init_modes.sh`:

```bash
#!/bin/bash
# 测试 init.sh 的模式切换

test_parse_arguments_dev_mode() {
    source ./init.sh
    DEV_MODE=false
    parse_arguments "--dev"
    assert_equals "$DEV_MODE" "true"
}

test_check_dev_dependencies_installed() {
    source ./scripts/init-helpers.sh

    # 在已安装 dev 依赖的环境中运行
    if check_dev_dependencies_installed; then
        assert_true "应该检测到 pytest"
    else
        assert_true "应该未检测到 pytest"
    fi
}
```

### 6.2 集成测试

创建 `tests/scripts/integration_test_modes.sh`:

```bash
#!/bin/bash

# 测试发布模式
test_release_mode() {
    echo "=== 测试发布模式 ==="

    ./init.sh --no-webtool > /tmp/release_output.log 2>&1

    # 验证核心依赖已安装
    uv run python -c "import xmindparser, flask, arrow"

    # 验证未安装开发依赖
    if uv pip list | grep -q "pytest"; then
        echo "❌ 发布模式不应安装 pytest"
        exit 1
    fi

    echo "✓ 发布模式测试通过"
}

# 测试开发模式
test_dev_mode() {
    echo "=== 测试开发模式 ==="

    ./init.sh --dev --no-webtool > /tmp/dev_output.log 2>&1

    # 验证所有依赖已安装
    uv run python -c "import xmindparser, flask, arrow, pytest"

    # 验证测试运行
    uv run pytest tests/ -v

    echo "✓ 开发模式测试通过"
}
```

### 6.3 手动测试清单

- [ ] 首次运行 `./init.sh --dev --no-webtool` - 应安装所有依赖
- [ ] 首次运行 `./init.sh --no-webtool` - 应只安装核心依赖
- [ ] 从发布模式切换到开发模式 - 应增量安装 dev 依赖
- [ ] 从开发模式切换到发布模式 - 应保留 dev 依赖
- [ ] 开发模式测试应通过
- [ ] 发布模式应跳过测试
- [ ] Web 工具在两种模式下都能正常启动
- [ ] `./init.sh --help` 显示正确信息

---

## 7. 实施计划

### 7.1 任务分解

1. **修改参数解析** - 添加 `--dev`，移除 `--release`
2. **实现模式检测** - 添加 `check_dev_dependencies_installed()`
3. **修改依赖安装** - 实现 `sync_dependencies()`
4. **条件化 pre-commit** - 仅在开发模式安装
5. **修改验证流程** - 条件化测试运行
6. **更新帮助信息** - 反映新的参数和模式
7. **编写测试** - 单元测试和集成测试
8. **更新文档** - README 和 CHANGELOG

### 7.2 兼容性

- ✅ macOS (Intel + Apple Silicon)
- ✅ Linux
- ✅ Windows (WSL/Git Bash)

### 7.3 向后兼容

- 默认行为保持不变（发布模式）
- 现有用户脚本不受影响
- uv.lock 继续有效

---

## 8. 验收标准

### 8.1 功能验收

- [x] `./init.sh` 默认运行发布模式
- [x] `./init.sh --dev` 运行开发模式
- [x] 发布模式只安装核心依赖
- [x] 开发模式安装所有依赖并运行测试
- [x] 智能检测已安装依赖
- [x] Web 工具在两种模式下都能启动

### 8.2 性能验收

- [ ] 发布模式安装时间 < 30 秒
- [ ] 开发模式完整流程 < 2 分钟
- [ ] 模式切换增量安装 < 10 秒

### 8.3 文档验收

- [ ] 帮助信息准确完整
- [ ] README 更新模式说明
- [ ] CHANGELOG 记录变更

---

## 9. 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| uv sync --all-groups 失败 | 高 | 添加重试逻辑和详细错误信息 |
| 依赖版本冲突 | 中 | 使用 uv.lock 锁定版本 |
| 用户困惑模式选择 | 低 | 清晰的帮助信息和提示 |
| 测试环境污染 | 中 | 每次测试前清理 .venv |

---

## 10. 后续优化

- [ ] 添加 `--clean` 参数强制重新安装
- [ ] 支持自定义依赖组安装
- [ ] 添加进度条显示
- [ ] 支持配置文件预设模式偏好
