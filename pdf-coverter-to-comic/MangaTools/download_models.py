import os
import requests
import sys

# ================= 配置 =================
# 你的工具目录 (基于你之前的报错路径)
BASE_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\MangaTools\tools\realesrgan-ncnn-vulkan-v0.2.0-windows"
MODELS_DIR = os.path.join(BASE_DIR, "models")

# 我们只需要下载 Anime (二次元) 模型，因为脚本里指定用了这个
FILES = {
    "realesrgan-x4plus-anime.bin": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-x4plus-anime.bin",
    "realesrgan-x4plus-anime.param": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-x4plus-anime.param"
}
# =======================================

def download_file(url, dest_path):
    print(f"⬇️ 正在下载: {os.path.basename(dest_path)} ...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ 下载成功!")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

def main():
    if not os.path.exists(BASE_DIR):
        print(f"❌ 错误: 找不到 Real-ESRGAN 目录:\n{BASE_DIR}")
        print("请检查文件夹名称是否改动过。")
        return

    # 创建 models 文件夹
    if not os.path.exists(MODELS_DIR):
        print(f"📂 创建 models 文件夹...")
        os.makedirs(MODELS_DIR)

    print("-" * 50)
    print("开始补全缺失的模型文件...")
    
    success_count = 0
    for filename, url in FILES.items():
        dest_path = os.path.join(MODELS_DIR, filename)
        
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
            print(f"🆗 文件已存在，跳过: {filename}")
            success_count += 1
        else:
            if download_file(url, dest_path):
                success_count += 1
    
    print("-" * 50)
    if success_count == len(FILES):
        print("🎉 所有模型文件已就绪！")
        print("🚀 请重新运行主程序 main_gui.py")
    else:
        print("⚠️ 部分文件下载失败，请检查网络 (可能需要科学上网)。")

if __name__ == "__main__":
    main()