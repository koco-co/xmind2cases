# XMind2Cases 快速启动指南

## 📋 前置要求

**无需安装任何东西！** 脚本会自动安装所需工具：

- ✅ **uv** - 极速 Python 包管理器
- ✅ **Python 3.12+** - 自动安装
- ✅ **项目依赖** - 自动同步

---

## 🚀 一键启动

### macOS / Linux / WSL / Git Bash

```bash
# 1. 克隆项目
git clone https://github.com/koco-co/xmind2cases.git
cd xmind2cases

# 2. 运行启动脚本
./init.sh
```

### Windows

**方式 1: 双击运行（推荐）**

1. 克隆项目
   ```cmd
   git clone https://github.com/koco-co/xmind2cases.git
   cd xmind2cases
   ```

2. 双击 `init.bat` 文件即可

**方式 2: 命令行运行**

```cmd
init.bat
```

**方式 3: PowerShell（功能更强大）**

```powershell
# 1. 克隆项目
git clone https://github.com/koco-co/xmind2cases.git
cd xmind2cases

# 2. 运行启动脚本
.\init.ps1
```

**⚠️ Windows 用户注意:**

如果遇到 PowerShell 执行策略限制，请运行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**推荐优先级:**
1. ⭐⭐⭐ **init.bat** - 双击运行，最简单
2. ⭐⭐ **init.ps1** - 功能更强大，更好的错误处理
3. ⭐ **手动安装** - 完全控制每个步骤

---

## 🎯 启动过程

脚本会依次执行以下步骤：

### 1️⃣ 检查 uv 包管理器

```
➜ 检查 uv 包管理器...
⚠ uv 未安装

uv 是一个极速的 Python 包管理器，本项目需要它来管理依赖

是否自动安装 uv? [Y/n]:
```

- **输入 `y` 或直接回车** → 自动安装 uv（推荐）
- **输入 `n`** → 显示手动安装方法并退出

### 2️⃣ 同步项目依赖

```
➜ 同步项目依赖...
✓ 依赖同步完成
```

### 3️⃣ 检查端口占用

```
➜ 检查端口 5002...
⚠ 端口 5002 已被占用

进程信息:
  PID: 12345
  命令: python webtool/application.py

是否要终止占用端口的进程? [Y/n]:
```

- **输入 `y` 或直接回车** → 终止旧进程并继续
- **输入 `n`** → 取消启动

### 4️⃣ 启动 Web 工具

```
✓ Web 工具启动成功！

访问地址: http://127.0.0.1:5002
按 Ctrl+C 停止服务
```

---

## 🌐 访问 Web 工具

启动成功后，在浏览器中打开：

```
http://localhost:5002
```

现在你可以：
- 📤 上传 XMind 文件
- 📊 查看转换后的测试用例
- 📥 导出为 CSV、XML 或 JSON 格式

---

## ❓ 常见问题

### Q: 脚本执行失败怎么办？

**A:** 检查以下几点：

1. **是否有执行权限** (Linux/macOS):
   ```bash
   chmod +x init.sh
   ```

2. **PowerShell 执行策略** (Windows):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **网络连接**:
   - 脚本需要下载 uv，确保网络畅通
   - 如果在国内，可能需要配置代理或镜像

### Q: 可以手动安装吗？

**A:** 当然可以！请参考 [README.md](README.md#手动安装) 章节。

### Q: 端口 5002 被占用怎么办？

**A:** 脚本会自动检测并提供选项：
- 选择 `y` → 自动终止占用进程
- 选择 `n` → 手动终止后重新运行脚本

或者手动终止：
```bash
# macOS/Linux
lsof -ti :5002 | xargs kill -9

# Windows
Get-NetTCPConnection -LocalPort 5002 | Stop-Process
```

### Q: 如何停止 Web 工具？

**A:** 在运行脚本的终端按 `Ctrl+C`

---

## 📚 更多文档

- [完整功能说明](README.md)
- [使用指南](webtool/static/guide/index.html)
- [API 文档](http://localhost:5002/docs) (FastAPI 版本)

---

**遇到问题？** [提交 Issue](https://github.com/koco-co/xmind2cases/issues)
