#!/bin/bash
# xmind2cases 项目初始化脚本
# 支持: macOS, Linux, Windows (WSL/Git Bash)

set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时退出
set -o pipefail  # 管道命令失败时退出

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 全局变量
RELEASE_MODE=false
NO_WEBTOOL=false
LOG_FILE="init-$(date +%Y%m%d-%H%M%S).log"

# 颜色输出函数
print_step() {
    echo -e "\033[1;34m➜\033[0m \033[1;36m$1\033[0m"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] STEP: $1" >> "$LOG_FILE"
}

print_success() {
    echo -e "\033[1;32m✓\033[0m \033[1;32m$1\033[0m"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "\033[1;31m✗\033[0m \033[1;31m$1\033[0m" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOG_FILE"
}

print_warning() {
    echo -e "\033[1;33m⚠\033[0m \033[1;33m$1\033[0m"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "$LOG_FILE"
}

print_info() {
    echo -e "  $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> "$LOG_FILE"
}

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Linux*)
            OS="Linux"
            ;;
        Darwin*)
            OS="macOS"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            OS="Windows"
            ;;
        *)
            OS="Unknown"
            ;;
    esac
}

# 检查/安装 uv
check_uv() {
    print_step "检查 uv 包管理器..."

    if command -v uv &> /dev/null; then
        local uv_version=$(uv --version 2>&1 | head -1)
        print_success "uv 已安装: $uv_version"
        return 0
    else
        print_warning "uv 未安装，正在安装..."
        if curl -LsSf https://astral.sh/uv/install.sh | sh; then
            export PATH="$HOME/.local/bin:$PATH"
            print_success "uv 安装完成"
            return 0
        else
            print_error "uv 安装失败"
            print_info "请手动安装: https://github.com/astral-sh/uv"
            exit 1
        fi
    fi
}

# 检查 Python 版本（通过 uv）
check_python_version() {
    print_step "检查 Python 版本..."

    local min_version="3.12.12"

    # 首先尝试获取 uv 管理的 Python 版本
    if command -v uv &> /dev/null; then
        # 检查是否有已安装的符合条件的 Python 版本
        local available_python=$(uv python list 2>/dev/null | grep -E "3\.(1[2-9]|[2-9][0-9])" | head -1 || true)

        if [[ -n "$available_python" ]]; then
            local python_version=$(echo "$available_python" | awk '{print $1}')
            print_success "找到 uv 管理的 Python: $python_version"
            return 0
        fi

        # 尝试查找系统可用的 Python 3.12+
        if uv python find 3.12 &> /dev/null; then
            print_success "uv 可以安装 Python 3.12+"
            print_info "将在需要时自动安装"
            return 0
        fi

        # 如果都找不到，提示用户
        print_warning "未找到 Python 3.12.12 或更高版本"
        print_info "uv 将在创建虚拟环境时自动安装 Python 3.12"
        return 0
    fi

    # 降级到系统 Python 检查
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1 | awk '{print $2}')
        if ! printf '%s\n' "$min_version" "$python_version" | sort -V -C; then
            print_warning "系统 Python 版本: $python_version (要求 >= $min_version)"
            print_info "uv 将自动安装符合要求的 Python 版本"
            return 0
        fi
        print_success "系统 Python 版本: $python_version"
    else
        print_warning "未找到系统 Python"
        print_info "uv 将自动安装 Python 3.12"
    fi
}

# 检查前置条件
check_prerequisites() {
    detect_os
    print_info "操作系统: $OS"
    check_uv
    check_python_version
}

# 清理项目文件
cleanup_project() {
    print_step "清理项目文件..."

    # 需要删除的文件和目录
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

    # 使用 find 命令删除匹配的文件
    for item in "${remove_list[@]}"; do
        if [[ "$item" == *"*"* ]]; then
            # 处理通配符
            find . -name "$item" -type f -delete 2>/dev/null || true
            find . -name "$item" -type d -exec rm -rf {} + 2>/dev/null || true
        else
            # 处理固定名称
            if [[ -d "$item" ]]; then
                rm -rf "$item" 2>/dev/null || true
            fi
            find . -name "$item" -type d -exec rm -rf {} + 2>/dev/null || true
        fi
    done

    print_success "项目清理完成"
}

# 安装单个工具
install_tool() {
    local tool=$1
    local check_cmd=$2

    if eval "$check_cmd &> /dev/null"; then
        print_success "$tool 已安装"
    else
        print_step "安装 $tool..."
        if uv tool install "$tool"; then
            print_success "$tool 安装完成"
        else
            print_error "$tool 安装失败"
            return 1
        fi
    fi
}

# 安装开发工具
install_tools() {
    print_step "检查开发工具..."

    # 确保在 PATH 中能找到 uv 安装的工具
    export PATH="$HOME/.local/bin:$PATH"

    # 安装 ruff
    install_tool "ruff" "command -v ruff"

    # 安装 pyright
    install_tool "pyright" "command -v pyright"

    # 安装 pre-commit
    install_tool "pre-commit" "command -v pre-commit"

    print_success "开发工具检查完成"
}

# 参数解析
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --release)
                RELEASE_MODE=true
                shift
                ;;
            --no-webtool)
                NO_WEBTOOL=true
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
  --release       启用发布模式（测试、构建、发布到 GitHub 和 PyPI）
  --no-webtool    仅配置环境，不启动 Web 工具
  --help          显示此帮助信息

示例:
  ./init.sh                # 配置环境并启动 Web 工具
  ./init.sh --no-webtool   # 仅配置环境
  ./init.sh --release      # 完整发布流程

环境要求:
  - Python 3.12.12 或更高版本
  - macOS/Linux，或 Windows (WSL/Git Bash)

发布模式环境变量:
  - UV_PUBLISH_TOKEN    PyPI 发布令牌（必需）
EOF
}

# 主函数
main() {
    parse_arguments "$@"

    echo ""
    print_step "xmind2cases 项目初始化"
    echo ""

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
    if [[ "$NO_WEBTOOL" == "false" ]]; then
        start_webtool
    else
        print_success "环境配置完成！"
        print_info "运行 'python -m xmind2testcase.cli webtool' 启动 Web 工具"
    fi
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
    print_release_summary
}

# 执行主函数
main "$@"
