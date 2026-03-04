#!/bin/bash
# logger.sh - 日志和彩色输出模块
# 提供统一的日志输出接口，支持彩色输出和日志文件记录

# ANSI 颜色代码
readonly COLOR_RESET='\033[0m'
readonly COLOR_BLUE='\033[1;34m'
readonly COLOR_GREEN='\033[1;32m'
readonly COLOR_RED='\033[1;31m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_CYAN='\033[1;36m'

# 日志文件路径（全局变量，由主脚本设置）
LOG_FILE=""

# 初始化日志
init_logging() {
    # 如果 LOG_FILE 为空，设置默认值
    if [[ -z "$LOG_FILE" ]]; then
        LOG_FILE="logs/init-$(date +%Y%m%d-%H%M%S).log"
    fi

    # 提取目录路径
    local log_dir
    log_dir="$(dirname "$LOG_FILE")"

    # 如果目录不存在且不是当前目录，创建它
    if [[ "$log_dir" != "." ]] && [[ ! -d "$log_dir" ]]; then
        mkdir -p "$log_dir" 2>/dev/null || true
    fi

    # 记录开始时间
    echo "=== Session started at $(date -u +"%Y-%m-%d %H:%M:%S UTC") ===" >> "$LOG_FILE" 2>/dev/null || true
}

# 打印步骤信息
print_step() {
    local message="$1"
    echo -e "${COLOR_BLUE}➜${COLOR_RESET} ${COLOR_CYAN}$message${COLOR_RESET}"
    log_message "STEP" "$message"
}

# 打印成功信息
print_success() {
    local message="$1"
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} ${COLOR_GREEN}$message${COLOR_RESET}"
    log_message "SUCCESS" "$message"
}

# 打印错误信息
print_error() {
    local message="$1"
    echo -e "${COLOR_RED}✗${COLOR_RESET} ${COLOR_RED}$message${COLOR_RESET}" >&2
    log_message "ERROR" "$message"
}

# 打印警告信息
print_warning() {
    local message="$1"
    echo -e "${COLOR_YELLOW}⚠${COLOR_RESET} ${COLOR_YELLOW}$message${COLOR_RESET}"
    log_message "WARNING" "$message"
}

# 打印普通信息
print_info() {
    local message="$1"
    echo "  $message"
    log_message "INFO" "$message"
}

# 写入日志文件
log_message() {
    local level="$1"
    local message="$2"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"

    if [[ -n "$LOG_FILE" ]]; then
        echo "[$timestamp] $level: $message" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

# 清理日志文件
cleanup_logging() {
    if [[ -n "$LOG_FILE" ]] && [[ -f "$LOG_FILE" ]]; then
        echo "=== Session ended at $(date -u +"%Y-%m-%d %H:%M:%S UTC") ===" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

# 调试日志（仅日志文件）
log_debug() {
    local message="$1"
    log_message "DEBUG" "$message"
}

# 警告日志（仅日志文件）
log_warn() {
    local message="$1"
    log_message "WARNING" "$message"
}

# 错误日志（仅日志文件）
log_error() {
    local message="$1"
    log_message "ERROR" "$message"
}

# 信息日志（仅日志文件）
log_info() {
    local message="$1"
    log_message "INFO" "$message"
}

# 导出函数供其他模块使用
export -f print_step print_success print_error print_warning print_info
export -f init_logging cleanup_logging
export -f log_debug log_warn log_error log_info
