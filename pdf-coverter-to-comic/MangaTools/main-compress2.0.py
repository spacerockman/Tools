import customtkinter as ctk
from tkinter import filedialog
import os
import sys
import subprocess
import threading
import zipfile
import io
import shutil
import time
import stat
import tempfile
import re
import multiprocessing
import numpy as np
from PIL import Image, ImageOps
from concurrent.futures import ProcessPoolExecutor, as_completed

# ================= 🎨 现代化主题配置 =================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

FONT_TITLE = ("Roboto Medium", 24)
FONT_NORMAL = ("Roboto", 14)
FONT_MONO = ("Consolas", 12)

# --- 📉 极限压缩参数 (400MB -> 40MB 的关键) ---
TARGET_WIDTH = 1264
# 强制降为 4 色 (黑, 深灰, 浅灰, 白) -> 极大减小体积
QUANTIZE_COLORS = 4 
# 质量降至 35 (配合纯净背景，Kindle上依然清晰)
JPEG_QUALITY = 35 
DEVICE_PROFILE = 'KO'

# ================= 独立的处理函数 (极限压缩算法) =================
def cpu_worker_task(args):
    """
    CPU 任务：缩放 -> 强力清洗 -> 4色量化 -> 极限压缩
    """
    img_path, original_filename = args
    try:
        # 读取重试
        img = None
        for _ in range(5):
            try:
                img = Image.open(img_path)
                img.load()
                break
            except:
                time.sleep(0.1)
        
        if img is None: return None

        # 1. 转灰度
        if img.mode != 'L': img = img.convert('L')

        # 2. 智能缩放 (LANCZOS)
        w, h = img.size
        if w > TARGET_WIDTH:
            ratio = TARGET_WIDTH / w
            new_h = int(h * ratio)
            img = img.resize((TARGET_WIDTH, new_h), Image.Resampling.LANCZOS)
        
        # --- 3. 强力背景清洗 (核心体积优化) ---
        # 将图片转为 numpy 数组进行矩阵运算
        arr = np.array(img)
        
        # 策略：
        # 1. 亮部清洗：大于 230 的全部变成 255 (纯白) -> 消除纸张底噪
        # 2. 暗部压实：小于 50 的全部变成 0 (纯黑) -> 让文字更黑
        # 3. 中间调拉伸：增加对比度
        
        # 使用 np.where 进行快速替换
        # 逻辑：如果 > 230 设为 255，否则保持原样
        arr = np.where(arr > 230, 255, arr)
        # 逻辑：如果 < 50 设为 0，否则保持原样
        arr = np.where(arr < 50, 0, arr)
        
        # 转回 PIL 图片
        img = Image.fromarray(arr)

        # --- 4. 4色阶量化 (Palette Reduction) ---
        # 这一步把复杂的灰度图变成只有 4 种颜色的“版画”风格
        # 极大利于 JPEG 霍夫曼编码
        img_rgb = img.convert("RGB")
        # method=2 (FastOctree) 速度快且效果好
        img_quant = img_rgb.quantize(colors=QUANTIZE_COLORS, method=2)
        img = img_quant.convert('L')
        
        # 5. 导出 (Quality 35 + Optimize)
        out = io.BytesIO()
        # subsampling=0 保证线条边缘不发虚
        img.save(out, format='JPEG', quality=JPEG_QUALITY, optimize=True, subsampling=0)
        
        return (original_filename, out.getvalue())
    except Exception:
        return None

