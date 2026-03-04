#!/bin/bash
# network.sh - 网络工具模块

check_network() {
    local test_urls=("https://pypi.org" "https://github.com" "https://astral.sh")
    for url in "${test_urls[@]}"; do
        if curl -s --head --connect-timeout 3 "$url" | head -n 1 | grep "HTTP" > /dev/null 2>&1; then
            echo "ok|$url"
            return 0
        fi
    done
    echo "failed|"
    return 1
}

detect_proxy() {
    local proxy_vars=("HTTP_PROXY" "HTTPS_PROXY" "http_proxy" "https_proxy" "ALL_PROXY" "all_proxy")
    for var in "${proxy_vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            echo "found|$var|${!var}"
            return 0
        fi
    done
    if command -v git &> /dev/null; then
        local git_proxy=$(git config --global http.proxy 2>/dev/null)
        if [[ -n "$git_proxy" ]]; then
            echo "found|git|$git_proxy"
            return 0
        fi
    fi
    echo "not_found||"
    return 1
}

download_with_retry() {
    local url="$1" output="$2" max_retries="${3:-3}" timeout="${4:-30}"
    for ((i=1; i<=max_retries; i++)); do
        if curl -fsSL --connect-timeout "$timeout" -o "$output" "$url"; then
            return 0
        fi
        if [ $i -lt $max_retries ]; then
            local wait_time=$((i * 2))
            sleep "$wait_time"
        fi
    done
    return 1
}

export -f check_network detect_proxy download_with_retry
