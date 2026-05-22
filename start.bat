@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

rem 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "VENV_PATH=%SCRIPT_DIR%.venv"
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"

rem 检查虚拟环境是否存在
if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo [91m错误：虚拟环境不存在于 %VENV_PATH%[0m
    echo 请先运行: pyenv local 3.11.9  && uv venv
    pause
    exit /b 1
)

rem 检查后端目录
if not exist "%BACKEND_DIR%\main.py" (
    echo [91m错误：后端目录不存在或缺少 main.py[0m
    pause
    exit /b 1
)

rem 检查前端目录
if not exist "%FRONTEND_DIR%\package.json" (
    echo [91m错误：前端目录不存在或缺少 package.json[0m
    pause
    exit /b 1
)

echo [92m==========================================[0m
echo [92m       MultiUiAutoTest 启动脚本[0m
echo [92m==========================================[0m
echo.
echo 虚拟环境: %VENV_PATH%
echo 后端目录: %BACKEND_DIR%
echo 前端目录: %FRONTEND_DIR%
echo.

rem 激活虚拟环境并启动后端
echo [93m[1/2] 启动后端服务...[0m
    start "Backend - Port 9000" cmd /k "cd /d %BACKEND_DIR% && call %VENV_PATH%\Scripts\activate.bat && echo 虚拟环境已激活: !VIRTUAL_ENV!  && python main.py"

rem 等待后端启动
timeout /t 3 /nobreak > nul

rem 启动前端
echo [93m[2/2] 启动前端服务...[0m
start "Frontend - Port 5174" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"

echo.
echo [92m服务启动完成！[0m
echo 后端地址: [94mhttp://localhost:9000[0m
echo 前端地址: [94mhttp://localhost:5174[0m
echo.
echo 按任意键退出...
pause > nul