"""
视频编码转换器 - GUI 操作面板
支持批量转换、进度显示和剩余时间预估
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from video_converter import VideoConverter, FFmpegChecker, VideoInfo, CompressionConfig


class ConverterApp:
    """视频转换器主界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VideoCompressor Pro - 视频编码转换与压缩工具")
        self.root.geometry("900x750")
        self.root.minsize(850, 650)
        
        self.converter = VideoConverter()
        self.file_queue: list[str] = []  # 待转换文件队列
        self.current_index: int = 0
        self.is_converting = False
        self.start_time: Optional[datetime] = None
        
        # 转换模式和压缩配置
        self.mode_var = tk.StringVar(value="convert")  # "convert" 或 "compress"
        self.crf_var = tk.IntVar(value=28)
        self.resolution_var = tk.StringVar(value="720")  # 目标高度
        self.preset_var = tk.StringVar(value="medium")
        
        self._setup_ui()
        self._check_ffmpeg()
    
    def _setup_ui(self):
        """设置界面"""
        # 顶部：文件选择区域
        file_frame = ttk.LabelFrame(self.root, text="文件选择", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(
            btn_frame,
            text="添加文件",
            command=self._add_files
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="添加文件夹",
            command=self._add_folder
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="清空列表",
            command=self._clear_list
        ).pack(side=tk.LEFT, padx=5)
        
        # 输出目录选择
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(output_frame, text="输出目录:").pack(side=tk.LEFT)
        
        self.output_path = tk.StringVar(value="")
        ttk.Entry(
            output_frame,
            textvariable=self.output_path,
            width=50
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(
            output_frame,
            text="浏览",
            command=self._select_output_dir
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            output_frame,
            text="使用源目录",
            command=self._use_source_dir
        ).pack(side=tk.LEFT, padx=5)
        
        # 转换模式和参数设置
        settings_frame = ttk.LabelFrame(self.root, text="转换设置", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 模式选择
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(mode_frame, text="转换模式:").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            mode_frame,
            text="编码转换 (H.265→H.264)",
            variable=self.mode_var,
            value="convert",
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            mode_frame,
            text="视频压缩",
            variable=self.mode_var,
            value="compress",
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=5)
        
        # 压缩参数设置 - 使用独立的Frame
        self.compress_frame = ttk.LabelFrame(self.root, text="压缩参数", padding=10)
        # 注意：不pack，默认隐藏
        
        # 第一行：清晰度和压缩程度在同一行
        param_row1 = ttk.Frame(self.compress_frame)
        param_row1.pack(fill=tk.X, pady=5)
        
        # 清晰度选择
        ttk.Label(param_row1, text="清晰度:").pack(side=tk.LEFT, padx=(0, 5))
        
        resolutions = [
            ("原始", "0"),
            ("480p", "480"),
            ("720p", "720"),
            ("1080p", "1080"),
            ("2K", "1440"),
            ("4K", "2160")
        ]
        
        for text, value in resolutions:
            ttk.Radiobutton(
                param_row1,
                text=text,
                variable=self.resolution_var,
                value=value,
                command=self._update_preview
            ).pack(side=tk.LEFT, padx=3)
        
        # 压缩程度
        ttk.Label(param_row1, text="压缩程度:").pack(side=tk.LEFT, padx=(20, 5))
        
        quality_frame = ttk.Frame(param_row1)
        quality_frame.pack(side=tk.LEFT)
        
        qualities = [
            ("高质量", 22),
            ("中等", 28),
            ("标准", 32),
            ("高压缩", 40)
        ]
        
        for text, value in qualities:
            btn = ttk.Radiobutton(
                quality_frame,
                text=text,
                variable=self.crf_var,
                value=value,
                command=self._update_preview
            )
            btn.pack(side=tk.LEFT, padx=3)
        
        # 第二行：编码速度和预览
        param_row2 = ttk.Frame(self.compress_frame)
        param_row2.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_row2, text="编码速度:").pack(side=tk.LEFT, padx=(0, 5))
        
        presets = [
            ("快", "fast"),
            ("中", "medium"),
            ("慢", "slow"),
            ("最慢", "veryslow")
        ]
        
        for text, value in presets:
            ttk.Radiobutton(
                param_row2,
                text=text,
                variable=self.preset_var,
                value=value
            ).pack(side=tk.LEFT, padx=3)
        
        # 参数预览
        self.preview_label = tk.Label(
            param_row2,
            text="",
            fg="gray",
            anchor=tk.E
        )
        self.preview_label.pack(side=tk.RIGHT)

        # 中间：文件列表
        list_frame = ttk.LabelFrame(self.root, text="待转换文件", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建树形视图
        columns = ("#", "文件名", "分辨率", "时长", "大小", "编码", "状态")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=10
        )
        
        # 设置列
        column_widths = {
            "#": 40,
            "文件名": 300,
            "分辨率": 100,
            "时长": 80,
            "大小": 80,
            "编码": 80,
            "状态": 100
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 底部：进度和控制区域
        control_frame = ttk.LabelFrame(self.root, text="转换控制", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 进度条
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(progress_frame, text="总体进度:").pack(side=tk.LEFT)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.progress_label = tk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT)
        
        # 当前文件进度
        current_progress_frame = ttk.Frame(control_frame)
        current_progress_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(current_progress_frame, text="当前文件:").pack(side=tk.LEFT)
        
        self.current_progress_var = tk.DoubleVar()
        self.current_progress_bar = ttk.Progressbar(
            current_progress_frame,
            variable=self.current_progress_var,
            maximum=100
        )
        self.current_progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.current_progress_label = tk.Label(current_progress_frame, text="0%")
        self.current_progress_label.pack(side=tk.LEFT)
        
        # 状态信息
        info_frame = ttk.Frame(control_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(info_frame, text="就绪", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.time_label = tk.Label(info_frame, text="剩余时间: --:--:--", anchor=tk.E)
        self.time_label.pack(side=tk.RIGHT)
        
        # 控制按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.start_btn = ttk.Button(
            button_frame,
            text="开始转换",
            command=self._start_conversion
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(
            button_frame,
            text="取消",
            command=self._cancel_conversion,
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        self.open_folder_btn = ttk.Button(
            button_frame,
            text="打开输出文件夹",
            command=self._open_output_folder
        )
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)

        # 初始化显示（必须在所有控件创建后调用）
        self._on_mode_change()

        # 日志区域
        log_frame = ttk.LabelFrame(self.root, text="日志", padding=10)
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=6, state=tk.DISABLED, yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        log_scroll.config(command=self.log_text.yview)
    
    def _check_ffmpeg(self):
        """检查 FFmpeg 是否可用"""
        available, message = FFmpegChecker.is_available()
        if not available:
            messagebox.showerror(
                "FFmpeg 不可用",
                f"{message}\n\n请安装 FFmpeg 并将其添加到系统 PATH。\n"
                f"可以从 https://ffmpeg.org/download.html 下载。"
            )
            self._log(message)
        else:
            self._log(f"FFmpeg 可用: {message}")
    
    def _on_mode_change(self):
        """转换模式改变时的处理"""
        if self.mode_var.get() == "compress":
            # 显示压缩参数设置 - 在settings_frame之后
            settings_frame = None
            list_frame = None
            for child in self.root.winfo_children():
                if isinstance(child, ttk.LabelFrame):
                    text = child.cget("text")
                    if text == "转换设置":
                        settings_frame = child
                    elif text == "待转换文件":
                        list_frame = child
            
            if settings_frame and list_frame:
                self.compress_frame.pack(fill=tk.X, padx=10, pady=5, after=settings_frame, before=list_frame)
            
            self._update_preview()
            # 更新按钮文字
            if hasattr(self, 'start_btn'):
                self.start_btn.config(text="开始压缩")
            # 调整窗口大小以确保所有内容可见
            self.root.geometry("900x850")
        else:
            # 隐藏压缩参数设置
            self.compress_frame.pack_forget()
            # 更新按钮文字
            if hasattr(self, 'start_btn'):
                self.start_btn.config(text="开始转换")
            # 恢复窗口大小
            self.root.geometry("900x750")
    
    def _update_preview(self):
        """更新参数预览"""
        if self.mode_var.get() != "compress":
            return
        
        crf = self.crf_var.get()
        resolution = self.resolution_var.get()
        preset = self.preset_var.get()
        
        # 计算压缩配置
        if resolution == "0":
            res_text = "原始分辨率"
        else:
            res_text = f"{resolution}p"
        
        comp = CompressionConfig(crf=crf, target_height=int(resolution) if resolution != "0" else None)
        
        preview_text = f"CRF {crf} ({comp.quality_label}) | {res_text} | {preset}"
        self.preview_label.config(text=preview_text)
    
    def _log(self, message: str):
        """添加日志消息"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _add_files(self):
        """添加文件到队列"""
        files = filedialog.askopenfilenames(
            title="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv *.webm"),
                ("所有文件", "*.*")
            ]
        )
        
        for file_path in files:
            self._add_file_to_queue(file_path)
    
    def _add_folder(self):
        """添加文件夹中的所有视频文件"""
        folder = filedialog.askdirectory(title="选择视频文件夹")
        if folder:
            video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm'}
            for root, dirs, files in os.walk(folder):
                for file in sorted(files):
                    if Path(file).suffix.lower() in video_extensions:
                        file_path = os.path.join(root, file)
                        self._add_file_to_queue(file_path)
    
    def _add_file_to_queue(self, file_path: str):
        """添加单个文件到队列"""
        # 规范化路径
        file_path = os.path.normpath(file_path)
        
        # 检查是否已存在
        if file_path in self.file_queue:
            return
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            self._log(f"文件不存在: {file_path}")
            return
        
        self.file_queue.append(file_path)
        index = len(self.file_queue)
        
        # 获取文件信息
        try:
            info = self.converter.get_video_info(file_path)
            self.tree.insert("", tk.END, values=(
                index,
                Path(file_path).name,
                f"{info.width}x{info.height}",
                info.duration_str,
                f"{info.file_size_mb:.1f}MB",
                info.codec,
                "等待中"
            ))
        except Exception as e:
            self._log(f"无法读取文件信息 {file_path}: {e}")
            self.tree.insert("", tk.END, values=(
                index,
                Path(file_path).name,
                "-",
                "-",
                "-",
                "-",
                "错误"
            ))
    
    def _clear_list(self):
        """清空文件列表"""
        if self.is_converting:
            messagebox.showwarning("警告", "转换进行中无法清空列表")
            return
        
        self.file_queue.clear()
        self.current_index = 0
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._log("已清空文件列表")
    
    def _select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_path.set(directory)
    
    def _use_source_dir(self):
        """使用源文件目录作为输出目录"""
        self.output_path.set("")
        self._log("将使用源文件目录作为输出目录")
    
    def _start_conversion(self):
        """开始转换"""
        if not self.file_queue:
            messagebox.showwarning("警告", "请先添加视频文件")
            return
        
        if self.is_converting:
            return
        
        self.is_converting = True
        self.current_index = 0
        self.start_time = datetime.now()
        
        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        # 在后台线程中运行转换
        thread = threading.Thread(target=self._conversion_worker, daemon=True)
        thread.start()
    
    def _conversion_worker(self):
        """转换工作线程"""
        total_files = len(self.file_queue)
        success_count = 0
        fail_count = 0
        
        # 获取压缩配置
        mode = self.mode_var.get()
        compression = None
        if mode == "compress":
            resolution = self.resolution_var.get()
            target_height = int(resolution) if resolution != "0" else None
            compression = CompressionConfig(
                crf=self.crf_var.get(),
                preset=self.preset_var.get(),
                target_height=target_height
            )
        
        for i, file_path in enumerate(self.file_queue):
            if not self.is_converting:
                break
            
            self.current_index = i
            mode_text = "压缩" if mode == "compress" else "转换"
            self._update_status(f"正在{mode_text} ({i+1}/{total_files}): {Path(file_path).name}")
            
            # 更新树状视图状态
            self._update_tree_item_status(i, "处理中")
            
            # 确定输出路径和文件名
            if self.output_path.get():
                output_dir = self.output_path.get()
            else:
                output_dir = str(Path(file_path).parent)
            
            # 根据模式生成不同的输出文件名
            if mode == "compress":
                suffix = f"_compressed_{self.resolution_var.get()}p_crf{self.crf_var.get()}"
            else:
                suffix = "_h264"
            
            output_file = os.path.join(
                output_dir,
                f"{Path(file_path).stem}{suffix}{Path(file_path).suffix}"
            )
            
            # 执行转换
            success = self.converter.convert(
                file_path,
                output_file,
                mode=mode,
                compression=compression,
                progress_callback=lambda progress, speed: self._on_progress(i, total_files, progress, speed),
                log_callback=lambda msg: self._log(msg)
            )
            
            if success:
                success_count += 1
                self._update_tree_item_status(i, "完成")
            else:
                fail_count += 1
                self._update_tree_item_status(i, "失败")
        
        # 转换完成
        self.is_converting = False
        self.root.after(0, self._on_conversion_complete, success_count, fail_count)
    
    def _on_progress(self, file_index: int, total_files: int, progress: float, speed: Optional[float]):
        """进度更新回调（在工作线程中调用）"""
        # 更新当前文件进度
        current_percent = progress * 100
        
        # 更新总体进度
        overall_progress = ((file_index + progress) / total_files) * 100
        
        self.root.after(0, self._update_progress, current_percent, overall_progress, speed)
    
    def _update_progress(self, current_percent: float, overall_progress: float, speed: Optional[float]):
        """更新进度条（在主线程中调用）"""
        self.current_progress_var.set(current_percent)
        self.current_progress_label.config(text=f"{current_percent:.1f}%")
        
        self.progress_var.set(overall_progress)
        self.progress_label.config(text=f"{overall_progress:.1f}%")
        
        # 更新剩余时间
        if speed and speed > 0 and self.start_time:
            elapsed = datetime.now() - self.start_time
            remaining_files = len(self.file_queue) - self.current_index - 1
            
            if remaining_files > 0:
                # 基于当前文件速度估算
                if current_percent > 0:
                    estimated_total_time = elapsed / (self.current_index + current_percent) * len(self.file_queue)
                    remaining_time = estimated_total_time - elapsed
                    self.time_label.config(text=f"剩余: {str(timedelta(seconds=int(remaining_time.total_seconds())))}")
    
    def _update_tree_item_status(self, index: int, status: str):
        """更新树状视图中的状态"""
        items = self.tree.get_children()
        if index < len(items):
            item_id = items[index]
            values = list(self.tree.item(item_id, "values"))
            values[-1] = status
            self.tree.item(item_id, values=values)
    
    def _update_status(self, message: str):
        """更新状态标签"""
        self.root.after(0, lambda: self.status_label.config(text=message))
    
    def _cancel_conversion(self):
        """取消转换"""
        if messagebox.askyesno("确认", "确定要取消转换吗？"):
            self.is_converting = False
            self.converter.cancel()
            self._log("正在取消转换...")
    
    def _open_output_folder(self):
        """打开输出文件夹"""
        import subprocess as sp
        
        # 确定输出目录
        if self.output_path.get():
            output_dir = self.output_path.get()
        elif self.file_queue:
            # 使用第一个文件的源目录
            output_dir = str(Path(self.file_queue[0]).parent)
        else:
            messagebox.showinfo("提示", "请先添加文件或选择输出目录")
            return
        
        # 确保目录存在
        if not os.path.exists(output_dir):
            messagebox.showwarning("警告", f"输出目录不存在: {output_dir}")
            return
        
        # 打开文件夹（Windows）
        sp.Popen(f'explorer "{output_dir}"')
        self._log(f"已打开输出文件夹: {output_dir}")
    
    def _on_conversion_complete(self, success_count: int, fail_count: int):
        """转换完成处理"""
        self.start_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        
        self.progress_var.set(100)
        self.progress_label.config(text="100%")
        self.current_progress_var.set(0)
        self.current_progress_label.config(text="0%")
        
        total_time = datetime.now() - self.start_time if self.start_time else timedelta()
        
        self._log("=" * 50)
        self._log(f"转换完成！成功: {success_count}, 失败: {fail_count}")
        self._log(f"总耗时: {str(timedelta(seconds=int(total_time.total_seconds())))}")
        
        messagebox.showinfo(
            "转换完成",
            f"成功: {success_count}\n失败: {fail_count}\n总耗时: {str(timedelta(seconds=int(total_time.total_seconds())))}"
        )
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    app = ConverterApp()
    app.run()


if __name__ == "__main__":
    main()
