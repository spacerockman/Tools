import subprocess
import os
import sys
import zipfile
import io
import time

# 尝试导入 Pillow，如果没装则报错提示
try:
    from PIL import Image, ImageOps
except ImportError:
    print("❌ 错误: 缺少 Pillow 库。")
    print("请运行: pip install pillow")
    sys.exit(1)

# ================= ⚙️ 全局配置区域 =================

# 1. KCC 程序路径
KCC_PATH = r"C:\Program Files\kindleComicConverter\kcc_c2e_9.2.2.exe"

# 2. 文件夹路径
INPUT_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\inputs"
OUTPUT_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\outputs"

# 3. 目标设备: Kindle 12代 (7英寸) -> 代码 'KO'
DEVICE_PROFILE = 'KO' 

# 4. 深度压缩参数
# 任何亮于 230 的颜色变成纯白(255)，暗于 30 的变成纯黑(0)
WHITE_THRESHOLD = 230 
BLACK_THRESHOLD = 30
# 最终 JPEG 质量 (65 是 Kindle 漫画的最佳平衡点)
JPEG_QUALITY = 65 

# ===================================================

def run_kcc_conversion(input_path, output_path):
    """
    第一阶段：调用 KCC 进行基础转换
    """
    print(f"   [1/2] 正在调用 KCC 转换 (智能切边 + 适配分辨率)...")
    
    cmd = [
        KCC_PATH,
        input_path,
        '-m',               # 漫画模式
        # 无 -q 参数 = 允许基础 JPEG 压缩
        '-s',               # 智能切边
        '--upscale',        # 自动放大
        '-g', '1.2',        # Gamma 校正
        '--format=EPUB',    # 输出格式
        '-p', DEVICE_PROFILE, 
        '--output', output_path
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # 只打印少量的关键日志，避免刷屏
        for line in process.stdout:
            pass # 这里如果不想要刷屏，可以 pass 掉，或者有选择地 print
            
        process.wait()
        
        if process.returncode == 0 and os.path.exists(output_path):
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ KCC 运行错误: {e}")
        return False

def optimize_image_data(img_data):
    """
    图像处理核心算法：灰度化 -> 色阶清洗 -> 压缩
    """
    try:
        img = Image.open(io.BytesIO(img_data))
        
        # 强制转为灰度 (L模式)
        if img.mode != 'L':
            img = img.convert('L')

        # 色阶映射表 (Lookup Table) - 极速处理
        lut = []
        for i in range(256):
            if i < BLACK_THRESHOLD:
                lut.append(0)
            elif i > WHITE_THRESHOLD:
                lut.append(255)
            else:
                val = int((i - BLACK_THRESHOLD) * 255 / (WHITE_THRESHOLD - BLACK_THRESHOLD))
                lut.append(val)
        img = img.point(lut)

        # 导出
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        return output.getvalue()
    except:
        return img_data # 出错则返回原图

def run_deep_optimization(epub_path):
    """
    第二阶段：解压 EPUB 进行深度优化
    """
    print(f"   [2/2] 正在进行深度优化 (去噪 + 强力压缩)...")
    
    temp_epub = epub_path + ".temp"
    original_size = os.path.getsize(epub_path)
    
    try:
        with zipfile.ZipFile(epub_path, 'r') as zin, zipfile.ZipFile(temp_epub, 'w', zipfile.ZIP_DEFLATED) as zout:
            file_list = zin.infolist()
            total = len(file_list)
            
            for i, item in enumerate(file_list):
                content = zin.read(item.filename)
                
                # 只处理图片
                if item.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    new_content = optimize_image_data(content)
                    zout.writestr(item, new_content)
                else:
                    zout.writestr(item, content)

        # 替换原文件
        os.remove(epub_path)
        os.rename(temp_epub, epub_path)
        
        final_size = os.path.getsize(epub_path)
        return original_size, final_size
        
    except Exception as e:
        print(f"❌ 优化失败: {e}")
        if os.path.exists(temp_epub):
            os.remove(temp_epub)
        return original_size, original_size

def main():
    # 检查环境
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    if not os.path.exists(KCC_PATH):
        print(f"❌ 找不到 KCC 程序: {KCC_PATH}")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not files:
        print("⚠️  inputs 文件夹为空")
        return

    print(f"🎯 任务队列: {len(files)} 个文件")
    print(f"⚙️  策略: KCC转换(KO) -> 深度去噪 -> 高压缩")
    print("-" * 60)

    total_start_time = time.time()

    for file in files:
        file_start_time = time.time()
        input_path = os.path.join(INPUT_DIR, file)
        output_filename = os.path.splitext(file)[0] + ".epub"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"🚀 处理中: {file}")
        
        # --- 步骤 1: KCC 转换 ---
        if run_kcc_conversion(input_path, output_path):
            
            # --- 步骤 2: 深度优化 ---
            size_before, size_after = run_deep_optimization(output_path)
            
            # --- 统计 ---
            duration = time.time() - file_start_time
            reduction = (size_before - size_after) / size_before * 100 if size_before > 0 else 0
            
            mb_before = size_before / 1024 / 1024
            mb_after = size_after / 1024 / 1024
            
            print(f"✅ 完成! 耗时 {duration:.1f}秒")
            print(f"   📉 体积优化: {mb_before:.2f}MB -> {mb_after:.2f}MB (减小了 {reduction:.1f}%)")
        else:
            print(f"❌ KCC 转换阶段失败，跳过后续步骤。")
        
        print("-" * 60)

    total_duration = time.time() - total_start_time
    print(f"🎉 全部任务完成! 总耗时: {total_duration:.1f}秒")
    print(f"📂 输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()