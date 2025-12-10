import subprocess
import os
import sys
import zipfile
import io
import time
from PIL import Image, ImageEnhance

# ================= ⚙️ 配置区域 =================

KCC_PATH = r"C:\Program Files\kindleComicConverter\kcc_c2e_9.2.2.exe"
INPUT_DIR = r"C:\Users\xujin\Downloads\comic\input"
OUTPUT_DIR = r"C:\Users\xujin\Downloads\comic\input"
DEVICE_PROFILE = 'KO' 

# --- 核心优化参数 ---

# 1. 目标宽度：Kindle 12代 (Oasis/PW5) 的物理分辨率宽度是 1264。
#    超过这个宽度的图片是浪费体积，缩放到这个尺寸是视觉无损压缩的关键。
TARGET_WIDTH = 1264

# 2. Gamma 值：用于加深黑色。
#    1.0 = 原图; >1.0 = 变黑; <1.0 = 变亮
#    1.4 是一个很安全的数值，能让灰蒙蒙的漫画变清晰，且不会造成空心。
GAMMA_VALUE = 1.4

# 3. 压缩质量：配合 subsampling=0，60 的质量在墨水屏上几乎看不出区别。
JPEG_QUALITY = 60

# ===============================================

def run_kcc_conversion(input_path, output_path):
    print(f"   [1/2] KCC 结构转换...")
    # 这里我们只让 KCC 做切边和排版，不做任何画质调整
    cmd = [
        KCC_PATH, input_path,
        '-m', '-s', 
        '-g', '1.0', # 保持原样，交给 Python 处理
        '--format=EPUB', '-p', DEVICE_PROFILE, 
        '--output', output_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except:
        return False

def safe_optimize_image(img_data):
    """
    🧪 核心算法：智能缩放 + Gamma压暗 + 高效编码
    """
    try:
        img = Image.open(io.BytesIO(img_data))
        
        # 1. 强制转为灰度 (L模式) - 这一步就砍掉 2/3 体积
        if img.mode != 'L':
            img = img.convert('L')

        # 2. 智能缩放 (Downscaling)
        # 如果图片宽度超过 Kindle 物理极限，用 Lanczos 算法高质量缩小
        w, h = img.size
        if w > TARGET_WIDTH:
            ratio = TARGET_WIDTH / w
            new_h = int(h * ratio)
            # LANZCOS 是画质最好的缩放算法，保留线条锐度
            img = img.resize((TARGET_WIDTH, new_h), Image.Resampling.LANCZOS)

        # 3. Gamma 增强 (加深黑色，但不丢失细节)
        # 公式: pixel = pixel ^ (1/gamma)
        # 这是一个平滑曲线，不会像阈值那样把黑色变成轮廓
        if GAMMA_VALUE != 1.0:
            # 建立 Gamma 映射表 (比逐像素计算快得多)
            lut = [int(((i / 255.0) ** GAMMA_VALUE) * 255) for i in range(256)]
            img = img.point(lut)

        # 4. 导出
        output = io.BytesIO()
        # subsampling=0: 关键参数！禁止色度抽样，保持线条边缘最锐利
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True, subsampling=0)
        return output.getvalue()

    except Exception as e:
        print(f"⚠️ 图片处理异常: {e}")
        return img_data

def run_deep_optimization(epub_path):
    print(f"   [2/2] 正在进行深度优化 (缩放至1264px + Gamma加深)...")
    temp_epub = epub_path + ".temp"
    original_size = os.path.getsize(epub_path)
    
    try:
        with zipfile.ZipFile(epub_path, 'r') as zin, zipfile.ZipFile(temp_epub, 'w', zipfile.ZIP_DEFLATED) as zout:
            file_list = zin.infolist()
            total = len(file_list)
            
            for i, item in enumerate(file_list):
                content = zin.read(item.filename)
                
                if item.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    new_content = safe_optimize_image(content)
                    zout.writestr(item, new_content)
                else:
                    zout.writestr(item, content)

        os.remove(epub_path)
        os.rename(temp_epub, epub_path)
        return original_size, os.path.getsize(epub_path)
        
    except Exception as e:
        print(f"❌ 优化出错: {e}")
        if os.path.exists(temp_epub): os.remove(temp_epub)
        return original_size, original_size

def main():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not files:
        print("⚠️  inputs 文件夹为空")
        return

    print(f"🧬 启动算法: 物理分辨率锁定(1264px) + Gamma平滑增强")
    print(f"✅ 已彻底移除不稳定的阈值算法，画质绝对安全")
    print("-" * 60)

    for file in files:
        start_time = time.time()
        input_path = os.path.join(INPUT_DIR, file)
        output_path = os.path.join(OUTPUT_DIR, os.path.splitext(file)[0] + ".epub")

        print(f"🚀 处理: {file}")
        
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