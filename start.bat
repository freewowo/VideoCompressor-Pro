@echo off
echo 正在启动视频编码转换器...
python gui_app.py
if errorlevel 1 (
    echo.
    echo 错误：Python 未找到或未正确配置
    echo 请确保已安装 Python 3.10+
    pause
)
