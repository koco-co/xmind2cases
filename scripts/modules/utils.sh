#!/bin/bash
# utils.sh - 通用工具函数模块
# 提供路径设置、版本验证等通用功能

# 设置 PATH（添加指定路径）
setup_path() {
    local new_path="$1"

    # 检查路径是否已存在
    if [[ ":$PATH:" != *":$new_path:"* ]]; then
        export PATH="$new_path:$PATH"
        return 0
    else
        return 1
    fi
}

# 配置 shell 配置文件的 PATH
configure_shell_path() {
    local path_to_add="$1"
    local shell_config=""
    local path_line="export PATH=\"$path_to_add:\$PATH\""

    # 检测 shell 类型
    if [[ -n "$ZSH_VERSION" ]]; then
        shell_config="$HOME/.zshrc"
    elif [[ -n "$BASH_VERSION" ]]; then
        # bash 可能使用 .bashrc 或 .bash_profile
        if [[ -f "$HOME/.bashrc" ]]; then
            shell_config="$HOME/.bashrc"
        elif [[ -f "$HOME/.bash_profile" ]]; then
            shell_config="$HOME/.bash_profile"
        fi
    fi

    # 如果找不到配置文件，创建默认的
    if [[ -z "$shell_config" ]]; then
        if [[ -n "$BASH_VERSION" ]]; then
            shell_config="$HOME/.bashrc"
        else
            shell_config="$HOME/.zshrc"
        fi
    fi

    # 检查配置文件是否已包含该路径
    if [[ -f "$shell_config" ]]; then
        if grep -q "$path_to_add" "$shell_config" 2>/dev/null; then
            return 0
        fi
    fi

    # 添加 PATH 配置
    {
        echo ""
        echo "# uv package manager - added by xmind2cases init script"
        echo "$path_line"
    } >> "$shell_config"

    return 0
}

# 版本比较
# 返回: 0=v1相等, 1=v1更大, 2=v2更大
compare_versions() {
    if [[ "$1" == "$2" ]]; then
        return 0
    fi

    local IFS=.
    local i ver1=($1) ver2=($2)

    # 填充空白位置
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done

    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]} ]]; then
            ver2[i]=0
        fi

        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1
        fi

        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2
        fi
    done

    return 0
}

# 验证最小版本要求
validate_version() {
    local current_version="$1"
    local min_version="$2"
    local package_name="${3:-package}"

    compare_versions "$current_version" "$min_version"
    local result=$?

    if [[ $result -eq 2 ]]; then
        print_error "$package_name 版本过低"
        print_info "当前版本: $current_version"
        print_info "最低要求: $min_version"
        return 1
    fi

    return 0
}

# 检查端口是否可用
check_port_available() {
    local port="$1"

    if command -v lsof &> /dev/null; then
        ! lsof -ti :"$port" &> /dev/null
    elif command -v netstat &> /dev/null; then
        ! netstat -an | grep ":$port" | grep LISTEN &> /dev/null
    else
        # 无法检测，假设可用
        return 0
    fi
}

# 查找可用端口
find_available_port() {
    local start_port="${1:-5002}"
    local max_attempts="${2:-10}"
    local port=$start_port

    for ((i=0; i<max_attempts; i++)); do
        if check_port_available "$port"; then
            echo "$port"
            return 0
        fi
        ((port++))
    done

    echo ""
    return 1
}

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Linux*)
            echo "Linux"
            ;;
        Darwin*)
            echo "macOS"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "Windows"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

# 检测 shell 类型
detect_shell() {
    if [[ -n "$ZSH_VERSION" ]]; then
        echo "zsh"
    elif [[ -n "$BASH_VERSION" ]]; then
        echo "bash"
    else
        echo "unknown"
    fi
}

# 导出函数
export -f setup_path configure_shell_path
export -f compare_versions validate_version
export -f check_port_available find_available_port
export -f detect_os detect_shell
