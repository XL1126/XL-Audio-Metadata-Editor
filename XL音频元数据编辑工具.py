import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import tempfile
import shutil
import base64
import mutagen
from mutagen.id3 import ID3, APIC, error, TIT2, TALB, TPE1, TDRC
from mutagen.flac import FLAC
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
import threading
from io import BytesIO


class AudioMetadataEmbedder:
    def __init__(self, root):
        self.root = root
        self.root.title("XL音频元数据编辑工具")
        self.root.geometry("850x620")  # 优化窗口尺寸
        self.root.minsize(800, 580)  # 合理的最小尺寸
        self.root.resizable(True, True)

        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("SimHei", 10))
        self.style.configure("TButton", font=("SimHei", 10))
        self.style.configure("TEntry", font=("SimHei", 10))
        self.style.configure("TProgressbar", thickness=15)
        self.style.configure("TLabelframe", font=("SimHei", 10, "bold"))

        # 变量初始化
        self.audio_path = tk.StringVar()
        self.image_path = tk.StringVar()
        self.save_path = tk.StringVar()

        # 元数据变量
        self.title_var = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.album_var = tk.StringVar()
        self.year_var = tk.StringVar()

        # 图片预览相关
        self.preview_image = None
        # 添加一个标记，用于跟踪用户是否明确删除了图片
        self.image_removed = False

        # 创建主框架并配置网格权重
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.grid_columnconfigure(0, weight=3)  # 左侧区域占3份
        self.main_frame.grid_columnconfigure(1, weight=2)  # 右侧预览区占2份
        self.main_frame.grid_rowconfigure(0, weight=2)  # 上部分占2份
        self.main_frame.grid_rowconfigure(1, weight=1)  # 下部分占1份

        self.create_widgets()

    def create_widgets(self):
        # 左侧区域 - 文件选择和元数据
        left_frame = ttk.LabelFrame(self.main_frame, text="文件与元数据", padding="15")
        left_frame.grid(row=0, column=0, padx=10, pady=5, sticky=tk.NSEW)
        left_frame.grid_columnconfigure(1, weight=1)

        # 音频文件选择
        ttk.Label(left_frame, text="音频文件:").grid(row=0, column=0, sticky=tk.W, pady=6, padx=5)
        ttk.Entry(left_frame, textvariable=self.audio_path).grid(row=0, column=1, pady=6, sticky=tk.EW)
        ttk.Button(left_frame, text="浏览...", command=self.select_audio).grid(row=0, column=2, padx=5, pady=6)

        # 图片文件选择（调整按钮位置）
        ttk.Label(left_frame, text="图片文件:").grid(row=1, column=0, sticky=tk.W, pady=6, padx=5)
        ttk.Entry(left_frame, textvariable=self.image_path).grid(row=1, column=1, pady=6, sticky=tk.EW)
        
        # 将图片选择按钮放置在输入框下方，向左偏移
        image_button_frame = ttk.Frame(left_frame)
        image_button_frame.grid(row=2, column=1, sticky=tk.W, padx=(0, 5), pady=(0, 10))
        ttk.Button(image_button_frame, text="浏览...", command=self.select_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(image_button_frame, text="删除", command=self.clear_image, style="Danger.TButton").pack(side=tk.LEFT, padx=2)

        # 保存路径选择
        ttk.Label(left_frame, text="保存位置:").grid(row=3, column=0, sticky=tk.W, pady=6, padx=5)
        ttk.Entry(left_frame, textvariable=self.save_path).grid(row=3, column=1, pady=6, sticky=tk.EW)
        ttk.Button(left_frame, text="浏览...", command=self.select_save_location).grid(row=3, column=2, padx=5, pady=6)

        # 元数据编辑区域
        ttk.Separator(left_frame, orient='horizontal').grid(row=4, column=0, columnspan=3, pady=12, sticky=tk.EW)
        ttk.Label(left_frame, text="元数据编辑:", font=("SimHei", 10, "bold")).grid(row=5, column=0, columnspan=3,
                                                                                    sticky=tk.W, pady=8)

        # 标题
        ttk.Label(left_frame, text="标题:").grid(row=6, column=0, sticky=tk.W, pady=6, padx=5)
        title_entry = ttk.Entry(left_frame, textvariable=self.title_var)
        title_entry.grid(row=6, column=1, columnspan=2, pady=6, sticky=tk.EW, padx=(0, 5))
        self.setup_entry_paste(title_entry)

        # 艺术家/作者
        ttk.Label(left_frame, text="艺术家:").grid(row=7, column=0, sticky=tk.W, pady=6, padx=5)
        artist_entry = ttk.Entry(left_frame, textvariable=self.artist_var)
        artist_entry.grid(row=7, column=1, columnspan=2, pady=6, sticky=tk.EW, padx=(0, 5))
        self.setup_entry_paste(artist_entry)

        # 专辑
        ttk.Label(left_frame, text="专辑:").grid(row=8, column=0, sticky=tk.W, pady=6, padx=5)
        album_entry = ttk.Entry(left_frame, textvariable=self.album_var)
        album_entry.grid(row=8, column=1, columnspan=2, pady=6, sticky=tk.EW, padx=(0, 5))
        self.setup_entry_paste(album_entry)

        # 年份
        ttk.Label(left_frame, text="年份:").grid(row=9, column=0, sticky=tk.W, pady=6, padx=5)
        year_entry = ttk.Entry(left_frame, textvariable=self.year_var)
        year_entry.grid(row=9, column=1, columnspan=2, pady=6, sticky=tk.EW, padx=(0, 5))
        self.setup_entry_paste(year_entry)

        # 嵌入按钮（美化样式）
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=10, column=0, columnspan=3, pady=15)
        embed_btn = ttk.Button(button_frame, text="开始嵌入", command=self.start_embedding, width=25)
        embed_btn.pack(pady=10)
        embed_btn.configure(style="Accent.TButton")

        # 右侧区域 - 图片预览（美化边框和阴影）
        right_frame = ttk.LabelFrame(self.main_frame, text="图片预览", padding="15")
        right_frame.grid(row=0, column=1, padx=10, pady=5, sticky=tk.NSEW)

        # 图片预览容器（美化样式）
        self.preview_container = ttk.Frame(
            right_frame,
            width=300,
            height=300,
            relief=tk.SUNKEN,
            borderwidth=1
        )
        self.preview_container.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.preview_container.grid_propagate(False)

        # 添加轻微的背景色，使空白区域更明显
        self.preview_container.configure(style="Preview.TFrame")

        # 图片预览标签（居中显示）
        self.preview_label = ttk.Label(self.preview_container)
        self.preview_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # 图片信息标签
        self.image_info_label = ttk.Label(right_frame, text="未选择图片", justify=tk.CENTER)
        self.image_info_label.pack(pady=10, fill=tk.X)

        # 底部区域 - 进度和日志（优化高度和间距）
        bottom_frame = ttk.LabelFrame(self.main_frame, text="操作信息", padding="15")
        bottom_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky=tk.NSEW)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(bottom_frame, variable=self.progress_var, mode="determinate")
        self.progress_bar.pack(pady=5, fill=tk.X)

        # 状态标签
        self.status_label = ttk.Label(bottom_frame, text="请选择音频文件开始操作", anchor=tk.W)
        self.status_label.pack(pady=5, fill=tk.X)

        # 日志标题
        ttk.Label(bottom_frame, text="操作日志:", anchor=tk.W).pack(fill=tk.X)

        # 日志文本框和滚动条
        log_frame = ttk.Frame(bottom_frame)
        log_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_frame,
            height=5,
            state=tk.DISABLED,
            font=("SimHei", 9),
            wrap=tk.WORD,
            relief=tk.SUNKEN,
            borderwidth=1
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # 自定义样式
        self.style.configure("Accent.TButton", font=("SimHei", 10, "bold"))
        self.style.configure("Danger.TButton", font=("SimHei", 10), foreground="#d9534f")
        self.style.configure("Preview.TFrame", background="#f8f9fa")

    def setup_entry_paste(self, entry):
        """设置输入框的粘贴事件处理，防止UI阻塞"""

        def paste(event):
            try:
                # 获取剪贴板内容
                text = self.root.clipboard_get()
                # 在当前光标位置插入文本
                entry.insert(tk.INSERT, text)
                return "break"  # 阻止默认粘贴行为，避免重复粘贴
            except tk.TclError:
                # 剪贴板为空时的处理
                return "break"

        # 绑定粘贴事件，使用自定义处理函数
        entry.bind('<Control-v>', paste)
        entry.bind('<Button-2>', paste)  # 鼠标中键粘贴

    def update_preview(self, image=None):
        """更新图片预览，无图片时显示空"""
        if image:
            # 调整图片大小以适应预览区域
            img = image.copy()
            max_size = (min(self.preview_container.winfo_width(), 300),
                        min(self.preview_container.winfo_height(), 300))
            img.thumbnail(max_size)
            self.preview_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.preview_image)
        else:
            # 无图片时清空预览
            self.preview_image = None
            self.preview_label.config(image="")

    def log(self, message):
        """添加日志信息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def select_audio(self):
        file_types = [
            ("音频文件", "*.mp3 *.flac *.m4a *.ogg"),
            ("所有文件", "*.*")
        ]
        filename = filedialog.askopenfilename(title="选择音频文件", filetypes=file_types)
        if filename:
            self.audio_path.set(filename)
            self.log(f"已选择音频文件: {os.path.basename(filename)}")

            # 在新线程中读取元数据，避免UI阻塞
            threading.Thread(target=self.read_metadata, args=(filename,), daemon=True).start()

            # 自动设置默认保存路径
            if not self.save_path.get():
                dir_name, file_name = os.path.split(filename)
                name, ext = os.path.splitext(file_name)
                self.save_path.set(dir_name.replace('\\', '/') + '/' + f"{name}_带封面{ext}")

    def select_image(self):
        file_types = [
            ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif"),
            ("所有文件", "*.*")
        ]
        filename = filedialog.askopenfilename(title="选择图片文件", filetypes=file_types)
        if filename:
            self.image_path.set(filename)
            self.image_removed = False  # 重新选择图片时重置删除标记
            self.log(f"已选择图片文件: {os.path.basename(filename)}")

            # 更新图片预览
            try:
                with Image.open(filename) as img:
                    self.update_preview(img)
                    # 显示图片信息
                    img_info = f"图片: {os.path.basename(filename)} ({img.size[0]}x{img.size[1]})"
                    self.image_info_label.config(text=img_info)
            except Exception as e:
                self.log(f"图片预览错误: {str(e)}")
                messagebox.showerror("错误", f"无法预览图片: {str(e)}")

            # 检查是否可以开始嵌入
            if self.audio_path.get() and self.save_path.get():
                self.status_label.config(text="可以开始嵌入操作")
        else:
            # 如果取消选择，清空预览
            self.clear_image()

    def clear_image(self):
        """删除已选择的图片"""
        if self.image_path.get():
            current_image = self.image_path.get()
            self.image_path.set("")
            self.image_removed = True  # 标记图片已被用户删除
            self.update_preview()
            self.image_info_label.config(text="未选择图片")
            self.log(f"已删除图片: {os.path.basename(current_image)}")
        else:
            # 如果没有选择图片，也更新状态确保一致
            self.update_preview()
            self.image_info_label.config(text="未选择图片")
            self.image_removed = True  # 即使之前没有图片，现在也标记为已删除状态

    def select_save_location(self):
        if self.audio_path.get():
            default_ext = os.path.splitext(self.audio_path.get())[1]
            default_filename = os.path.basename(self.audio_path.get())
            name, ext = os.path.splitext(default_filename)
            default_filename = f"{name}_带封面{ext}"
        else:
            default_ext = ".mp3"
            default_filename = f"output{default_ext}"

        file_types = [
            ("音频文件", f"*{default_ext}"),
            ("所有文件", "*.*")
        ]

        filename = filedialog.asksaveasfilename(
            title="选择保存位置",
            defaultextension=default_ext,
            initialfile=default_filename,
            filetypes=file_types
        )
        if filename:
            self.save_path.set(filename)
            self.log(f"保存位置: {filename}")

    def update_status(self, message):
        # 使用try-except块处理可能的UI状态检查错误
        try:
            # 确保在主线程中更新UI
            self.root.after(0, lambda: self.status_label.config(text=message))
            self.root.update_idletasks()
        except Exception:
            pass  # 忽略已关闭窗口的更新尝试

    def update_progress(self, value):
        # 使用try-except块处理可能的UI状态检查错误
        try:
            # 确保在主线程中更新UI
            self.root.after(0, lambda: self.progress_var.set(value))
            self.root.update_idletasks()
        except Exception:
            pass  # 忽略已关闭窗口的更新尝试

    def read_metadata(self, audio_path):
        """读取音频文件的元数据并显示在编辑框中"""
        self.update_status("正在读取元数据...")
        self.log(f"正在读取元数据...")
        file_ext = os.path.splitext(audio_path)[1].lower()

        # 清空现有元数据（在主线程中执行）
        self.root.after(0, lambda: self.title_var.set(""))
        self.root.after(0, lambda: self.artist_var.set(""))
        self.root.after(0, lambda: self.album_var.set(""))
        self.root.after(0, lambda: self.year_var.set(""))

        # 默认不显示任何图片
        self.root.after(0, lambda: self.update_preview())
        self.root.after(0, lambda: self.image_info_label.config(text="未选择图片"))

        try:
            if file_ext == '.mp3':
                # 读取MP3元数据
                audio = ID3(audio_path)
                title = audio.get('TIT2', [''])[0] if 'TIT2' in audio else ""
                artist = audio.get('TPE1', [''])[0] if 'TPE1' in audio else ""
                album = audio.get('TALB', [''])[0] if 'TALB' in audio else ""
                year = audio.get('TDRC', [''])[0] if 'TDRC' in audio else ""

                # 在主线程中更新UI
                self.root.after(0, lambda: self.title_var.set(title))
                self.root.after(0, lambda: self.artist_var.set(artist))
                self.root.after(0, lambda: self.album_var.set(album))
                self.root.after(0, lambda: self.year_var.set(str(year)))

                # 检查是否有封面图片
                cover_data = None
                for tag in audio.keys():
                    if tag.startswith('APIC'):
                        self.log("检测到现有封面图片")
                        cover_data = audio[tag].data
                        break

            elif file_ext == '.flac':
                # 读取FLAC元数据
                audio = FLAC(audio_path)
                title = audio.get('title', [''])[0] if 'title' in audio else ""
                artist = audio.get('artist', [''])[0] if 'artist' in audio else ""
                album = audio.get('album', [''])[0] if 'album' in audio else ""
                year = audio.get('date', [''])[0] if 'date' in audio else ""

                # 在主线程中更新UI
                self.root.after(0, lambda: self.title_var.set(title))
                self.root.after(0, lambda: self.artist_var.set(artist))
                self.root.after(0, lambda: self.album_var.set(album))
                self.root.after(0, lambda: self.year_var.set(year))

                # 检查是否有封面图片
                cover_data = audio.pictures[0].data if audio.pictures else None
                if cover_data:
                    self.log("检测到现有封面图片")

            elif file_ext in ['.m4a', '.mp4']:
                # 读取MP4/M4A元数据
                audio = MP4(audio_path)
                title = audio.get('\xa9nam', [''])[0] if '\xa9nam' in audio else ""
                artist = audio.get('\xa9ART', [''])[0] if '\xa9ART' in audio else ""
                album = audio.get('\xa9alb', [''])[0] if '\xa9alb' in audio else ""
                year = audio.get('\xa9day', [''])[0] if '\xa9day' in audio else ""

                # 在主线程中更新UI
                self.root.after(0, lambda: self.title_var.set(title))
                self.root.after(0, lambda: self.artist_var.set(artist))
                self.root.after(0, lambda: self.album_var.set(album))
                self.root.after(0, lambda: self.year_var.set(year))

                # 检查是否有封面图片
                cover_data = audio['covr'][0] if 'covr' in audio and audio['covr'] else None
                if cover_data:
                    self.log("检测到现有封面图片")

            elif file_ext == '.ogg':
                # 读取OGG元数据
                audio = OggVorbis(audio_path)
                title = audio.get('title', [''])[0] if 'title' in audio else ""
                artist = audio.get('artist', [''])[0] if 'artist' in audio else ""
                album = audio.get('album', [''])[0] if 'album' in audio else ""
                year = audio.get('date', [''])[0] if 'date' in audio else ""

                # 在主线程中更新UI
                self.root.after(0, lambda: self.title_var.set(title))
                self.root.after(0, lambda: self.artist_var.set(artist))
                self.root.after(0, lambda: self.album_var.set(album))
                self.root.after(0, lambda: self.year_var.set(year))

                # OGG封面处理较复杂，这里简化处理
                cover_data = None

            # 如果有封面数据，显示封面
            if cover_data:
                try:
                    img = Image.open(BytesIO(cover_data))
                    self.root.after(0, lambda: self.update_preview(img))
                    self.root.after(0, lambda: self.image_info_label.config(
                        text=f"现有封面图片 ({img.size[0]}x{img.size[1]})"))
                except Exception as e:
                    self.log(f"显示现有封面失败: {str(e)}")

            self.log("元数据读取完成")
            self.update_status("元数据读取完成，可以编辑")

        except Exception as e:
            self.log(f"读取元数据时出错: {str(e)}")
            self.update_status("读取元数据时出错")
            self.root.after(0, lambda: messagebox.showwarning(
                "警告", f"读取元数据时出错: {str(e)}\n将使用默认值"))

    def process_image(self, image_path):
        """处理图片，转换为合适的格式和大小"""
        self.update_status("正在处理图片...")
        self.log("开始处理图片...")
        self.update_progress(20)

        try:
            with Image.open(image_path) as img:
                self.log(f"原始图片格式: {img.format}, 大小: {img.size}, 模式: {img.mode}")

                # 确保图片是RGB模式
                if img.mode in ('RGBA', 'LA'):
                    self.log(f"图片包含Alpha通道，正在转换为RGB模式...")
                    background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
                    background.paste(img, img.split()[-1])
                    img = background
                elif img.mode == 'P':
                    self.log("图片是调色板模式，正在转换为RGB模式...")
                    img = img.convert('RGB')

                # 调整图片大小，最大800x800以确保足够的清晰度
                max_size = (800, 800)
                img.thumbnail(max_size)
                self.log(f"处理后图片大小: {img.size}")

                # 保存为临时文件
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                img.save(temp_file, 'JPEG', quality=95)
                temp_file.close()

                # 检查临时文件大小
                img_size = os.path.getsize(temp_file.name)
                self.log(f"处理后的图片大小: {img_size / 1024:.2f} KB")

                return temp_file.name
        except Exception as e:
            error_msg = f"图片处理错误: {str(e)}"
            self.update_status(error_msg)
            self.log(error_msg)
            return None

    def embed_cover(self):
        """执行嵌入操作"""
        audio_path = self.audio_path.get()
        image_path = self.image_path.get()
        save_path = self.save_path.get()

        # 获取元数据
        title = self.title_var.get().strip()
        artist = self.artist_var.get().strip()
        album = self.album_var.get().strip()
        year = self.year_var.get().strip()

        # 验证输入
        if not audio_path or not os.path.exists(audio_path):
            self.update_status("请选择有效的音频文件")
            return

        if not save_path:
            self.update_status("请选择保存位置")
            return

        try:
            # 记录原始文件大小
            original_size = os.path.getsize(audio_path)
            self.log(f"原始音频文件大小: {original_size / 1024:.2f} KB")

            # 复制原始文件到保存路径
            self.update_status("正在准备文件...")
            self.log("复制原始文件到目标位置...")
            self.update_progress(10)

            shutil.copy2(audio_path, save_path)

            # 处理图片（如果提供了新图片）
            processed_img_path = None
            if image_path and os.path.exists(image_path):
                processed_img_path = self.process_image(image_path)
                if not processed_img_path:
                    return
            else:
                self.log("未提供新图片，将根据用户操作决定是否保留原有封面")
                self.update_progress(30)

            self.update_status("正在嵌入图片和元数据...")
            self.log("开始嵌入图片和元数据到音频文件...")
            self.update_progress(50)

            # 根据文件类型选择不同的嵌入方法
            file_ext = os.path.splitext(save_path)[1].lower()
            self.log(f"音频格式: {file_ext}")

            if file_ext == '.mp3':
                self.embed_mp3(save_path, processed_img_path, title, artist, album, year)
            elif file_ext == '.flac':
                self.embed_flac(save_path, processed_img_path, title, artist, album, year)
            elif file_ext in ['.m4a', '.mp4']:
                self.embed_mp4(save_path, processed_img_path, title, artist, album, year)
            elif file_ext == '.ogg':
                self.embed_ogg(save_path, processed_img_path, title, artist, album, year)
            else:
                self.update_status(f"不支持的文件格式: {file_ext}")
                self.log(f"错误: 不支持的文件格式: {file_ext}")
                return

            # 清理临时文件
            if processed_img_path and os.path.exists(processed_img_path):
                os.remove(processed_img_path)
                self.log("清理临时文件完成")

            # 检查最终文件大小
            final_size = os.path.getsize(save_path)
            size_diff = final_size - original_size
            self.log(f"处理后文件大小: {final_size / 1024:.2f} KB")
            self.log(f"增加的大小: {size_diff / 1024:.2f} KB")

            self.update_progress(100)
            self.update_status("图片和元数据嵌入成功！")
            self.log("图片和元数据嵌入成功！")
            self.root.after(0, lambda: messagebox.showinfo(
                "成功",
                f"图片和元数据已成功嵌入到音频文件\n"
                f"保存位置: {save_path}\n"
                f"文件大小增加: {size_diff / 1024:.2f} KB"
            ))

        except Exception as e:
            error_msg = f"操作失败: {str(e)}"
            self.update_status(error_msg)
            self.log(error_msg)
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

    # 以下是各种音频格式的嵌入方法
    def embed_mp3(self, audio_path, image_path, title, artist, album, year):
        try:
            try:
                audio = ID3(audio_path, v2_version=3)
            except error:
                self.log("未发现ID3标签，创建新标签...")
                audio = ID3()

            # 处理图片嵌入或删除
            if image_path:
                # 用户选择了新图片，嵌入新图片
                with open(image_path, 'rb') as img_file:
                    img_data = img_file.read()

                self.log(f"准备嵌入图片数据，大小: {len(img_data) / 1024:.2f} KB")

                # 删除现有封面
                for tag in list(audio.keys()):
                    if tag.startswith('APIC'):
                        del audio[tag]
                        self.log("已移除现有封面图片")

                # 添加新封面
                audio.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Front Cover',
                    data=img_data
                ))
            elif self.image_removed:
                # 用户明确删除了图片，移除所有封面
                removed_count = 0
                for tag in list(audio.keys()):
                    if tag.startswith('APIC'):
                        del audio[tag]
                        removed_count += 1
                if removed_count > 0:
                    self.log(f"已移除 {removed_count} 个封面图片")
                else:
                    self.log("未找到需要移除的封面图片")

            if title:
                if 'TIT2' in audio:
                    del audio['TIT2']
                audio.add(TIT2(encoding=3, text=[title]))
                self.log(f"更新标题: {title}")

            if artist:
                if 'TPE1' in audio:
                    del audio['TPE1']
                audio.add(TPE1(encoding=3, text=[artist]))
                self.log(f"更新艺术家: {artist}")

            if album:
                if 'TALB' in audio:
                    del audio['TALB']
                audio.add(TALB(encoding=3, text=[album]))
                self.log(f"更新专辑: {album}")

            if year:
                if 'TDRC' in audio:
                    del audio['TDRC']
                audio.add(TDRC(encoding=3, text=[year]))
                self.log(f"更新年份: {year}")

            audio.save(audio_path, v2_version=3)
            self.log("MP3封面和元数据嵌入完成")

        except Exception as e:
            raise Exception(f"MP3嵌入错误: {str(e)}")

    def embed_flac(self, audio_path, image_path, title, artist, album, year):
        try:
            audio = FLAC(audio_path)

            # 处理图片嵌入或删除
            if image_path:
                # 用户选择了新图片，嵌入新图片
                with open(image_path, 'rb') as img_file:
                    img_data = img_file.read()

                self.log(f"准备嵌入图片数据，大小: {len(img_data) / 1024:.2f} KB")

                # 清除现有图片
                if len(audio.pictures) > 0:
                    audio.clear_pictures()
                    self.log(f"已移除 {len(audio.pictures)} 个现有图片")

                # 添加新图片
                picture = FLAC.Picture()
                picture.data = img_data
                picture.type = 3
                picture.mime = 'image/jpeg'
                picture.desc = 'Front Cover'
                audio.add_picture(picture)
            elif self.image_removed:
                # 用户明确删除了图片，移除所有图片
                if len(audio.pictures) > 0:
                    count = len(audio.pictures)
                    audio.clear_pictures()
                    self.log(f"已移除 {count} 个图片")
                else:
                    self.log("未找到需要移除的图片")

            if title:
                audio['title'] = title
                self.log(f"更新标题: {title}")
            elif 'title' in audio:
                del audio['title']

            if artist:
                audio['artist'] = artist
                self.log(f"更新艺术家: {artist}")
            elif 'artist' in audio:
                del audio['artist']

            if album:
                audio['album'] = album
                self.log(f"更新专辑: {album}")
            elif 'album' in audio:
                del audio['album']

            if year:
                audio['date'] = year
                self.log(f"更新年份: {year}")
            elif 'date' in audio:
                del audio['date']

            audio.save()
            self.log("FLAC封面和元数据嵌入完成")

        except Exception as e:
            raise Exception(f"FLAC嵌入错误: {str(e)}")

    def embed_mp4(self, audio_path, image_path, title, artist, album, year):
        try:
            audio = MP4(audio_path)

            # 处理图片嵌入或删除
            if image_path:
                # 用户选择了新图片，嵌入新图片
                with open(image_path, 'rb') as img_file:
                    img_data = img_file.read()

                self.log(f"准备嵌入图片数据，大小: {len(img_data) / 1024:.2f} KB")
                audio['covr'] = [MP4Cover(img_data, imageformat=MP4Cover.FORMAT_JPEG)]
            elif self.image_removed:
                # 用户明确删除了图片，移除所有封面
                if 'covr' in audio:
                    del audio['covr']
                    self.log("已移除封面图片")
                else:
                    self.log("未找到需要移除的封面图片")

            if title:
                audio['\xa9nam'] = title
                self.log(f"更新标题: {title}")
            elif '\xa9nam' in audio:
                del audio['\xa9nam']

            if artist:
                audio['\xa9ART'] = artist
                self.log(f"更新艺术家: {artist}")
            elif '\xa9ART' in audio:
                del audio['\xa9ART']

            if album:
                audio['\xa9alb'] = album
                self.log(f"更新专辑: {album}")
            elif '\xa9alb' in audio:
                del audio['\xa9alb']

            if year:
                audio['\xa9day'] = year
                self.log(f"更新年份: {year}")
            elif '\xa9day' in audio:
                del audio['\xa9day']

            audio.save()
            self.log("MP4/M4A封面和元数据嵌入完成")

        except Exception as e:
            raise Exception(f"MP4/M4A嵌入错误: {str(e)}")

    def embed_ogg(self, audio_path, image_path, title, artist, album, year):
        try:
            audio = OggVorbis(audio_path)

            # 处理图片嵌入或删除
            if image_path:
                # 用户选择了新图片，嵌入新图片
                with open(image_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img_b64 = base64.b64encode(img_data).decode('utf-8')

                self.log(f"准备嵌入图片数据，原始大小: {len(img_data) / 1024:.2f} KB")
                picture_meta = f"3:image/jpeg;Front Cover;{img_b64}"
                audio['metadata_block_picture'] = [picture_meta]
            elif self.image_removed:
                # 用户明确删除了图片，移除所有封面
                if 'metadata_block_picture' in audio:
                    del audio['metadata_block_picture']
                    self.log("已移除封面图片")
                else:
                    self.log("未找到需要移除的封面图片")

            if title:
                audio['title'] = title
                self.log(f"更新标题: {title}")
            elif 'title' in audio:
                del audio['title']

            if artist:
                audio['artist'] = artist
                self.log(f"更新艺术家: {artist}")
            elif 'artist' in audio:
                del audio['artist']

            if album:
                audio['album'] = album
                self.log(f"更新专辑: {album}")
            elif 'album' in audio:
                del audio['album']

            if year:
                audio['date'] = year
                self.log(f"更新年份: {year}")
            elif 'date' in audio:
                del audio['date']

            audio.save()
            self.log("OGG封面和元数据嵌入完成")

        except Exception as e:
            raise Exception(f"OGG嵌入错误: {str(e)}")

    def start_embedding(self):
        """在新线程中开始嵌入操作，避免界面卡顿"""
        self.update_progress(0)
        self.log("开始嵌入操作...")
        threading.Thread(target=self.embed_cover, daemon=True).start()


if __name__ == "__main__":
    print("XL音频元数据编辑工具开始运行")
    print("作者: XL(小狸)")
    root = tk.Tk()
    root.option_add("*Font", "SimHei 10")
    app = AudioMetadataEmbedder(root)
    root.mainloop()