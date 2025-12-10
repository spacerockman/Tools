import subprocess
import os
import sys
import zipfile
import io
import time
import shutil
import numpy as np
from PIL import Image

# ================= ⚙️ 配置区域 =================

# 1. KCC 路径
KCC_PATH = r"C:\Program Files\kindleComicConverter\kcc_c2e_9.2.2.exe"

# 2. [关键] Real-ESRGAN ncnn vulkan 的 exe 路径
#    请修改为你解压的实际路径！
REAL_ESRGAN_PATH = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\realesrgan-ncnn-vulkan-v0.2.0-windows\realesrgan-ncnn-vulkan.exe"

# 3. 输入输出
INPUT_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\inputs"
OUTPUT_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\outputs"
DEVICE_PROFILE = 'KO' 

# --- 画质与压缩参数 ---

TARGET_WIDTH = 1264
# 动态直方图参数 (清洗背景)
LOWER_PERCENTILE = 2
UPPER_PERCENTILE = 98
GAMMA_VALUE = 1.3  # AI修复后的线条很实，Gamma不需要太激进
JPEG_QUALITY = 60  # 画面极纯净，60的质量足够，体积会很小

# ===============================================

def run_kcc_conversion(input_path, output_path):
    print(f"   [1/3] KCC 基础转换...")
    cmd = [
        KCC_PATH, input_path,
        '-m', '-s', 
        '-g', '1.0', 
        '--format=EPUB', '-p', DEVICE_PROFILE, 
        '--output', output_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except:
        return False

def process_image_with_realesrgan(img_data, filename_hint):
    """
    AMD GPU 加速核心：写入磁盘 -> 调用 exe 放大 -> 读取 -> 删除
    """
    # 临时文件名
    temp_in = f"temp_in_{filename_hint}.jpg"
    temp_out = f"temp_out_{filename_hint}.png" # ESRGAN 输出通常是 png

    try:
        # 1. 写入临时文件供 exe 读取
        with open(temp_in, "wb") as f:
            f.write(img_data)

        # 2. 调用 Real-ESRGAN NCNN (Vulkan加速)
        # -i 输入 -o 输出 -n 模型名 -s 缩放倍率
        # realesrgan-x4plus-anime 是专门针对二次元线条优化的模型，效果极好
        cmd = [
            REAL_ESRGAN_PATH,
            '-i', temp_in,
            '-o', temp_out,
            '-n', 'realesrgan-x4plus-anime', 
            '-s', '4', # 4倍放大 (虽然慢，但重绘效果最好，之后再缩小画质无敌)
            '-g', '0', # GPU ID, 0 通常是主显卡 (AMD)
            '-j', '2:2:2' # 线程数，可根据显卡性能调整
        ]
        
        # 这里的 capture_output=True 是为了不让控制台刷屏
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3. 读取放大后的图片
        if os.path.exists(temp_out):
            # 用 Pillow 打开
            img = Image.open(temp_out)
            return img
        else:
            # 失败回退
            return Image.open(io.BytesIO(img_data))

    except Exception as e:
        print(f"      [GPU Error] {e} (Falling back to CPU raw)")
        return Image.open(io.BytesIO(img_data))
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_in): os.remove(temp_in)
        if os.path.exists(temp_out): os.remove(temp_out)

def post_process_image(img):
    """
    后处理：超采样缩小 + 直方图清洗 + 压缩
    """
    try:
        # 1. 转灰度 (Kindle 不需要彩色)
        if img.mode != 'L':
            img = img.convert('L')

        # 2. 超采样缩小 (Super Sampling Downscale)
        # 此时 img 是经过 AI 放大的 4K/8K 图，缩小回 1264 会极其锐利
        w, h = img.size
        if w > TARGET_WIDTH:
            ratio = TARGET_WIDTH / w
            new_h = int(h * ratio)
            # LANCZOS 是缩小算法的画质天花板
            img = img.resize((TARGET_WIDTH, new_h), Image.Resampling.LANCZOS)

        # 3. 动态直方图清洗 (极致压缩的关键)
        img_arr = np.array(img)
        # 计算 2% 和 98% 分位点
        p_low, p_high = np.percentile(img_arr, (LOWER_PERCENTILE, UPPER_PERCENTILE))
        # 拉伸对比度，剔除背景噪点
        img_arr = (img_arr - p_low) * (255.0 / (p_high - p_low))
        img_arr = np.clip(img_arr, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_arr)

        # 4. Gamma 微调
        if GAMMA_VALUE != 1.0:
            lut = [int(((i / 255.0) ** GAMMA_VALUE) * 255) for i in range(256)]
            img = img.point(lut)

        # 5. 导出
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True, subsampling=0)
        return output.getvalue()

    except Exception as e:
        print(f"⚠️ 后处理错误: {e}")
        return None

def run_deep_optimization(epub_path):
    print(f"   [2/3] 启动 AMD GPU 加速引擎 (Real-ESRGAN x4 Anime)...")
    print(f"   [3/3] 正在进行超采样重绘 + 深度清洗...")
    
    temp_epub = epub_path + ".temp"
    original_size = os.path.getsize(epub_path)
    
    # 简单的计数器用于生成唯一临时文件名
    counter = 0

    try:
        with zipfile.ZipFile(epub_path, 'r') as zin, zipfile.ZipFile(temp_epub, 'w', zipfile.ZIP_DEFLATED) as zout:
            file_list = zin.infolist()
            total = len([x for x in file_list if x.filename.lower().endswith(('.jpg', '.png'))])
            current = 0
            
            for item in file_list:
                content = zin.read(item.filename)
                
                if item.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    current += 1
                    counter += 1
                    
                    # 打印进度条
                    print(f"      处理图片: {current}/{total}...", end='\r')
                    
                    # A. GPU AI 放大
                    img_pil = process_image_with_realesrgan(content, counter)
                    
                    # B. 后处理 (缩小+压缩)
                    new_content = post_process_image(img_pil)
                    
                    if new_content:
                        zout.writestr(item, new_content)
                    else:
                        zout.writestr(item, content)
                else:
                    zout.writestr(item, content)

        os.remove(epub_path)
        os.rename(temp_epub, epub_path)
        print("") # 换行
        return original_size, os.path.getsize(epub_path)
        
    except Exception as e:
        print(f"\n❌ 优化出错: {e}")
        if os.path.exists(temp_epub): os.remove(temp_epub)
        return original_size, original_size

def main():
    # 检查 exe 是否存在
    if not os.path.exists(REAL_ESRGAN_PATH):
        print(f"❌ 错误：找不到 Real-ESRGAN 程序。")
        print(f"请下载 realesrgan-ncnn-vulkan 并解压。")
        print(f"当前配置路径: {REAL_ESRGAN_PATH}")
        return

    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not files:
        print("⚠️  inputs 文件夹为空")
        return

    print(f"🧬 终极引擎启动: Real-ESRGAN (Anime) + 动态直方图")
    print(f"🚀 使用 AMD GPU (Vulkan) 进行矢量级重绘")
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
            reduction = (size_before - size_after) / size_before * 100
            
            print(f"✅ 完成! 耗时 {time.time()-start_time:.1f}s")
            print(f"   📉 {mb_before:.2f}MB -> {mb_after:.2f}MB (减小了 {reduction:.1f}%)")
        else:
            print("❌ KCC 转换失败")
        print("-" * 60)

if __name__ == "__main__":
    main()