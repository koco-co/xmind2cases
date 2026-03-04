#!/bin/bash
# detector.sh - 智能检测模块

detect_uv() {
    local uv_info=""

    # 定义所有可能的 uv 安装路径（按优先级排序）
    local uv_paths=(
        "/opt/homebrew/bin/uv"           # Homebrew ARM (Apple Silicon)
        "/usr/local/bin/uv"              # Homebrew Intel
        "$HOME/.local/bin/uv"            # pip/curl 官方安装脚本
        "$HOME/.cargo/bin/uv"            # cargo 安装
        "$HOME/bin/uv"                   # 其他自定义路径
        "/usr/bin/uv"                    # 系统包管理器
        "/opt/uv/bin/uv"                 # 自定义安装
    )

    # 直接检查所有已知路径，避免使用 command -v
    for uv_path in "${uv_paths[@]}"; do
        if [[ -f "$uv_path" ]] && [[ -x "$uv_path" ]]; then
            uv_info="$uv_path|uv version unknown"
            break
        fi
    done

    # 如果直接路径检查失败，尝试使用 PATH（但使用更安全的方式）
    if [[ -z "$uv_info" ]]; then
        # 使用 type 命令代替 command -v（更可靠）
        local uv_loc=""
        if uv_loc=$(type -P uv 2>/dev/null); then
            if [[ -f "$uv_loc" ]]; then
                uv_info="$uv_loc|uv version unknown"
            fi
        fi
    fi

    # 返回检测结果
    if [[ -n "$uv_info" ]]; then
        echo "found|$uv_info"
        return 0
    else
        echo "not_found||"
        return 1
    fi
}

detect_package_managers() {
    local managers=()

    if command -v brew &> /dev/null; then
        managers+=("homebrew")
    fi

    if command -v npm &> /dev/null; then
        managers+=("npm")
    fi

    if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
        managers+=("pip")
    fi

    if command -v cargo &> /dev/null; then
        managers+=("cargo")
    fi

    if command -v curl &> /dev/null || command -v wget &> /dev/null; then
        managers+=("curl")
    fi

    echo "${managers[@]}"
}

detect_python() {
    # 辅助函数：安全地提取 Python 版本（避免 grep -P）
    _extract_version() {
        local output="$1"
        # 使用 sed 代替 grep -P（更好的兼容性）
        echo "$output" | sed -nE 's/.* ([0-9]+\.[0-9]+)\.?[0-9]*.*/\1/p' 2>/dev/null || echo ""
    }

    # 检查 python3
    if [[ -f "/usr/bin/python3" ]] || [[ -f "/usr/local/bin/python3" ]] || [[ -f "/opt/homebrew/bin/python3" ]]; then
        local py3_path=""
        if [[ -f "/opt/homebrew/bin/python3" ]]; then
            py3_path="/opt/homebrew/bin/python3"
        elif [[ -f "/usr/local/bin/python3" ]]; then
            py3_path="/usr/local/bin/python3"
        else
            py3_path="/usr/bin/python3"
        fi

        if [[ -x "$py3_path" ]]; then
            local version_output=$("$py3_path" --version 2>&1 || echo "")
            local version=$(_extract_version "$version_output")
            if [[ -n "$version" ]]; then
                echo "found|$py3_path|$version"
                return 0
            fi
        fi
    fi

    # 检查 python
    if [[ -f "/usr/bin/python" ]] || [[ -f "/usr/local/bin/python" ]]; then
        local py_path=""
        if [[ -f "/usr/local/bin/python" ]]; then
            py_path="/usr/local/bin/python"
        else
            py_path="/usr/bin/python"
        fi

        if [[ -x "$py_path" ]]; then
            local version_output=$("$py_path" --version 2>&1 || echo "")
            local version=$(_extract_version "$version_output")
            if [[ -n "$version" ]]; then
                echo "found|$py_path|$version"
                return 0
            fi
        fi
    fi

    # 检查特定版本（仅文件检查，不执行命令）
    if [[ -f "/opt/homebrew/bin/python3.12" ]] || [[ -f "/usr/local/bin/python3.12" ]]; then
        echo "found|/opt/homebrew/bin/python3.12|3.12"
        return 0
    fi

    if [[ -f "/opt/homebrew/bin/python3.11" ]] || [[ -f "/usr/local/bin/python3.11" ]]; then
        echo "found|/opt/homebrew/bin/python3.11|3.11"
        return 0
    fi

    if [[ -f "/opt/homebrew/bin/python3.10" ]] || [[ -f "/usr/local/bin/python3.10" ]]; then
        echo "found|/opt/homebrew/bin/python3.10|3.10"
        return 0
    fi

    echo "not_found||"
    return 1
}

check_uv_installation() {
    local uv_result=$(detect_uv)
    if [[ "$uv_result" == found* ]]; then
        local uv_info="${uv_result#found|}"
        local uv_path="${uv_info%|*}"
        # 不执行 uv --version 以避免卡住
        echo "installed|$uv_path|version unknown"
        return 0
    fi
    echo "not_found||"
    return 1
}

analyze_environment() {
    echo "=== Environment Analysis ==="

    echo "OS: $(uname -s) $(uname -m)"
    echo "Shell: $SHELL"

    echo -e "\n--- UV Status ---"
    check_uv_installation

    echo -e "\n--- Package Managers ---"
    local managers=($(detect_package_managers))
    if [[ ${#managers[@]} -gt 0 ]]; then
        echo "Found: ${managers[*]}"
    else
        echo "No package managers found"
    fi

    echo -e "\n--- Python Versions ---"
    local py_versions=($(detect_python))
    if [[ ${#py_versions[@]} -gt 0 ]]; then
        echo "Found: ${py_versions[*]}"
    else
        echo "No Python found"
    fi

    echo -e "\n--- Network Status ---"
    source "$(dirname "${BASH_SOURCE[0]}")/network.sh"
    local network_status=$(check_network)
    echo "Network: ${network_status%|*}"

    local proxy_status=$(detect_proxy)
    if [[ "${proxy_status%%|*}" == "found" ]]; then
        echo "Proxy: ${proxy_status#*|}"
    else
        echo "Proxy: Not configured"
    fi
}

export -f detect_uv detect_package_managers detect_python check_uv_installation analyze_environment
