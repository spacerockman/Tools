import subprocess
import os
import sys
import zipfile
import io
import time
import shutil
import numpy as np
from PIL import Image, ImageOps
from concurrent.futures import ThreadPoolExecutor

# ================= ⚙️ 配置区域 =================

# 1. KCC 路径
KCC_PATH = r"C:\Program Files\kindleComicConverter\kcc_c2e_9.2.2.exe"

# 2. Real-ESRGAN 路径
REAL_ESRGAN_PATH = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\MangaTools\tools\realesrgan-ncnn-vulkan-v0.2.0-windows\realesrgan-ncnn-vulkan.exe"

# 3. 输入输出
INPUT_DIR = r"C:\Users\xujin\Downloads\comic\input"
OUTPUT_DIR = r"C:\Users\xujin\Downloads\comic\input"
DEVICE_PROFILE = 'KO' 

# 4. 临时文件夹 (用于批处理)
TEMP_WORK_DIR = r"C:\Users\xujin\Downloads\comic\input\temp_work"

# --- 参数 ---
TARGET_WIDTH = 1264
QUANTIZE_COLORS = 8 
JPEG_QUALITY = 45 

# ===============================================

def run_kcc_conversion(input_path, output_path):
    print(f"   [1/4] KCC 基础转换...")
    cmd = [
        KCC_PATH, input_path,
        '-m', '-s', '-g', '1.0', 
        '--format=EPUB', '-p', DEVICE_PROFILE, 
        '--output', output_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except:
        return False

def cpu_post_process_single(args):
    """
    单个图片的 CPU 后处理：缩放 + 量化 (多线程调用)
    """
    img_path, original_filename = args
    try:
        # 打开 AI 放大后的图片
        img = Image.open(img_path)
        
        # 1. 转灰度
        if img.mode != 'L':
            img = img.convert('L')

        # 2. 缩放 (LANCZOS)
        w, h = img.size
        if w > TARGET_WIDTH:
            ratio = TARGET_WIDTH / w
            new_h = int(h * ratio)
            img = img.resize((TARGET_WIDTH, new_h), Image.Resampling.LANCZOS)

        # 3. 8色量化 (转RGB->量化->转L)
        img_rgb = img.convert("RGB")
        img_quant = img_rgb.quantize(colors=QUANTIZE_COLORS, method=2)
        img = img_quant.convert('L')
        
        # 4. 自动对比度
        img = ImageOps.autocontrast(img, cutoff=1)

        # 5. 导出字节流
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True, subsampling=0)
        
        return (original_filename, output.getvalue())
    except Exception as e:
        print(f"Error processing {img_path}: {e}")
        return None

