#!/usr/bin/env python3
"""文档一致性检查脚本"""

import sys
from pathlib import Path


def check_readme():
    """检查 README.md 中的包名一致性"""
    readme = Path("README.md")

    if not readme.exists():
        print("❌ README.md 文件不存在")
        return False

    content = readme.read_text(encoding="utf-8")

    # 不应出现旧的包名
    if "xmind2testcase" in content:
        print("❌ README.md 中包含旧包名 'xmind2testcase'")
        # 显示出现位置
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if "xmind2testcase" in line:
                print(f"   第 {i} 行: {line.strip()}")
        return False

    # 应包含新包名
    if "xmind2cases" not in content:
        print("❌ README.md 中缺少包名 'xmind2cases'")
        return False

    print("✅ README.md 包名检查通过")
    return True


def check_changelog_version():
    """检查 CHANGELOG 与 pyproject.toml 版本匹配"""
    import tomllib

    pyproject_path = Path("pyproject.toml")
    changelog_path = Path("CHANGELOG.md")

    if not pyproject_path.exists():
        print("❌ pyproject.toml 文件不存在")
        return False

    if not changelog_path.exists():
        print("❌ CHANGELOG.md 文件不存在")
        return False

    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)
    version = pyproject["project"]["version"]

    changelog = changelog_path.read_text(encoding="utf-8")

    # 检查最新版本是否在 CHANGELOG 中
    if f"[{version}]" not in changelog:
        print(f"❌ CHANGELOG.md 中缺少版本 [{version}]")
        print(f"   pyproject.toml 版本: {version}")
        # 显示 CHANGELOG 中的版本
        import re

        versions = re.findall(r"\[(\d+\.\d+\.\d+)\]", changelog)
        if versions:
            print(f"   CHANGELOG 最新版本: {versions[0]}")
        return False

    print(f"✅ CHANGELOG.md 版本 {version} 检查通过")
    return True


def check_no_duplicate_quick_start():
    """检查 README 中没有重复的快速开始部分"""
    readme = Path("README.md")
    content = readme.read_text(encoding="utf-8")

    count = content.count("## 🚀 快速开始")
    if count > 1:
        print(f"❌ README.md 中 '快速开始' 部分重复 {count} 次")
        return False

    print("✅ README.md 无重复内容检查通过")
    return True


def main():
    """主函数"""
    print("=" * 50)
    print("🔍 文档一致性检查")
    print("=" * 50)

    all_passed = True

    all_passed &= check_readme()
    all_passed &= check_changelog_version()
    all_passed &= check_no_duplicate_quick_start()

    print("=" * 50)
    if all_passed:
        print("✅ 所有文档检查通过")
        print("=" * 50)
        return 0
    else:
        print("❌ 文档检查失败")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    sys.exit(main())
