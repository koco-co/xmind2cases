@echo off
REM XMind2Cases Windows 快速启动脚本
REM 批处理版本 - 双击即可运行

setlocal enabledelayedexpansion

REM 颜色设置（Windows 10+ 支持 ANSI 转义序列）
set "SUCCESS=[92m"
set "ERROR=[91m"
set "WARNING=[93m"
set "INFO=[94m"
set "RESET=[0m"

echo.
echo ========================================
echo   XMind2Cases 快速启动
echo ========================================
echo.

REM 检查 uv
echo [94m➜[0m 检查 uv 包管理器...
where uv >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('uv --version') do set UV_VERSION=%%i
    echo [92m✓[0m uv 已安装: %UV_VERSION%
) else (
    echo [93m⚠[0m uv 未安装
    echo.
    echo   uv 是一个极速的 Python 包管理器
    echo.
    set /p INSTALL_UV="是否自动安装 uv? [Y/n]: "

    if /i "!INSTALL_UV!"=="n" (
        echo [91m✗[0m 用户取消安装
        echo.
        echo   手动安装方法:
        echo   1. 访问 https://github.com/astral-sh/uv#installation
        echo   2. 或运行: powershell -c "irm https://astral.sh/uv/install.ps1 ^| iex"
        pause
        exit /b 1
    )

    echo [94m  正在安装 uv...[0m
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo [91m✗[0m uv 安装失败
        echo.
        echo   请手动安装: https://github.com/astral-sh/uv#installation
        pause
        exit /b 1
    )
    echo [92m✓[0m uv 安装完成
    REM 刷新环境变量
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

echo.

REM 同步依赖
echo [94m➜[0m 同步项目依赖...
uv sync
if %errorlevel% neq 0 (
    echo [91m✗[0m 依赖同步失败
    pause
    exit /b 1
)
echo [92m✓[0m 依赖同步完成
echo.

REM 检查端口占用
echo [94m➜[0m 检查端口 5002...
netstat -ano | findstr ":5002" >nul 2>&1
if %errorlevel% equ 0 (
    echo [93m⚠[0m 端口 5002 已被占用
    echo.

    REM 获取占用端口的 PID
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5002"') do (
        set PID=%%a
        goto :found_pid
    )
    :found_pid

    echo   进程信息:
    echo   PID: [91m!PID![0m
    echo.

    set /p KILL_PROCESS="是否要终止占用端口的进程? [Y/n]: "

    if /i "!KILL_PROCESS!"=="n" (
        echo [91m✗[0m 用户取消启动
        pause
        exit /b 1
    )

    echo [94m  正在终止进程 !PID!...[0m
    taskkill /F /PID !PID! >nul 2>&1
    if %errorlevel% neq 0 (
        echo [91m✗[0m 无法终止进程
        echo   请手动执行: taskkill /F /PID !PID!
        pause
        exit /b 1
    )
    echo [92m✓[0m 进程已终止
    timeout /t 1 /nobreak >nul
)

echo.

REM 启动 webtool
echo [94m➜[0m 启动 Web 工具...
echo.
echo [92m✓[0m Web 工具启动成功！
echo.
echo   访问地址: [96mhttp://127.0.0.1:5002[0m
echo   按 Ctrl+C 停止服务
echo.
echo ========================================
echo.

REM 启动 FastAPI 服务器
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 5002 --reload
