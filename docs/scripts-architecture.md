# 初始化脚本架构文档

## 概述

xmind2cases 项目的初始化脚本采用模块化架构设计，将复杂的初始化逻辑拆分为多个可复用的功能模块。

## 架构设计

### 文件结构

```
scripts/
├── init-helpers.sh          # 模块加载器
└── modules/
    ├── logger.sh            # 日志输出
    ├── utils.sh             # 工具函数
    ├── detector.sh          # 智能检测
    ├── network.sh           # 网络工具
    ├── installer.sh         # 安装器
    ├── error.sh             # 错误处理
    ├── state.sh             # 状态管理
    └── fallback.sh          # 回退机制
```

### 模块职责

#### logger.sh
- 提供统一的日志输出接口
- 支持彩色终端输出
- 日志文件记录

#### utils.sh
- PATH 配置和管理
- 版本比较和验证
- 端口检测
- OS 和 shell 类型检测

#### detector.sh
- uv 多路径检测（10+ 种位置）
- 包管理器检测（homebrew/npm/pip/cargo）
- Python 版本检测

#### network.sh
- 网络连接检测
- 代理配置检测
- 下载重试机制

#### installer.sh
- 交互式安装方式选择
- 多种安装方法支持

#### error.sh
- 统一错误处理接口
- 智能问题诊断
- 修复建议生成

#### state.sh
- JSON 状态持久化
- 步骤跳过逻辑
- 诊断信息保存

#### fallback.sh
- 依赖安装多层次回退
- 缓存清理重试

## 设计原则

1. **单一职责** - 每个模块只负责一类功能
2. **幂等性** - 脚本可以安全地重复运行
3. **失败友好** - 每个步骤都有回退机制
4. **平台抽象** - macOS/Linux/Windows 共享核心逻辑

## 扩展指南

### 添加新模块

1. 在 `scripts/modules/` 创建新文件
2. 定义函数并使用 `export -f` 导出
3. 在 `scripts/init-helpers.sh` 中加载
4. 编写单元测试

### 添加新的检测路径

编辑 `scripts/modules/detector.sh`，在 `detect_uv()` 函数中添加新的检查逻辑。

### 添加新的安装方法

编辑 `scripts/modules/installer.sh`，在 `install_uv_interactive()` 函数中添加新的 case 分支。
