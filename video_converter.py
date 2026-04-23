"""
视频编码转换器 - 核心转换引擎
支持 H.265 到 H.264 的批量转换，保持原始尺寸和比例
支持视频压缩，可调节压缩程度和清晰度
"""

import subprocess
import os
import re
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable

logger = logging.getLogger(__name__)


@dataclass
class CompressionConfig:
    """压缩配置"""
    crf: int = 28  # 质量参数 18-51，越大压缩越多
    preset: str = "medium"  # 编码速度 ultrafast, fast, medium, slow, veryslow
    target_height: Optional[int] = None  # 目标高度（None=保持原始）
    target_width: Optional[int] = None  # 目标宽度（None=保持原始）
    
    @property
    def quality_label(self) -> str:
        """质量等级标签"""
        if self.crf <= 20:
            return "高质量"
        elif self.crf <= 26:
            return "中等质量"
        elif self.crf <= 32:
            return "标准压缩"
        else:
            return "高压缩"


@dataclass
class VideoInfo:
    """视频文件信息"""
    path: str
    duration: float  # 秒
    width: int
    height: int
    codec: str
    file_size: int  # 字节
    
    @property
    def file_size_mb(self) -> float:
        return self.file_size / (1024 * 1024)
    
    @property
    def duration_str(self) -> str:
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class FFmpegChecker:
    """检查 FFmpeg 是否可用"""
    
    @staticmethod
    def is_available() -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return True, version_line
            return False, "FFmpeg 返回非零退出码"
        except FileNotFoundError:
            return False, "未找到 ffmpeg，请先安装 ffmpeg 并添加到 PATH"
        except Exception as e:
            return False, f"检查 ffmpeg 失败: {str(e)}"


