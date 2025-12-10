import subprocess
import os
import sys

# ================= 配置区域 =================

# 1. 这里保持你刚才正确的路径
KCC_PATH = r"C:\Program Files\kindleComicConverter\kcc_c2e_9.2.2.exe"

# 2. 输入输出路径
INPUT_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\inputs"
OUTPUT_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\outputs"

# 3. [关键修改] 目标设备代码
# KO = Kindle Oasis (7英寸)，这是 Kindle 12代 (2024) 的最佳匹配
# KPW5 = Kindle Paperwhite 5 (6.8英寸)
DEVICE_PROFILE = 'KO' 

# ===========================================

def main():
    # 检查输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 获取 PDF 文件
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not files:
        print("⚠️  inputs 文件夹里没找到 PDF。")
        return

    print(f"🔍 KCC 路径: {KCC_PATH}")
    print(f"📱 目标设备: Kindle 12代 (使用 'KO' 配置文件)")
    print("-" * 50)

    for file in files:
        input_path = os.path.join(INPUT_DIR, file)
        # 这里的 output_filename 保持 epub 即可
        output_filename = os.path.splitext(file)[0] + ".epub"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"🚀 正在转换: {file}")
        
        cmd = [
            KCC_PATH,
            input_path,
            '-m',               # 漫画模式
            '-q',               # 高质量
            '-s',               # 智能切边
            '--upscale',        # 自动放大
            '-g', '1.2',        # Gamma 校正
            '--format=EPUB',    # 输出格式
            '-p', DEVICE_PROFILE, # 这里现在是 'KO'
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
                if line:
                    # 过滤掉一些不重要的进度条显示，只显示关键信息
                    if not line.startswith("\r"): 
                        print(f"   [KCC] {line}")
            
            process.wait()

            if process.returncode == 0 and os.path.exists(output_path):
                print(f"✅ 转换成功！文件已生成: {output_path}")
            else:
                print(f"❌ 转换可能失败，请检查上方日志。")

        except Exception as e:
            print(f"❌ 运行报错: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    main()