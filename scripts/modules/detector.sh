#!/bin/bash
# detector.sh - 智能检测模块

detect_uv() {
    local uv_info=""

    # 检查 1: 标准 PATH
    if command -v uv &> /dev/null; then
        uv_info="$(command -v uv)|$(uv --version 2>&1 | head -1)"
    fi

    # 检查 2: Homebrew 路径 (macOS - Intel)
    if [[ -z "$uv_info" ]] && [[ -f "/usr/local/bin/uv" ]]; then
        uv_info="/usr/local/bin/uv|uv version unknown"
    fi

    # 检查 3: Homebrew 路径 (macOS - Apple Silicon)
    if [[ -z "$uv_info" ]] && [[ -f "/opt/homebrew/bin/uv" ]]; then
        uv_info="/opt/homebrew/bin/uv|uv version unknown"
    fi

    # 检查 4: npm 全局安装路径
    if [[ -z "$uv_info" ]] && command -v npm &> /dev/null; then
        local npm_prefix=$(npm config get prefix 2>/dev/null)
        if [[ -f "$npm_prefix/bin/uv" ]]; then
            uv_info="$npm_prefix/bin/uv|uv version unknown"
        fi
    fi

    # 检查 5: pip/cargo 安装路径
    if [[ -z "$uv_info" ]]; then
        local local_paths=(
            "$HOME/.local/bin/uv"
            "$HOME/.cargo/bin/uv"
            "$HOME/bin/uv"
        )
        for path in "${local_paths[@]}"; do
            if [[ -f "$path" ]]; then
                uv_info="$path|uv version unknown"
                break
            fi
        done
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
    local python_versions=()

    if command -v python3 &> /dev/null; then
        local version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
        python_versions+=("python3:$version")
    fi

    if command -v python &> /dev/null; then
        local version=$(python --version 2>&1 | grep -oP '\d+\.\d+')
        if [[ ! " ${python_versions[@]} " =~ " python3:$version " ]]; then
            python_versions+=("python:$version")
        fi
    fi

    if command -v python3.12 &> /dev/null; then
        python_versions+=("python3.12:3.12")
    fi

    if command -v python3.11 &> /dev/null; then
        python_versions+=("python3.11:3.11")
    fi

    if command -v python3.10 &> /dev/null; then
        python_versions+=("python3.10:3.10")
    fi

    echo "${python_versions[@]}"
}

check_uv_installation() {
    local uv_path=$(detect_uv)
    if [[ -n "$uv_path" ]]; then
        local version=$("$uv_path" --version 2>&1 | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
        echo "installed|$uv_path|$version"
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
