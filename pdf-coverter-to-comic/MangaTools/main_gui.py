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
import numpy as np
from PIL import Image, ImageOps
from concurrent.futures import ThreadPoolExecutor

# ================= 配置常量 =================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

TARGET_WIDTH = 1264
QUANTIZE_COLORS = 8
JPEG_QUALITY = 45
DEVICE_PROFILE = 'KO'

class MangaConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Kindle 漫画转换器 (智能防崩溃版)")
        self.geometry("750x600")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # 1. 标题
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        ctk.CTkLabel(self.header_frame, text="Manga Ultimate Converter", font=("Arial", 20, "bold")).pack(pady=5)
        ctk.CTkLabel(self.header_frame, text="自动降级机制 | 显存自适应 | CPU兜底", text_color="gray").pack(pady=(0, 5))

        # 2. 路径选择
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.path_frame, text="输入文件夹:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_input = ctk.CTkEntry(self.path_frame, placeholder_text="包含 PDF 的文件夹")
        self.entry_input.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.path_frame, text="浏览", width=60, command=self.select_input).grid(row=0, column=2, padx=10, pady=10)

        ctk.CTkLabel(self.path_frame, text="输出文件夹:").grid(row=1, column=0, padx=10, pady=10)
        self.entry_output = ctk.CTkEntry(self.path_frame, placeholder_text="选择保存位置")
        self.entry_output.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.path_frame, text="浏览", width=60, command=self.select_output).grid(row=1, column=2, padx=10, pady=10)

        # 3. 按钮
        self.btn_start = ctk.CTkButton(self, text="开始转换", command=self.start_process, height=40, font=("Arial", 14, "bold"))
        self.btn_start.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # 4. 日志
        self.textbox_log = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.textbox_log.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")

        self.init_tools_paths()

    def log(self, message):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

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
        self.log(f"根目录: {base_path}")

        path_7z_dir = os.path.join(tools_root, "7z")
        os.environ["PATH"] += os.pathsep + path_7z_dir
        
        self.kcc_exe = os.path.join(tools_root, "kindleComicConverter", "kcc_c2e_9.2.2.exe")
        self.ai_exe = os.path.join(tools_root, "realesrgan-ncnn-vulkan-v0.2.0-windows", "realesrgan-ncnn-vulkan.exe")

        # 检查 models 文件夹是否存在 (这是 0xC0000409 错误的另一个常见原因)
        models_dir = os.path.join(os.path.dirname(self.ai_exe), "models")
        
        missing = []
        if not os.path.exists(self.kcc_exe): missing.append(self.kcc_exe)
        if not os.path.exists(self.ai_exe): missing.append(self.ai_exe)
        if not os.path.exists(os.path.join(path_7z_dir, "7z.exe")): missing.append("7z.exe")
        if not os.path.exists(models_dir): missing.append("models 文件夹 (必须在 AI exe 旁边)")

        if missing:
            self.log("❌ 工具缺失，请检查 tools 结构:")
            for m in missing: self.log(f"   - {m}")
            self.btn_start.configure(state="disabled")
        else:
            self.log("✅ 工具完整性检查通过。")

    def start_process(self):
        input_dir = self.entry_input.get().strip()
        output_dir = self.entry_output.get().strip()

        if not input_dir or not os.path.exists(input_dir):
            self.log("⚠️ 无效输入目录")
            return
        if not output_dir:
            self.log("⚠️ 无效输出目录")
            return

        self.btn_start.configure(state="disabled", text="正在处理...")
        threading.Thread(target=self.run_logic, args=(input_dir, output_dir), daemon=True).start()

    def force_remove_readonly(self, func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        try: func(path)
        except Exception: pass

    def safe_rmtree(self, path):
        if os.path.exists(path):
            try: shutil.rmtree(path, onerror=self.force_remove_readonly)
            except Exception: pass

    def run_logic(self, input_dir, output_dir):
        files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
        if not files:
            self.log("❌ 没有找到 PDF")
            self.reset_ui()
            return

        self.log(f"🚀 任务队列: {len(files)} 个文件")
        temp_work_dir = os.path.join(tempfile.gettempdir(), "MangaConvert_Work")
        
        total_start = time.time()

        for idx, file in enumerate(files):
            file_start = time.time()
            self.log(f"\n[{idx+1}/{len(files)}] 处理中: {file}")
            
            input_path = os.path.join(input_dir, file)
            output_epub = os.path.join(output_dir, os.path.splitext(file)[0] + ".epub")
            
            self.log("   [1/2] KCC 转换...")
            if not self.run_kcc(input_path, output_epub):
                self.log("   ❌ KCC 失败")
                continue

            self.log("   [2/2] AI 重绘 (尝试 GPU -> 自动降级)...")
            res = self.deep_optimize(output_epub, temp_work_dir)
            
            if res:
                size_mb = os.path.getsize(output_epub) / 1024 / 1024
                self.log(f"   ✅ 成功! 体积: {size_mb:.2f} MB")
            
            self.log(f"   ⏳ 耗时: {time.time() - file_start:.1f} 秒")

        self.log(f"\n🎉 全部完成! 总耗时: {time.time() - total_start:.1f} 秒")
        self.safe_rmtree(temp_work_dir)
        self.reset_ui()

    def reset_ui(self):
        self.btn_start.configure(state="normal", text="开始转换")

    def run_kcc(self, input_path, output_path):
        cmd = [
            self.kcc_exe, input_path,
            '-m', '-s', '-g', '1.0',
            '--format=EPUB', '-p', DEVICE_PROFILE,
            '--output', output_path
        ]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                           check=True, startupinfo=startupinfo)
            return True
        except Exception as e:
            self.log(f"KCC Error: {e}")
            return False

    def deep_optimize(self, epub_path, work_dir):
        self.safe_rmtree(work_dir)
        time.sleep(0.2)
        
        temp_in = os.path.join(work_dir, "in")
        temp_out = os.path.join(work_dir, "out")
        
        try:
            os.makedirs(temp_in, exist_ok=True)
            os.makedirs(temp_out, exist_ok=True)
        except PermissionError:
             self.log("❌ 无法创建临时目录")
             return False

        temp_epub_file = epub_path + ".temp"
        file_map = {}
        non_image_files = {}

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

            # ==========================================
            # 🛡️ 智能防崩溃 AI 调用逻辑
            # ==========================================
            ai_success = False
            
            # 基础命令参数
            base_cmd = [
                self.ai_exe,
                '-i', temp_in,
                '-o', temp_out,
                '-n', 'realesrgan-x4plus-anime',
                '-s', '4',
                '-f', 'jpg'
            ]
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # 方案 A: 激进模式 (GPU, Tile 100) - 速度快
            if not ai_success:
                try:
                    self.log("      尝试方案 A: GPU 加速 (Tile 100)...")
                    cmd = base_cmd + ['-g', '0', '-j', '1:1:1', '-t', '100']
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                    ai_success = True
                except subprocess.CalledProcessError:
                    self.log("      ⚠️ 方案 A 失败 (显存不足)")

            # 方案 B: 安全模式 (GPU, Tile 32) - 极小切块，极省显存
            if not ai_success:
                try:
                    self.log("      尝试方案 B: 安全模式 (Tile 32)...")
                    cmd = base_cmd + ['-g', '0', '-j', '1:1:1', '-t', '32']
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                    ai_success = True
                except subprocess.CalledProcessError:
                    self.log("      ⚠️ 方案 B 失败 (严重显存不足或驱动问题)")

            # 方案 C: CPU 兜底 (GPU ID -1) - 慢但绝对稳
            if not ai_success:
                try:
                    self.log("      尝试方案 C: CPU 兜底模式 (慢但稳)...")
                    # CPU 模式不需要 tile size，因为它使用系统内存
                    cmd = base_cmd + ['-g', '-1'] 
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                    ai_success = True
                except subprocess.CalledProcessError as e:
                    self.log(f"      ❌ 所有方案均失败: {e}")
                    return False

            # ==========================================

            tasks = []
            for orig_path, simple_name in file_map.items():
                base = os.path.splitext(simple_name)[0]
                potential = os.path.join(temp_out, base + ".jpg")
                if not os.path.exists(potential): potential = os.path.join(temp_out, base + ".png")
                
                if os.path.exists(potential):
                    tasks.append((potential, orig_path))
            
            processed_data = {}
            with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                results = executor.map(self.cpu_process_single, tasks)
                for res in results:
                    if res: processed_data[res[0]] = res[1]

            with zipfile.ZipFile(temp_epub_file, 'w', zipfile.ZIP_DEFLATED) as zout:
                for fname, data in processed_data.items(): zout.writestr(fname, data)
                for fname, data in non_image_files.items(): zout.writestr(fname, data)

            if os.path.exists(epub_path): os.remove(epub_path)
            os.rename(temp_epub_file, epub_path)
            
            return True

        except Exception as e:
            self.log(f"优化未知错误: {e}")
            return False

    def cpu_process_single(self, args):
        img_path, original_filename = args
        try:
            img = Image.open(img_path)
            if img.mode != 'L': img = img.convert('L')

            w, h = img.size
            if w > TARGET_WIDTH:
                ratio = TARGET_WIDTH / w
                new_h = int(h * ratio)
                img = img.resize((TARGET_WIDTH, new_h), Image.Resampling.LANCZOS)
            
            img_rgb = img.convert("RGB")
            img_quant = img_rgb.quantize(colors=QUANTIZE_COLORS, method=2)
            img = img_quant.convert('L')
            img = ImageOps.autocontrast(img, cutoff=1)

            out = io.BytesIO()
            img.save(out, format='JPEG', quality=JPEG_QUALITY, optimize=True, subsampling=0)
            return (original_filename, out.getvalue())
        except:
            return None

if __name__ == "__main__":
    app = MangaConverterApp()
    app.mainloop()