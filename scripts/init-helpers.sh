#!/bin/bash
# init-helpers.sh - 模块加载器和初始化

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULES_DIR="$SCRIPT_DIR/modules"

export SCRIPT_DIR MODULES_DIR

log_module() {
    local module="$1"
    local status="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")

    echo "[$timestamp] [module] $module -> $status" >&2
}

load_module() {
    local module="$1"
    local module_path="$MODULES_DIR/$module.sh"

    if [[ ! -f "$module_path" ]]; then
        log_module "$module" "NOT_FOUND"
        return 1
    fi

    if [[ ! -x "$module_path" ]]; then
        chmod +x "$module_path"
    fi

    # shellcheck source=/dev/null
    source "$module_path"

    log_module "$module" "loaded"
    return 0
}

init_helpers() {
    local modules=(
        "logger"
        "utils"
        "network"
        "detector"
        "installer"
        "error"
        "state"
        "fallback"
    )

    echo "[$(date +"%Y-%m-%d %H:%M:%S")] [init] Initializing helper modules..." >&2

    for module in "${modules[@]}"; do
        if ! load_module "$module"; then
            echo "[$(date +"%Y-%m-%d %H:%M:%S")] [error] Failed to load module: $module" >&2
            return 1
        fi
    done

    echo "[$(date +"%Y-%m-%d %H:%M:%S")] [init] All helper modules loaded successfully" >&2

    return 0
}

init_environment() {
    # Initialize logging
    init_logging

    # Detect OS and shell (export as global variables)
    OS="$(detect_os)"
    SHELL_TYPE="$(detect_shell)"

    export OS
    export SHELL_TYPE
}

# Auto-initialize if sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    init_helpers
    init_environment
fi

export -f load_module init_helpers init_environment log_module
