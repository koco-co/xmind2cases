#!/bin/bash
# 检测器模块单元测试

# 加载被测试模块
source "$(dirname "${BASH_SOURCE[0]}")/../../scripts/modules/detector.sh"
source "$(dirname "${BASH_SOURCE[0]}")/../../scripts/modules/logger.sh"

# 测试框架
run_test() {
    local test_name="$1"
    local test_function="$2"

    echo "测试: $test_name"
    if $test_function; then
        echo "  ✓ 通过"
        return 0
    else
        echo "  ✗ 失败"
        return 1
    fi
}

# 测试 OS 检测
test_detect_os() {
    local os=$(detect_os)
    [[ "$os" =~ ^(Linux|macOS|Windows|Unknown)$ ]]
}

# 测试 uv 检测
test_detect_uv() {
    local result=$(detect_uv)
    # 结果格式应该是 "found|path|version" 或 "not_found||"
    [[ "$result" =~ ^found\|.*\|.*$ ]] || [[ "$result" == "not_found||" ]]
}

# 运行所有测试
main() {
    echo "========================================="
    echo "  检测器模块测试"
    echo "========================================="
    echo ""

    local failed=0

    run_test "OS 检测" "test_detect_os" || ((failed++))
    run_test "uv 检测" "test_detect_uv" || ((failed++))

    echo ""
    if [[ $failed -eq 0 ]]; then
        echo "✓ 所有测试通过"
        return 0
    else
        echo "✗ $failed 个测试失败"
        return 1
    fi
}

main "$@"