class VideoConverter:
    """视频转换器"""
    
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False
    
    def get_video_info(self, video_path: str) -> VideoInfo:
        """获取视频信息"""
        # 确保路径存在
        if not os.path.exists(video_path):
            raise RuntimeError(f"文件不存在: {video_path}")
        
        # 使用 ffmpeg 获取视频信息（因为 ffprobe 可能不可用）
        result = subprocess.run(
            [
                'ffmpeg', '-i', video_path
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=30
        )
        
        # 从输出中解析视频信息（合并 stdout 和 stderr）
        output = result.stderr if result.stderr else ""
        if not output:
            output = result.stdout if result.stdout else ""
        import re
        
        # 解析分辨率（支持多种格式）
        # 格式1: 1920x1080 [SAR 1:1 DAR 16:9]
        # 格式2: Stream #0:0 ... 1920x1080
        size_match = re.search(r'Video:\s+.*?(\d+)x(\d+)', output, re.DOTALL)
        if not size_match:
            size_match = re.search(r'(\d{2,5})x(\d{2,5})', output)
        
        width = int(size_match.group(1)) if size_match else 0
        height = int(size_match.group(2)) if size_match else 0
        
        # 解析时长
        duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', output)
        if duration_match:
            hours, minutes, seconds, centiseconds = duration_match.groups()
            duration = (
                int(hours) * 3600 +
                int(minutes) * 60 +
                int(seconds) +
                int(centiseconds) / 100
            )
        else:
            duration = 0
        
        # 解析编码器
        codec_match = re.search(r'Video:\s+([^,\n]+)', output)
        codec = codec_match.group(1).strip() if codec_match else 'unknown'
        
        # 文件大小
        file_size = os.path.getsize(video_path)
        
        return VideoInfo(
            path=video_path,
            duration=duration,
            width=width,
            height=height,
            codec=codec,
            file_size=file_size
        )
    
    def _parse_duration_from_output(self, line: str) -> Optional[float]:
        """从 FFmpeg 输出中解析当前时间"""
        match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
        if match:
            hours, minutes, seconds, centiseconds = match.groups()
            return (
                int(hours) * 3600 +
                int(minutes) * 60 +
                int(seconds) +
                int(centiseconds) / 100
            )
        return None
    
    def _parse_speed_from_output(self, line: str) -> Optional[float]:
        """从 FFmpeg 输出中解析速度"""
        match = re.search(r'speed=\s*([\d.]+)x', line)
        if match:
            return float(match.group(1))
        return None
    
    def convert(
        self,
        input_path: str,
        output_path: str,
        mode: str = "convert",  # "convert" 或 "compress"
        compression: Optional[CompressionConfig] = None,
        progress_callback: Optional[Callable[[float, float], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        转换或压缩视频文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            mode: 模式 - "convert"(编码转换) 或 "compress"(压缩)
            compression: 压缩配置（仅 compress 模式需要）
            progress_callback: 进度回调 (current_time, total_duration)
            log_callback: 日志回调
            
        Returns:
            转换是否成功
        """
        self._cancelled = False
        
        video_info = self.get_video_info(input_path)
        total_duration = video_info.duration
        
        if log_callback:
            log_callback(f"开始{'压缩' if mode == 'compress' else '转换'}: {Path(input_path).name}")
            log_callback(f"  原始分辨率: {video_info.width}x{video_info.height}")
            log_callback(f"  时长: {video_info.duration_str}")
            log_callback(f"  大小: {video_info.file_size_mb:.2f} MB")
        
        # 确定输出分辨率
        if mode == "compress" and compression:
            if compression.target_height and compression.target_width:
                # 固定宽高 - 使用 force_original_aspect_ratio 保持比例
                out_width = compression.target_width
                out_height = compression.target_height
                scale_filter = f"scale={out_width}:{out_height}:force_original_aspect_ratio=decrease"
            elif compression.target_height:
                # 只指定高度，宽度自动计算以保持比例
                out_height = compression.target_height
                out_width = -1
                scale_filter = f"scale=-1:{out_height}"
            else:
                out_width = video_info.width
                out_height = video_info.height
                scale_filter = f"scale={out_width}:{out_height}"

            crf = compression.crf
            preset = compression.preset
        else:
            # 编码转换模式：保持原始尺寸，使用默认参数
            out_width = video_info.width
            out_height = video_info.height
            scale_filter = f"scale={out_width}:{out_height}"
            crf = 23
            preset = "medium"
        
        # 确保输出尺寸为偶数（H.264 要求）
        if out_width > 0 and out_height > 0:
            # 对于固定宽高的情况，需要确保都是偶数
            if out_width % 2 != 0:
                out_width += 1
            if out_height % 2 != 0:
                out_height += 1
            scale_filter = f"scale={out_width}:{out_height}"
        elif out_width == -1:
            # 宽度自动计算，确保为偶数
            scale_filter = f"scale=-2:{out_height}"
        elif out_height == -1:
            # 高度自动计算，确保为偶数
            scale_filter = f"scale={out_width}:-2"
        
        if log_callback:
            # 计算实际输出分辨率用于日志
            if out_width == -1:
                actual_width = int(video_info.width * (out_height / video_info.height))
                actual_width = actual_width if actual_width % 2 == 0 else actual_width + 1
                actual_height = out_height
            elif out_height == -1:
                actual_height = int(video_info.height * (out_width / video_info.width))
                actual_height = actual_height if actual_height % 2 == 0 else actual_height + 1
                actual_width = out_width
            else:
                actual_width = out_width
                actual_height = out_height
            
            log_callback(f"  输出分辨率: {actual_width}x{actual_height} (保持原始比例)")
            if mode == "compress":
                log_callback(f"  压缩质量: CRF {crf} ({compression.quality_label})")
                log_callback(f"  编码速度: {preset}")
        
        # FFmpeg 命令
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',  # H.264 编码
            '-preset', preset,
            '-crf', str(crf),
            '-c:a', 'aac',  # 音频编码
            '-b:a', '128k',  # 音频比特率
            '-vf', scale_filter,  # 缩放（保持比例）
            '-movflags', '+faststart',  # 优化网络播放
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        if log_callback:
            log_callback(f"  命令: {' '.join(cmd[0:6])} ...")
        
        try:
            # Windows 下隐藏控制台窗口
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 读取输出并解析进度
            for line in self._process.stdout:
                if self._cancelled:
                    self._process.terminate()
                    if log_callback:
                        log_callback("转换已取消")
                    return False
                
                if log_callback:
                    # 只输出有用的进度信息
                    if 'time=' in line or 'frame=' in line:
                        log_callback(line.strip())
                
                # 解析进度
                if progress_callback and total_duration > 0:
                    current_time = self._parse_duration_from_output(line)
                    if current_time is not None:
                        progress = min(current_time / total_duration, 1.0)
                        speed = self._parse_speed_from_output(line)
                        progress_callback(progress, speed)
            
            # 等待进程结束
            return_code = self._process.wait()
            self._process = None
            
            if return_code == 0:
                if log_callback:
                    log_callback(f"转换完成: {Path(output_path).name}")
                return True
            else:
                if log_callback:
                    log_callback(f"转换失败，退出码: {return_code}")
                return False
                
        except Exception as e:
            if log_callback:
                log_callback(f"转换异常: {str(e)}")
            return False
        finally:
            self._process = None
    
    def cancel(self):
        """取消转换"""
        self._cancelled = True
        if self._process:
            self._process.terminate()
    
    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None
