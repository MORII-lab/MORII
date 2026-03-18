@echo off
setlocal
cd /d "%~dp0"

set "PORT=3000"
set "SITE_URL=http://localhost:%PORT%/"

start "" "%SITE_URL%"

where python >nul 2>nul
if %errorlevel%==0 (
  python -m http.server %PORT%
  goto :end
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -m http.server %PORT%
  goto :end
)

echo.
echo Python 没有找到，无法启动本地网址。
echo 请先安装 Python，然后重新运行这个文件。
pause

:end
endlocal
