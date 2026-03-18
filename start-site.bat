@echo off
setlocal
cd /d "%~dp0"

set "PORT=3000"
set "SITE_URL=http://localhost:%PORT%/"

if not exist ".env" (
  if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
    echo 已根据 .env.example 创建 .env
    echo 请把 OPENAI_API_KEY 填进去，然后重新运行一次。
    echo.
  )
)

start "" "%SITE_URL%"

where python >nul 2>nul
if %errorlevel%==0 (
  python server.py
  goto :end
)

where py >nul 2>nul
if %errorlevel%==0 (
  py server.py
  goto :end
)

echo.
echo 没有找到 Python，无法启动网站。
echo 请先安装 Python，然后重新运行这个文件。
pause

:end
endlocal
