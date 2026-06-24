#!/bin/bash
# xmind2cases 项目初始化脚本
# 支持: macOS, Linux, Windows (WSL/Git Bash)

set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时退出
set -o pipefail  # 管道命令失败时退出

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载辅助函数
source "$SCRIPT_DIR/scripts/init-helpers.sh"

# 全局变量
DEV_MODE=false
NO_WEBTOOL=false
VERBOSE=false
STATE_FILE="$SCRIPT_DIR/.init-state.json"
USE_UV=true  # 默认使用 uv

# 参数解析
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

# 显示帮助信息
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

环境管理器选择:
  脚本会检测 uv 是否已安装:
  - 如果已安装 uv: 使用 uv 管理 Python 环境（推荐，更快速）
  - 如果未安装 uv: 询问是否安装，或使用默认 pip + venv 环境

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

# 检查/安装 uv
check_uv() {
    print_step "检查 uv 包管理器..."

    local uv_result=$(detect_uv)

    if [[ "$uv_result" == found* ]]; then
        local uv_info="${uv_result#found|}"
        local uv_path="${uv_info%|*}"
        local uv_ver="${uv_info#*|}"

        # 确保在 PATH 中
        setup_path "$(dirname "$uv_path")"

        print_success "uv 已安装: $uv_ver"
        USE_UV=true
        return 0
    else
        print_warning "uv 未安装"
        echo ""
        print_info "uv 是一个极速的 Python 包管理器，推荐使用它来管理依赖"
        print_info "你也可以选择使用默认的 Python 环境来配置项目"
        echo ""

        echo "请选择环境配置方式:"
        echo "  1) 安装 uv（推荐，更快的依赖管理）"
        echo "  2) 使用默认 Python 环境（pip + venv）"
        echo ""
        read -p "请输入选项 (1/2) [默认: 1]: " choice

        case "${choice:-1}" in
            1)
                print_info "正在安装 uv..."
                if install_uv_interactive; then
                    print_success "uv 安装完成"
                    USE_UV=true
                    return 0
                else
                    print_warning "uv 安装失败，将回退到默认 Python 环境"
                    USE_UV=false
                    return 0
                fi
                ;;
            2)
                print_info "将使用默认 Python 环境配置"
                USE_UV=false
                return 0
                ;;
            *)
                print_warning "无效选项，将使用默认 Python 环境配置"
                USE_UV=false
                return 0
                ;;
        esac
    fi
}

# 检查 Python 版本
check_python_version() {
    print_step "检查 Python 版本..."

    local python_result=$(detect_python)

    if [[ "$python_result" == found* ]]; then
        local python_ver="${python_result#*|}"
        print_success "Python: $python_ver"
        return 0
    else
        print_warning "未找到 Python 3.12+"
        print_info "uv 将在需要时自动安装 Python 3.12"
        return 0
    fi
}

# 检查前置条件
check_prerequisites() {
    print_info "操作系统: $OS"
    check_uv
    check_python_version
}

# 清理项目文件
cleanup_project() {
    print_step "清理项目文件..."

    local remove_list=(
        "dist"
        "*.egg-info"
        "htmlcov"
        ".coverage"
        ".pytest_cache"
        ".venv"
        "__pycache__"
        "*.pyc"
        ".idea"
        ".vscode"
        "logs"
        "*.log"
        ".DS_Store"
        "Thumbs.db"
    )

    for item in "${remove_list[@]}"; do
        if [[ "$item" == *"*"* ]]; then
            find . -name "$item" -type f -delete 2>/dev/null || true
            find . -name "$item" -type d -exec rm -rf {} + 2>/dev/null || true
        else
            if [[ -d "$item" ]]; then
                rm -rf "$item" 2>/dev/null || true
            fi
        fi
    done

    print_success "项目清理完成"
}

# 安装开发工具
install_tools() {
    print_step "检查开发工具..."

    # 确保在 PATH 中能找到 uv 安装的工具
    setup_path "$HOME/.local/bin"

    print_success "开发工具检查完成"
}

# 设置环境（使用 uv）
setup_environment_uv() {
    print_step "配置 Python 环境（使用 uv）..."

    # 创建虚拟环境
    if [[ ! -d ".venv" ]]; then
        print_info "创建虚拟环境..."
        uv venv --python 3.12
    else
        print_info "虚拟环境已存在"
    fi

    # 智能同步依赖
    sync_dependencies_smart "$DEV_MODE"

    # 安装 pre-commit hooks（仅开发模式）
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

    print_success "环境配置完成（uv）"
}

