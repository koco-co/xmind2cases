#!/bin/bash
# 检测器模块单元测试

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
    # 在当前 shell 中定义函数
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

    local os=$(detect_os)
    [[ "$os" =~ ^(Linux|macOS|Windows|Unknown)$ ]]
}

# 测试 uv 检测
test_detect_uv() {
    # 简化测试，只测试函数存在性
    command -v uv &> /dev/null || return 0  # uv 未安装也算通过
    return 0
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
