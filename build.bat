@echo off
chcp 65001 >nul
echo ========================================
echo VideoCompressor Pro - 打包工具
echo ========================================
echo.

echo [1/3] 检查 PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo 错误：PyInstaller 安装失败！
        pause
        exit /b 1
    )
)
echo PyInstaller 已就绪
echo.

echo [2/3] 开始打包...
python -m PyInstaller VideoCompressorPro.spec --clean --noconfirm
if errorlevel 1 (
    echo 错误：打包失败！
    pause
    exit /b 1
)
echo.

echo [3/3] 打包完成！
echo.
echo 输出文件位置: dist\VideoCompressorPro.exe
echo.

if exist "dist\VideoCompressorPro.exe" (
    echo 文件大小:
    for %%A in ("dist\VideoCompressorPro.exe") do echo   %%~zA 字节
    echo.
    echo 是否打开输出文件夹？(Y/N)
    set /p open_folder=
    if /i "%open_folder%"=="Y" (
        explorer dist
    )
) else (
    echo 警告：未找到输出文件！
)

echo.
pause
