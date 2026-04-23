# VideoCompressor Pro - 视频编码转换与压缩工具

一个功能完整的 Windows 桌面视频处理工具，支持 H.265 到 H.264 的编码转换和视频压缩，具有批量处理、实时进度显示和剩余时间预估功能。

## ✨ 功能特性

### 双模式支持

**🔄 编码转换模式**
- H.265 (HEVC) → H.264 (AVC) 编码转换
- 保持原始视频质量和分辨率
- 兼容更多播放设备和平台

**📦 视频压缩模式**
- 可调节压缩程度（CRF 22-40）
- 多档清晰度选择：480p / 720p / 1080p / 2K / 4K / 原始
- 编码速度可调：快 / 中 / 慢 / 最慢
- 自动保持原始画面比例，不裁剪

### 批量处理
- 支持添加多个视频文件
- 支持整个文件夹批量导入
- 支持格式：MP4 / MKV / AVI / MOV / FLV / WMV / WebM

### 用户体验
- 🎨 现代化 GUI 操作面板
- 📊 实时双进度条显示（当前文件 + 总体进度）
- ⏱️ 智能剩余时间预估
- 📝 详细转换日志输出
- 📁 一键打开输出文件夹
- 🚫 隐藏 FFmpeg 控制台窗口

## 🖥️ 系统要求

- **操作系统：** Windows 10 或 Windows 11
- **Python：** 3.10 或更高版本（仅开发需要）
- **FFmpeg：** 必须安装并添加到 PATH，或与程序放在同一目录

## 📥 安装与使用

### 方法一：直接使用打包程序（推荐）

1. 下载 `VideoCompressorPro.exe` 和 `ffmpeg.exe`
2. 将两个文件放在**同一文件夹**内
3. 双击 `VideoCompressorPro.exe` 运行

### 方法二：从源代码运行

```bash
# 1. 克隆项目
git clone https://github.com/freewowo/VideoCompressor-Pro.git
cd VideoCompressor-Pro

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python gui_app.py
```

**注意：** 需要确保 `ffmpeg.exe` 在系统 PATH 中或与程序在同一目录

## 🎯 使用指南

### 编码转换（H.265 → H.264）

1. 选择"编码转换 (H.265→H.264)"模式
2. 点击"添加文件"或"添加文件夹"导入视频
3. 选择输出目录（或使用源文件目录）
4. 点击"开始转换"

### 视频压缩

1. 选择"视频压缩"模式
2. 设置压缩参数：
   - **清晰度：** 选择目标分辨率
   - **压缩程度：** 高质量 / 中等 / 标准 / 高压缩
   - **编码速度：** 快 / 中 / 慢 / 最慢
3. 添加视频文件
4. 选择输出目录
5. 点击"开始压缩"

### 压缩参数说明

**压缩程度（CRF 值）**

| 选项 | CRF 值 | 质量 | 文件大小 |
|------|--------|------|---------|
| 高质量 | 22 | 优秀 | 较大 |
| 中等 | 28 | 良好 | 适中 |
| 标准 | 32 | 可接受 | 较小 |
| 高压缩 | 40 | 一般 | 最小 |

**清晰度选项**

| 选项 | 输出高度 | 适用场景 |
|------|---------|---------|
| 原始 | 保持源文件 | 不改变分辨率 |
| 480p | 480px | 手机观看，文件最小 |
| 720p | 720px | 网络分享，平衡质量 |
| 1080p | 1080px | 高清观看 |
| 2K | 1440px | 高质量 |
| 4K | 2160px | 超高清 |

## 🏗️ 项目结构

```
VideoCompressor-Pro/
├── gui_app.py                    # GUI 主程序
├── video_converter.py            # 转换引擎
├── VideoCompressorPro.spec       # PyInstaller 打包配置
├── requirements.txt              # Python 依赖
├── build.bat                     # Windows 打包脚本
├── start.bat                     # Windows 启动脚本
├── app_icon.ico                  # 程序图标
├── ffmpeg.exe                    # FFmpeg 工具（需单独下载）
├── README.md                     # 项目说明文档
└── README_用户.md                # 用户使用手册
```

## 📦 打包发布

### 自动打包（推荐）

双击运行 `build.bat`，脚本会自动：
1. 检查并安装 PyInstaller
2. 打包程序为 exe
3. 显示输出文件位置

### 手动打包

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包程序
pyinstaller VideoCompressorPro.spec --clean --noconfirm
```

打包完成后，exe 文件位于：`dist\VideoCompressorPro.exe`

### 发布清单

创建以下结构的发布包：

```
VideoCompressorPro_v1.0/
├── VideoCompressorPro.exe      # 主程序
├── ffmpeg.exe                   # FFmpeg 工具
└── README_用户.md               # 使用说明
```

## ⚙️ 技术细节

### 编码参数

**编码转换模式**
- 编码：H.264 (libx264)
- 质量：CRF 23
- 速度：preset medium
- 音频：AAC 128kbps
- 尺寸：保持原始分辨率

**视频压缩模式**
- 编码：H.264 (libx264)
- 质量：用户可调 CRF 18-51
- 速度：用户可调 preset
- 音频：AAC 128kbps
- 尺寸：按比例缩放，不裁剪

### 输出文件命名

- 编码转换：`原文件名_h264.mp4`
- 视频压缩：`原文件名_compressed_720p_crf28.mp4`

## ❓ 常见问题

**Q: 提示"FFmpeg 不可用"？**  
A: 请确保 FFmpeg 已正确安装并添加到系统 PATH，或将 `ffmpeg.exe` 与程序放在同一目录。

**Q: 转换速度慢？**  
A: H.264 编码需要时间。可在压缩模式中选择更快的编码速度（fast），但质量会略低。

**Q: 输出文件太大？**  
A: 使用"视频压缩"模式，调高 CRF 值或降低分辨率可显著减小文件大小。

**Q: 压缩后质量太差？**  
A: 降低 CRF 值（如从 40 改为 28），或选择更慢的编码速度（slow/veryslow）。

**Q: 视频尺寸比例变化？**  
A: 程序已自动保持原始比例。如仍有问题，请检查输出日志中的分辨率信息。

## 📄 许可证

本项目仅供学习和个人使用。

## 🙏 致谢

- [FFmpeg](https://ffmpeg.org/) - 强大的多媒体框架
- [PyInstaller](https://pyinstaller.org/) - Python 打包工具
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - Python GUI 库

---

**版本：** 1.0  
**更新日期：** 2026-04-23
