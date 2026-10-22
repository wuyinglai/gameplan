@echo off
chcp 65001 >nul
title 余烬商队 · 人工测试台
cd /d "%~dp0"

REM ==== 已经在跑？那就只开浏览器 ====
curl -s -o nul http://localhost:5173/
if %errorlevel%==0 (
  echo 测试台已经在运行了，正在打开浏览器…
  start "" "http://localhost:5173/"
  timeout /t 3 /nobreak >nul
  exit /b 0
)

REM ==== 第一次用要先装依赖 ====
if not exist "node_modules" (
  echo 第一次运行，先装依赖（约一两分钟，装完就不用再装了）
  call npm install
)

echo 正在启动测试台… 这个黑窗口请开着，关掉它测试台就停了。
echo 启动后浏览器会自动打开 http://localhost:5173/
start "打开浏览器" /min cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5173/"
call npx vite --port 5173 --strictPort
pause