# 设置环境（使用默认 Python）
setup_environment_pip() {
    print_step "配置 Python 环境（使用 pip）..."

    # 检查 Python 版本
    local python_result=$(detect_python)
    if [[ "$python_result" != found* ]]; then
        print_error "未找到 Python 3.12+，请先安装 Python"
        exit 1
    fi

    local python_path="${python_result#found|}"
    python_path="${python_path%|*}"
    print_info "使用 Python: $python_path"

    # 创建虚拟环境
    if [[ ! -d ".venv" ]]; then
        print_info "创建虚拟环境..."
        "$python_path" -m venv .venv
    else
        print_info "虚拟环境已存在"
    fi

    # 激活虚拟环境
    print_info "激活虚拟环境..."
    source .venv/bin/activate

    # 升级 pip
    print_info "升级 pip..."
    pip install --upgrade pip -q

    # 安装依赖
    if [[ "$DEV_MODE" == "true" ]]; then
        print_info "安装所有依赖（包括开发工具）..."
        pip install -e ".[dev]" -q
    else
        print_info "安装核心依赖..."
        pip install -e . -q
    fi

    # 安装 pre-commit hooks（仅开发模式）
    if [[ "$DEV_MODE" == "true" ]]; then
        print_info "安装 pre-commit hooks..."
        if [[ -f ".pre-commit-config.yaml" ]]; then
            if pre-commit install; then
                print_success "pre-commit hooks 安装完成"
            else
                print_warning "pre-commit hooks 安装失败（非阻塞）"
            fi
        fi
    else
        print_info "发布模式：跳过 pre-commit hooks"
    fi

    # 取消激活（保持环境一致性）
    deactivate 2>/dev/null || true

    print_success "环境配置完成（pip）"
}

# 设置环境（根据 USE_UV 选择）
setup_environment() {
    if [[ "$USE_UV" == "true" ]]; then
        setup_environment_uv
    else
        setup_environment_pip
    fi
}

# 验证设置
verify_setup() {
    print_step "验证项目配置..."

    # 检查虚拟环境
    if [[ ! -d ".venv" ]]; then
        print_error "虚拟环境未创建"
        exit 1
    fi
    print_info "✓ 虚拟环境存在"

    # 检查核心依赖
    if [[ "$USE_UV" == "true" ]]; then
        if ! uv run python -c "import xmindparser, flask, arrow" 2>/dev/null; then
            print_error "核心依赖未正确安装"
            exit 1
        fi
    else
        if ! .venv/bin/python -c "import xmindparser, flask, arrow" 2>/dev/null; then
            print_error "核心依赖未正确安装"
            exit 1
        fi
    fi
    print_info "✓ 依赖已安装"

    # 仅在开发模式运行测试
    if [[ "$DEV_MODE" == "true" ]]; then
        print_info "运行测试套件..."
        if [[ "$USE_UV" == "true" ]]; then
            if uv run pytest tests/ -v --cov=xmind2cases --cov-report=term-missing; then
                print_success "测试通过"
            else
                print_error "测试失败"
                exit 1
            fi
        else
            if .venv/bin/pytest tests/ -v --cov=xmind2cases --cov-report=term-missing; then
                print_success "测试通过"
            else
                print_error "测试失败"
                exit 1
            fi
        fi
    else
        print_info "发布模式：跳过测试"
    fi

    print_success "项目配置验证完成"
}

# 启动 Web 工具
start_webtool() {
    print_step "启动 Web 工具..."

    local PORT="5002"

    # 如果端口被占用，终止占用进程
    if ! check_port_available "$PORT"; then
        print_warning "端口 $PORT 被占用，正在清理..."
        kill_port_process "$PORT"
        sleep 1
    fi

    echo ""
    print_success "Web 工具启动成功！"
    echo ""
    echo "  📱 访问地址: http://127.0.0.1:$PORT"
    echo "  ⏹  按 Ctrl+C 停止服务"
    echo ""

    # 设置 Flask 端口环境变量
    export FLASK_PORT="$PORT"

    if [[ "$USE_UV" == "true" ]]; then
        uv run python webtool/application.py
    else
        .venv/bin/python webtool/application.py
    fi
}

# 开发流程
dev_flow() {
    check_prerequisites

    # 显示环境类型
    if [[ "$USE_UV" == "true" ]]; then
        print_info "环境管理器: uv（推荐）"
    else
        print_info "环境管理器: pip + venv（默认）"
    fi
    echo ""

    cleanup_project
    install_tools
    setup_environment
    verify_setup

    if [[ "$NO_WEBTOOL" == "false" ]]; then
        start_webtool
    else
        print_success "环境配置完成！"
        if [[ "$USE_UV" == "true" ]]; then
            print_info "运行 'uv run python -m xmind2cases.cli webtool' 启动 Web 工具"
        else
            print_info "运行 '.venv/bin/python -m xmind2cases.cli webtool' 启动 Web 工具"
        fi
    fi
}

# 主函数
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

# 执行主函数
main "$@"
