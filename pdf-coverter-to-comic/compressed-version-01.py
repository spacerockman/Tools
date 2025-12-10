import os
import zipfile
import io
from PIL import Image, ImageOps

# ================= 配置区域 =================
# 你的 EPUB 输出目录
TARGET_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\outputs"

# --- 算法参数 (关键) ---
# 任何亮于 230 的颜色都会变成纯白 (255) -> 极大减小体积
WHITE_THRESHOLD = 230 
# 任何暗于 30 的颜色都会变成纯黑 (0) -> 增加对比度
BLACK_THRESHOLD = 30
# JPEG 压缩质量 (对于去噪后的黑白漫画，65 在 Kindle 上肉眼很难看出区别，但体积极小)
JPEG_QUALITY = 65 
# ===========================================

def optimize_image(img_data):
    """
    核心算法：加载图片 -> 转单通道灰度 -> 色阶映射(去噪) -> 重新压缩
    """
    try:
        # 1. 加载图片
        img = Image.open(io.BytesIO(img_data))
        
        # 2. 强制转为 'L' 模式 (8位灰度)
        if img.mode != 'L':
            img = img.convert('L')

        # 3. 色阶调整算法 (Levels Adjustment)
        # 利用查找表 (Lookup Table) 快速处理像素
        # 公式：将 [BLACK_THRESHOLD, WHITE_THRESHOLD] 映射到 [0, 255]
        lut = []
        for i in range(256):
            if i < BLACK_THRESHOLD:
                lut.append(0)
            elif i > WHITE_THRESHOLD:
                lut.append(255)
            else:
                # 线性插值
                val = int((i - BLACK_THRESHOLD) * 255 / (WHITE_THRESHOLD - BLACK_THRESHOLD))
                lut.append(val)
        
        # 应用映射
        img = img.point(lut)

        # 4. 导出为优化后的 JPEG 字节流
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        return output.getvalue()
        
    except Exception as e:
        # 如果出错，返回原数据
        print(f"   [警告] 图片处理失败: {e}")
        return img_data

def process_epub(epub_path):
    print(f"🔧 正在深度优化: {os.path.basename(epub_path)}")
    
    # 创建临时文件
    temp_epub = epub_path + ".temp"
    
    original_size = os.path.getsize(epub_path)
    
    try:
        # 打开原本的 EPUB (读) 和 临时的 EPUB (写)
        with zipfile.ZipFile(epub_path, 'r') as zin, zipfile.ZipFile(temp_epub, 'w', zipfile.ZIP_DEFLATED) as zout:
            file_list = zin.infolist()
            total_files = len(file_list)
            
            for i, item in enumerate(file_list):
                # 读取原数据
                content = zin.read(item.filename)
                
                # 判断是否为图片 (KCC生成的EPUB图片通常在 OEBPS/Images 或 images 下，且为 jpg/png)
                if item.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    # 执行图像优化算法
                    new_content = optimize_image(content)
                    zout.writestr(item, new_content)
                else:
                    # 非图片文件 (xml, css 等) 直接复制
                    zout.writestr(item, content)
                
                # 简单的进度显示
                if i % 10 == 0:
                    print(f"   进度: {i}/{total_files}...", end='\r')

        # 替换文件
        os.remove(epub_path)
        os.rename(temp_epub, epub_path)
        
        new_size = os.path.getsize(epub_path)
        reduction = (original_size - new_size) / original_size * 100
        
        print(f"\n✅ 优化完成!")
        print(f"   原始体积: {original_size / 1024 / 1024:.2f} MB")
        print(f"   最终体积: {new_size / 1024 / 1024:.2f} MB")
        print(f"   🚀 缩减了: {reduction:.1f}%")
        print("-" * 50)
        
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        if os.path.exists(temp_epub):
            os.remove(temp_epub)

def main():
    if not os.path.exists(TARGET_DIR):
        print("找不到输出目录")
        return

    epubs = [f for f in os.listdir(TARGET_DIR) if f.lower().endswith('.epub')]
    
    if not epubs:
        print("目录下没有 EPUB 文件")
        return

    print(f"🎯 发现 {len(epubs)} 个 EPUB，开始深度压缩算法...")
    print("💡 提示：此过程涉及大量像素计算，速度可能稍慢。")
    print("-" * 50)

    for epub in epubs:
        process_epub(os.path.join(TARGET_DIR, epub))

if __name__ == "__main__":
    main()