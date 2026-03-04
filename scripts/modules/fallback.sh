#!/bin/bash
# fallback.sh - 回退机制模块

install_dependencies_with_fallback() {
    local max_attempts="${1:-3}"
    local attempt=1

    log_info "Starting dependency installation with fallback (max $max_attempts attempts)"

    while [[ $attempt -le $max_attempts ]]; do
        log_info "Attempt $attempt of $max_attempts"

        if install_dependencies_direct; then
            log_info "Dependencies installed successfully on attempt $attempt"
            return 0
        fi

        log_warn "Installation failed on attempt $attempt"

        if [[ $attempt -lt $max_attempts ]]; then
            log_info "Applying fallback strategy..."

            case $attempt in
                1)
                    log_info "Fallback 1: Clearing UV cache and retrying"
                    clear_uv_cache
                    ;;
                2)
                    log_info "Fallback 2: Trying minimal installation"
                    install_dependencies_minimal
                    ;;
                *)
                    log_info "Fallback $attempt: Cleaning up and retrying"
                    cleanup_installation_artifacts
                    ;;
            esac

            local wait_time=$((attempt * 5))
            log_info "Waiting ${wait_time}s before retry..."
            sleep "$wait_time"
        fi

        ((attempt++))
    done

    log_error "Failed to install dependencies after $max_attempts attempts"
    return 1
}

install_dependencies_direct() {
    local uv_result=$(detect_uv)

    if [[ "$uv_result" != found* ]]; then
        log_error "UV not found. Cannot install dependencies."
        return 1
    fi

    # 解析 uv 路径
    local uv_info="${uv_result#found|}"
    local uv_path="${uv_info%|*}"

    log_info "Installing dependencies with UV..."

    if "$uv_path" sync; then
        log_info "Dependencies installed successfully"
        return 0
    else
        log_warn "UV sync failed"
        return 1
    fi
}

install_dependencies_minimal() {
    local uv_result=$(detect_uv)

    if [[ "$uv_result" != found* ]]; then
        log_error "UV not found. Cannot install dependencies."
        return 1
    fi

    # 解析 uv 路径
    local uv_info="${uv_result#found|}"
    local uv_path="${uv_info%|*}"

    log_info "Attempting minimal dependency installation..."

    # Extract core dependencies only
    local core_deps=("pytest" "requests")

    for dep in "${core_deps[@]}"; do
        log_info "Installing core dependency: $dep"
        if "$uv_path" pip install "$dep" --no-deps; then
            log_info "Installed $dep successfully"
        else
            log_warn "Failed to install $dep"
        fi
    done

    return 0
}

clear_uv_cache() {
    log_info "Clearing UV cache..."

    local uv_result=$(detect_uv)
    if [[ "$uv_result" == found* ]]; then
        # 解析 uv 路径
        local uv_info="${uv_result#found|}"
        local uv_path="${uv_info%|*}"
        "$uv_path" cache clean 2>/dev/null || true
        log_info "UV cache cleared"
    fi

    # Clear Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    log_info "Python cache cleared"
}

cleanup_installation_artifacts() {
    log_info "Cleaning up installation artifacts..."

    # Remove incomplete installations
    rm -rf .venv 2>/dev/null || true
    rm -rf uv.lock 2>/dev/null || true

    # Remove build artifacts
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true

    log_info "Cleanup completed"
}

retry_with_different_network() {
    local command="$1"
    local max_retries=3

    log_info "Retrying with network fallback..."

    for ((i=1; i<=max_retries; i++)); do
        log_info "Network attempt $i of $max_retries"

        # Check network status
        local network_status=$(check_network)
        if [[ "${network_status%%|*}" != "ok" ]]; then
            log_warn "Network not available. Waiting..."
            sleep 10
            continue
        fi

        # Try with proxy if available
        local proxy_status=$(detect_proxy)
        if [[ "${proxy_status%%|*}" == "found" ]]; then
            log_info "Using detected proxy"
            export HTTP_PROXY="${proxy_status##*|}"
            export HTTPS_PROXY="${proxy_status##*|}"
        fi

        if eval "$command"; then
            log_info "Command succeeded on attempt $i"
            return 0
        fi

        if [[ $i -lt $max_retries ]]; then
            local wait_time=$((i * 5))
            log_info "Waiting ${wait_time}s before retry..."
            sleep "$wait_time"
        fi
    done

    log_error "Command failed after $max_retries network attempts"
    return 1
}

install_uv_with_fallback() {
    log_info "Attempting UV installation with fallback..."

    local managers=($(detect_package_managers))

    # Try multiple installation methods
    for method in homebrew npm pip cargo curl; do
        log_info "Trying UV installation via $method..."

        case $method in
            homebrew)
                if [[ " ${managers[*]} " =~ " homebrew " ]]; then
                    if install_uv_via_homebrew; then
                        log_info "UV installed via Homebrew"
                        return 0
                    fi
                fi
                ;;
            npm)
                if [[ " ${managers[*]} " =~ " npm " ]]; then
                    if install_uv_via_npm; then
                        log_info "UV installed via NPM"
                        return 0
                    fi
                fi
                ;;
            pip)
                if [[ " ${managers[*]} " =~ " pip " ]]; then
                    if install_uv_via_pip; then
                        log_info "UV installed via Pip"
                        return 0
                    fi
                fi
                ;;
            cargo)
                if [[ " ${managers[*]} " =~ " cargo " ]]; then
                    if install_uv_via_cargo; then
                        log_info "UV installed via Cargo"
                        return 0
                    fi
                fi
                ;;
            curl)
                if [[ " ${managers[*]} " =~ " curl " ]]; then
                    if install_uv_via_curl; then
                        log_info "UV installed via Curl"
                        return 0
                    fi
                fi
                ;;
        esac
    done

    log_error "All UV installation methods failed"
    return 1
}

export -f install_dependencies_with_fallback install_dependencies_direct
export -f install_dependencies_minimal clear_uv_cache cleanup_installation_artifacts
export -f retry_with_different_network install_uv_with_fallback
