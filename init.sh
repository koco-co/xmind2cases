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
        return 0
    else
        print_warning "uv 未安装"
        echo ""
        print_info "uv 是一个极速的 Python 包管理器，本项目需要它来管理依赖"
        echo ""

        if install_uv_interactive; then
            print_success "uv 安装完成"
            return 0
        else
            print_error "uv 安装失败"
            return 1
        fi
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

# 设置环境
setup_environment() {
    print_step "配置 Python 环境..."

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

    print_success "环境配置完成"
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
    if ! uv run python -c "import xmindparser, flask, arrow" 2>/dev/null; then
        print_error "核心依赖未正确安装"
        exit 1
    fi
    print_info "✓ 依赖已安装"

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

# 启动 Web 工具
start_webtool() {
    print_step "启动 Web 工具..."

    local PORT
    PORT=$(find_available_port 5002)

    if [[ -z "$PORT" ]]; then
        print_error "无法找到可用端口"
        exit 1
    fi

    echo ""
    print_success "Web 工具启动成功！"
    echo ""
    echo "  📱 访问地址: http://127.0.0.1:$PORT"
    echo "  ⏹  按 Ctrl+C 停止服务"
    echo ""

    # 设置 Flask 端口环境变量
    export FLASK_PORT="$PORT"
    uv run python webtool/application.py
}

# 开发流程
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
        print_info "运行 'uv run python -m xmind2cases.cli webtool' 启动 Web 工具"
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
