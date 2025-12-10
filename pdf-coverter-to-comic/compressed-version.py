import subprocess
import os
import sys

# ================= 配置区域 =================

KCC_PATH = r"C:\Program Files\kindleComicConverter\kcc_c2e_9.2.2.exe"
INPUT_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\inputs"
OUTPUT_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\outputs"

# 目标设备: Kindle 12代 (7英寸)
DEVICE_PROFILE = 'KO' 

# ===========================================

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not files:
        print("⚠️  inputs 文件夹里没找到 PDF。")
        return

    print(f"🔍 KCC 路径: {KCC_PATH}")
    print(f"📉 模式: 智能压缩 (JPEG压缩开启，去除无损标志)")
    print("-" * 50)

    for file in files:
        input_path = os.path.join(INPUT_DIR, file)
        output_filename = os.path.splitext(file)[0] + ".epub"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"🚀 正在转换并压缩: {file}")
        
        cmd = [
            KCC_PATH,
            input_path,
            '-m',               # 漫画模式
            # 1. 移除了 '-q': 启用 JPEG 压缩 (这是减小体积的主力)
            '-s',               # 智能切边
            # 2. 移除了报错的 '--grayscale': KCC 9.2.2 不支持此参数，但不需要它也能压缩
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

            for line in process.stdout:
                line = line.strip()
                if line and not line.startswith("\r"): 
                    print(f"   [KCC] {line}")
            
            process.wait()

            if process.returncode == 0 and os.path.exists(output_path):
                # 计算一下压缩后的体积
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"✅ 转换成功！")
                print(f"📦 输出文件: {output_path}")
                print(f"💾 当前体积: {size_mb:.2f} MB")
            else:
                print(f"❌ 转换可能失败，请检查上方日志。")

        except Exception as e:
            print(f"❌ 运行报错: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    main()