def run_deep_optimization(epub_path):
    # 准备临时目录
    temp_in = os.path.join(TEMP_WORK_DIR, "in")
    temp_out = os.path.join(TEMP_WORK_DIR, "out")
    
    # 清理旧数据
    if os.path.exists(TEMP_WORK_DIR): shutil.rmtree(TEMP_WORK_DIR)
    os.makedirs(temp_in)
    os.makedirs(temp_out)

    temp_epub = epub_path + ".temp"
    original_size = os.path.getsize(epub_path)
    
    # 映射表：文件名 -> 临时文件名
    # 结构： file_map = { "original_epub_path": "temp_filename.jpg" }
    file_map = {}
    non_image_files = {} # 存储非图片文件内容

    print(f"   [2/4] 解压图片到临时目录...")
    with zipfile.ZipFile(epub_path, 'r') as zin:
        file_list = zin.infolist()
        img_idx = 0
        for item in file_list:
            content = zin.read(item.filename)
            if item.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                # 生成简单的文件名避免特殊字符问题
                ext = os.path.splitext(item.filename)[1]
                temp_name = f"img_{img_idx:05d}{ext}"
                temp_path = os.path.join(temp_in, temp_name)
                
                with open(temp_path, "wb") as f:
                    f.write(content)
                
                file_map[item.filename] = temp_name
                img_idx += 1
            else:
                non_image_files[item.filename] = content

    print(f"   [3/4] 启动 GPU 批处理 (Real-ESRGAN x4 Anime)...")
    print(f"         (正在一次性处理 {img_idx} 张图片，AMD显卡火力全开...)")
    
    # === 🚀 关键：一次性调用 exe 处理整个文件夹 ===
    cmd = [
        REAL_ESRGAN_PATH,
        '-i', temp_in,   # 输入文件夹
        '-o', temp_out,  # 输出文件夹
        '-n', 'realesrgan-x4plus-anime', 
        '-s', '4',
        '-g', '0',       # GPU ID
        '-j', '4:4:4',   # 线程数 (Load:Proc:Save)，加大线程让 GPU 吃满
        '-f', 'jpg'      # 强制输出 jpg 节省这一步的 I/O 时间
    ]
    
    # 这一步会阻塞直到所有图片处理完
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"❌ GPU 处理失败: {e}")
        return original_size, original_size

    print(f"   [4/4] 多线程 CPU 后处理 (缩放+量化+打包)...")
    
    # 准备多线程任务
    tasks = []
    # Real-ESRGAN 批处理输出的文件名通常保持不变 (或者扩展名变了)
    # 我们遍历输出目录
    for orig_path, temp_name in file_map.items():
        # 注意：如果输入是 .png，输出也是 .png；如果输入是 .jpg，我们上面指定了 -f jpg
        # 但 Real-ESRGAN 有时会强制改扩展名，所以我们模糊匹配
        base_name = os.path.splitext(temp_name)[0]
        
        # 寻找对应的输出文件
        target_file = None
        for ext in ['.jpg', '.png', '.jpeg']:
            potential_path = os.path.join(temp_out, base_name + ext)
            if os.path.exists(potential_path):
                target_file = potential_path
                break
        
        if target_file:
            tasks.append((target_file, orig_path))
        else:
            print(f"⚠️ 警告：找不到 AI 处理后的文件: {temp_name}")

    # 使用 ThreadPoolExecutor 并行处理 CPU 任务 (缩放/量化)
    # 线程数设置为 CPU 核心数 + 4
    processed_data = {}
    with ThreadPoolExecutor(max_workers=os.cpu_count() + 4) as executor:
        results = executor.map(cpu_post_process_single, tasks)
        
        count = 0
        total = len(tasks)
        for res in results:
            if res:
                fname, data = res
                processed_data[fname] = data
                count += 1
                if count % 20 == 0:
                    print(f"      打包进度: {count}/{total}...", end='\r')

    print("") # 换行

    # 重新打包 EPUB
    with zipfile.ZipFile(temp_epub, 'w', zipfile.ZIP_DEFLATED) as zout:
        # 写入处理后的图片
        for fname, data in processed_data.items():
            zout.writestr(fname, data)
        
        # 写入非图片文件 (原样放回)
        for fname, data in non_image_files.items():
            zout.writestr(fname, data)

    # 替换文件
    if os.path.exists(epub_path): os.remove(epub_path)
    os.rename(temp_epub, epub_path)
    
    # 清理临时目录
    try:
        shutil.rmtree(TEMP_WORK_DIR)
    except:
        pass # 有时候 windows 会锁文件，忽略即可

    return original_size, os.path.getsize(epub_path)

def main():
    if not os.path.exists(REAL_ESRGAN_PATH):
        print(f"❌ 找不到 Real-ESRGAN: {REAL_ESRGAN_PATH}")
        return

    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not files:
        print("⚠️  inputs 文件夹为空")
        return

    print(f"⚡ 极速引擎启动: 文件夹级批处理 + 多线程流水线")
    print(f"🚀 AMD GPU 将满载运行，请稍候...")
    print("-" * 60)

    for file in files:
        start_time = time.time()
        input_path = os.path.join(INPUT_DIR, file)
        output_path = os.path.join(OUTPUT_DIR, os.path.splitext(file)[0] + ".epub")

        print(f"📚 任务: {file}")
        
        if run_kcc_conversion(input_path, output_path):
            size_before, size_after = run_deep_optimization(output_path)
            
            mb_before = size_before / 1024 / 1024
            mb_after = size_after / 1024 / 1024
            reduction = 0
            if size_before > 0:
                reduction = (size_before - size_after) / size_before * 100
            
            print(f"✅ 完成! 总耗时 {time.time()-start_time:.1f}s")
            print(f"   📉 {mb_before:.2f}MB -> {mb_after:.2f}MB (减小了 {reduction:.1f}%)")
        else:
            print("❌ KCC 转换失败")
        print("-" * 60)

if __name__ == "__main__":
    main()