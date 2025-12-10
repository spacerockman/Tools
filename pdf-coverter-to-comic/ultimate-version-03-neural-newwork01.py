import subprocess
import os
import sys
import zipfile
import io
import time
import requests
import numpy as np
import cv2 # 需要 opencv-contrib-python

# ================= ⚙️ 配置区域 =================

KCC_PATH = r"C:\Program Files\kindleComicConverter\kcc_c2e_9.2.2.exe"
INPUT_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\inputs"
OUTPUT_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\outputs"
DEVICE_PROFILE = 'KO' 

# --- AI & 图像参数 ---

# 1. 目标宽度：Kindle 12代物理极限
TARGET_WIDTH = 1264

# 2. Gamma 值：AI 重绘后线条会变清晰，1.4 的 Gamma 能让黑色更扎实
GAMMA_VALUE = 1.4

# 3. 压缩质量：配合 AI 降噪后的纯净画面，60 依然完美
JPEG_QUALITY = 60

# 4. AI 模型路径 (脚本会自动下载，无需手动寻找)
MODEL_NAME = "FSRCNN_x2.pb"
MODEL_URL = "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x2.pb"

# ===============================================

def check_and_download_model():
    """检查 AI 模型是否存在，不存在则自动下载"""
    if not os.path.exists(MODEL_NAME):
        print(f"⬇️ 正在下载神经网络模型 ({MODEL_NAME})...")
        try:
            response = requests.get(MODEL_URL, stream=True)
            if response.status_code == 200:
                with open(MODEL_NAME, 'wb') as f:
                    f.write(response.content)
                print("✅ 模型下载完成！")
            else:
                print("❌ 模型下载失败，请检查网络。")
                sys.exit(1)
        except Exception as e:
            print(f"❌ 下载出错: {e}")
            sys.exit(1)

def run_kcc_conversion(input_path, output_path):
    print(f"   [1/2] KCC 结构转换...")
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

# 初始化 AI 超分对象 (全局复用，提高速度)
sr = cv2.dnn_superres.DnnSuperResImpl_create()
model_loaded = False

def neural_enhance_image(img_bytes):
    """
    🧠 核心算法：AI 重绘 (FSRCNN) + 物理缩放 + Gamma
    """
    global model_loaded, sr
    
    # 1. 解码为 OpenCV 格式
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE) # 直接读为灰度，省流
    
    if img is None: return img_bytes

    # --- 步骤 A: 神经网络重绘 (AI Super Resolution) ---
    # 只有当图片不是特别巨大的时候才启用 AI，否则速度会太慢
    # FSRCNN 速度很快，但如果原图已经是 4000px 宽，再放大 2 倍内存会爆
    h, w = img.shape[:2]
    
    # 加载模型 (只加载一次)
    if not model_loaded:
        sr.readModel(MODEL_NAME)
        sr.setModel("fsrcnn", 2) # 2倍放大
        model_loaded = True
    
    # 策略：如果图片宽度小于 1500，我们用 AI 放大重绘
    # 这能极大改善低分辨率扫描件的画质，去除噪点
    if w < 1500:
        try:
            # AI 推理 (重绘线条)
            img = sr.upsample(img)
            # 更新尺寸
            h, w = img.shape[:2]
        except Exception as e:
            print(f"   [AI跳过] 显存/内存不足或报错: {e}")

    # --- 步骤 B: 物理缩放 (Super Sampling Downscale) ---
    # 将刚刚可能被 AI 放大的高清图，或者原本的高清图，
    # 使用 "区域插值 (INTER_AREA)" 缩小回 1264px
    # INTER_AREA 是缩小图片时画质最好的算法，能产生抗锯齿效果
    if w > TARGET_WIDTH:
        ratio = TARGET_WIDTH / w
        new_h = int(h * ratio)
        img = cv2.resize(img, (TARGET_WIDTH, new_h), interpolation=cv2.INTER_AREA)

    # --- 步骤 C: Gamma 增强 (LUT) ---
    if GAMMA_VALUE != 1.0:
        # OpenCV 的 LUT 速度极快
        lut = np.empty((1, 256), np.uint8)
        for i in range(256):
            lut[0, i] = np.clip(pow(i / 255.0, GAMMA_VALUE) * 255.0, 0, 255)
        img = cv2.LUT(img, lut)

    # --- 步骤 D: 编码导出 ---
    # 使用 OpenCV 的 JPEG 编码
    params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    success, encoded_img = cv2.imencode('.jpg', img, params)
    
    return encoded_img.tobytes() if success else img_bytes

def run_deep_optimization(epub_path):
    print(f"   [2/2] 正在进行神经网络重绘 (FSRCNN) + 超采样缩放...")
    temp_epub = epub_path + ".temp"
    original_size = os.path.getsize(epub_path)
    
    try:
        with zipfile.ZipFile(epub_path, 'r') as zin, zipfile.ZipFile(temp_epub, 'w', zipfile.ZIP_DEFLATED) as zout:
            file_list = zin.infolist()
            total = len(file_list)
            
            for i, item in enumerate(file_list):
                content = zin.read(item.filename)
                
                if item.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    new_content = neural_enhance_image(content)
                    zout.writestr(item, new_content)
                else:
                    zout.writestr(item, content)
                
                # 打印进度，因为AI处理比较慢
                if i % 5 == 0:
                    print(f"      进度: {i}/{total} 页 processed...", end='\r')

        os.remove(epub_path)
        os.rename(temp_epub, epub_path)
        print("") # 换行
        return original_size, os.path.getsize(epub_path)
        
    except Exception as e:
        print(f"❌ 优化出错: {e}")
        if os.path.exists(temp_epub): os.remove(temp_epub)
        return original_size, original_size

def main():
    # 0. 检查模型
    check_and_download_model()

    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not files:
        print("⚠️  inputs 文件夹为空")
        return

    print(f"🧬 启动引擎: 神经网络超分 (FSRCNN) + 物理抗锯齿缩放")
    print(f"✅ 专为 Kindle 12代 优化")
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