# ================= 主程序类 (保持多进程架构) =================
class ModernMangaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Manga Ultimate Converter | Extreme Compression")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="Manga\nConverter", font=FONT_TITLE)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.lbl_ver = ctk.CTkLabel(self.sidebar, text="v5.1 Extreme", text_color="gray", font=("Roboto", 12))
        self.lbl_ver.grid(row=1, column=0, padx=20, pady=(0, 20))

        self.info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.info_frame.grid(row=2, column=0, padx=10, sticky="ew")
        ctk.CTkLabel(self.info_frame, text="⚡ GPU AI 重绘", font=("Roboto", 12)).pack(anchor="w")
        ctk.CTkLabel(self.info_frame, text="📉 4色阶极限压缩", font=("Roboto", 12)).pack(anchor="w")
        ctk.CTkLabel(self.info_frame, text="🧹 智能背景清洗", font=("Roboto", 12)).pack(anchor="w")

        # --- Main Area ---
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_rowconfigure(3, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        # Paths
        self.card_paths = ctk.CTkFrame(self.main_area, corner_radius=10)
        self.card_paths.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.card_paths.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.card_paths, text="📂 输入目录", font=FONT_NORMAL).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        self.entry_input = ctk.CTkEntry(self.card_paths, placeholder_text="选择包含 PDF 的文件夹", height=35)
        self.entry_input.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        ctk.CTkButton(self.card_paths, text="浏览", width=80, height=35, command=self.select_input).grid(row=0, column=2, padx=15, pady=15)

        ctk.CTkLabel(self.card_paths, text="💾 输出目录", font=FONT_NORMAL).grid(row=1, column=0, padx=15, pady=(0,15), sticky="w")
        self.entry_output = ctk.CTkEntry(self.card_paths, placeholder_text="选择保存位置", height=35)
        self.entry_output.grid(row=1, column=1, padx=10, pady=(0,15), sticky="ew")
        ctk.CTkButton(self.card_paths, text="浏览", width=80, height=35, command=self.select_output).grid(row=1, column=2, padx=15, pady=(0,15))

        # Controls
        self.card_ctrl = ctk.CTkFrame(self.main_area, corner_radius=10, fg_color="transparent")
        self.card_ctrl.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.card_ctrl.grid_columnconfigure(0, weight=1)

        self.btn_start = ctk.CTkButton(self.card_ctrl, text="🚀 启动极限压缩引擎", height=50, font=("Roboto", 16, "bold"), 
                                       fg_color="#b33f00", hover_color="#8a3100", command=self.start_process)
        self.btn_start.grid(row=0, column=0, sticky="ew")

        self.lbl_progress = ctk.CTkLabel(self.card_ctrl, text="准备就绪", font=("Roboto", 12), text_color="gray")
        self.lbl_progress.grid(row=1, column=0, sticky="w", pady=(5, 0))

        self.progress_bar = ctk.CTkProgressBar(self.card_ctrl, height=15)
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        self.progress_bar.set(0)

        # Log
        self.lbl_log = ctk.CTkLabel(self.main_area, text=">_ 系统日志", font=("Roboto", 12, "bold"), anchor="w")
        self.lbl_log.grid(row=3, column=0, sticky="w", pady=(10, 5))

        self.textbox_log = ctk.CTkTextbox(self.main_area, font=FONT_MONO, activate_scrollbars=True)
        self.textbox_log.grid(row=4, column=0, sticky="nsew")
        self.textbox_log.configure(state="disabled", fg_color="#1a1a1a", text_color="#00ff00")

        self.init_tools_paths()

    # ================= Helpers =================

    def log(self, message, end="\n"):
        def _write():
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert("end", message + end)
            self.textbox_log.see("end")
            self.textbox_log.configure(state="disabled")
        self.after(0, _write)

    def update_progress(self, val, text=None):
        self.progress_bar.set(val)
        if text:
            self.lbl_progress.configure(text=text)

    def select_input(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_input.delete(0, "end")
            self.entry_input.insert(0, path)

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_output.delete(0, "end")
            self.entry_output.insert(0, path)

    def init_tools_paths(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        tools_root = os.path.join(base_path, "tools")
        path_7z_dir = os.path.join(tools_root, "7z")
        os.environ["PATH"] += os.pathsep + path_7z_dir
        
        self.kcc_exe = os.path.join(tools_root, "kindleComicConverter", "kcc_c2e_9.2.2.exe")
        self.ai_exe = os.path.join(tools_root, "realesrgan-ncnn-vulkan-v0.2.0-windows", "realesrgan-ncnn-vulkan.exe")
        
        missing = []
        if not os.path.exists(self.kcc_exe): missing.append("KCC")
        if not os.path.exists(self.ai_exe): missing.append("Real-ESRGAN")
        if not os.path.exists(os.path.join(path_7z_dir, "7z.exe")): missing.append("7z")

        if missing:
            self.log("❌ [System] 工具缺失: " + ", ".join(missing))
            self.btn_start.configure(state="disabled")
        else:
            self.log("✅ [System] 核心引擎已就绪。")

    # ================= Core Logic =================

    def start_process(self):
        input_dir = self.entry_input.get().strip()
        output_dir = self.entry_output.get().strip()

        if not input_dir or not os.path.exists(input_dir):
            self.log("⚠️ 请选择输入目录")
            return
        if not output_dir:
            self.log("⚠️ 请选择输出目录")
            return

        self.btn_start.configure(state="disabled", text="🔥 极限压缩中...", fg_color="gray")
        self.update_progress(0, "初始化...")
        threading.Thread(target=self.worker_thread, args=(input_dir, output_dir), daemon=True).start()

    def worker_thread(self, input_dir, output_dir):
        files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
        if not files:
            self.log("❌ 没有 PDF 文件")
            self.reset_ui()
            return

        self.log(f"🚀 [Task] 队列: {len(files)} 个文件")
        temp_work_dir = os.path.join(tempfile.gettempdir(), "MangaConvert_Work")
        
        total_start = time.time()

        for idx, file in enumerate(files):
            file_start = time.time()
            base_progress = idx / len(files)
            self.update_progress(base_progress, f"处理: {file}")
            
            self.log(f"\n{'='*40}")
            self.log(f"📄 [{idx+1}/{len(files)}] {file}")
            self.log(f"{'='*40}")
            
            input_path = os.path.join(input_dir, file)
            output_epub = os.path.join(output_dir, os.path.splitext(file)[0] + ".epub")
            
            # 1. KCC
            self.log(">>> Step 1: KCC 转换...")
            if not self.run_command_realtime([
                self.kcc_exe, input_path,
                '-m', '-s', '-g', '1.0',
                '--format=EPUB', '-p', DEVICE_PROFILE,
                '--output', output_epub 
            ]):
                self.log("❌ KCC 失败")
                continue

            # 2. Pipeline Optimization
            self.log(">>> Step 2: GPU/CPU 并发流水线 (极限压缩)...")
            res = self.pipeline_optimize(output_epub, temp_work_dir, base_progress, len(files))
            
            if res:
                size_mb = os.path.getsize(output_epub) / 1024 / 1024
                self.log(f"✅ [Done] 最终体积: {size_mb:.2f} MB")
            
            self.log(f"⏱️ 耗时: {time.time() - file_start:.1f} 秒")

        self.update_progress(1.0, "全部完成")
        self.log(f"\n🎉 总耗时: {time.time() - total_start:.1f} 秒")
        self.safe_rmtree(temp_work_dir)
        self.reset_ui()

    def reset_ui(self):
        self.after(0, lambda: self.btn_start.configure(state="normal", text="🚀 启动极限压缩引擎", fg_color="#b33f00"))

    def run_command_realtime(self, cmd):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding='utf-8', errors='replace', startupinfo=startupinfo, bufsize=1)
            for line in process.stdout:
                if line.strip(): self.log(f"   [KCC] {line.strip()}")
            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.log(f"❌ Error: {e}")
            return False

    # ================= 核心：流水线并发逻辑 =================

    def pipeline_optimize(self, epub_path, work_dir, base_progress, total_files):
        self.safe_rmtree(work_dir)
        time.sleep(0.2)
        
        temp_in = os.path.join(work_dir, "in")
        temp_out = os.path.join(work_dir, "out")
        
        try:
            os.makedirs(temp_in, exist_ok=True)
            os.makedirs(temp_out, exist_ok=True)
        except:
            self.log("❌ 无法创建临时目录")
            return False

        temp_epub_file = epub_path + ".temp"
        file_map = {}
        non_image_files = {}

        # 1. 解压
        try:
            with zipfile.ZipFile(epub_path, 'r') as zin:
                file_list = zin.infolist()
                img_cnt = 0
                for item in file_list:
                    content = zin.read(item.filename)
                    if item.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                        ext = os.path.splitext(item.filename)[1]
                        simple_name = f"img_{img_cnt:05d}{ext}"
                        with open(os.path.join(temp_in, simple_name), "wb") as f: f.write(content)
                        file_map[item.filename] = simple_name
                        img_cnt += 1
                    else:
                        non_image_files[item.filename] = content
            
            if img_cnt == 0: return False
            self.log(f"   -> 待处理图片: {img_cnt} 张")

            # 2. 启动 GPU 进程 (非阻塞)
            ai_cmd = [
                self.ai_exe, '-i', temp_in, '-o', temp_out,
                '-n', 'realesrgan-x4plus-anime', '-s', '4', '-f', 'jpg',
                '-g', '0', '-j', '2:2:2', '-t', '100'
            ]
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            self.log("   -> 启动 GPU 引擎 (后台运行)...")
            ai_process = subprocess.Popen(
                ai_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                startupinfo=startupinfo
            )

            # 3. 启动 CPU 消费者进程池
            processed_data = {}
            processed_files = set()
            
            cpu_executor = ProcessPoolExecutor(max_workers=os.cpu_count())
            futures = []

            self.log("   -> 启动 CPU 多进程流水线...")
            
            last_log_time = 0
            
            while True:
                ai_ret = ai_process.poll()
                
                try:
                    generated_files = os.listdir(temp_out)
                except:
                    generated_files = []

                for fname in generated_files:
                    if fname not in processed_files:
                        full_path = os.path.join(temp_out, fname)
                        
                        if self.wait_for_file(full_path):
                            orig_name = None
                            base_name = os.path.splitext(fname)[0]
                            for k, v in file_map.items():
                                if os.path.splitext(v)[0] == base_name:
                                    orig_name = k
                                    break
                            
                            if orig_name:
                                futures.append(cpu_executor.submit(cpu_worker_task, (full_path, orig_name)))
                                processed_files.add(fname)

                done_count = len(processed_files)
                percent = (done_count / img_cnt) * 100
                
                if time.time() - last_log_time > 1.0 and done_count > 0:
                     finished_cpu = sum(1 for f in futures if f.done())
                     self.log(f"      [Pipeline] GPU产出: {done_count} | CPU完成: {finished_cpu} ({percent:.1f}%)")
                     last_log_time = time.time()

                global_prog = base_progress + (done_count / img_cnt) * (1.0 / total_files)
                self.update_progress(global_prog, f"流水线处理中: {done_count}/{img_cnt}")

                if ai_ret is not None:
                    if ai_ret != 0:
                        self.log(f"❌ AI 引擎异常退出 (Code {ai_ret})")
                        break
                    
                    if len(processed_files) >= img_cnt:
                        break
                    
                    if len(generated_files) == len(processed_files):
                         time.sleep(2)
                         if len(os.listdir(temp_out)) == len(processed_files):
                             break
                
                time.sleep(0.2)

            self.log("   -> 等待 CPU 收尾...")
            for f in as_completed(futures):
                res = f.result()
                if res:
                    processed_data[res[0]] = res[1]
            
            cpu_executor.shutdown()

            # 4. 打包
            self.log("   -> 打包 EPUB...")
            with zipfile.ZipFile(temp_epub_file, 'w', zipfile.ZIP_DEFLATED) as zout:
                for fname, data in processed_data.items(): zout.writestr(fname, data)
                for fname, data in non_image_files.items(): zout.writestr(fname, data)

            if os.path.exists(epub_path): os.remove(epub_path)
            os.rename(temp_epub_file, epub_path)
            return True

        except Exception as e:
            self.log(f"❌ 流程错误: {e}")
            return False

    def wait_for_file(self, path, retries=5):
        for _ in range(retries):
            try:
                with open(path, 'rb'): pass
                return True
            except:
                time.sleep(0.1)
        return False

    def safe_rmtree(self, path):
        if os.path.exists(path):
            try: shutil.rmtree(path, onerror=self.force_remove_readonly)
            except: pass

    def force_remove_readonly(self, func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        try: func(path)
        except: pass

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = ModernMangaApp()
    app.mainloop()