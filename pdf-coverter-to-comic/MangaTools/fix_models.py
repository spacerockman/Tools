import os
import requests
import zipfile
import io
import shutil

# ================= 配置 =================
# 你的工具目录
TARGET_TOOL_DIR = r"D:\BaiduNetdiskDownload\onedrive\Desktop\workspace\Tools\pdf-coverter-to-comic\MangaTools\tools\realesrgan-ncnn-vulkan-v0.2.0-windows"
MODELS_DIR = os.path.join(TARGET_TOOL_DIR, "models")

# ✅ 官方文档中引用的真实地址 (v0.2.5.0)
# 包含 exe 和所有 models
ZIP_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
# =======================================

def main():
    print(f"🔧 启动模型修复工具 (官方文档版)...")
    print(f"📂 目标目录: {MODELS_DIR}")
    
    os.makedirs(MODELS_DIR, exist_ok=True)

    print(f"\n⬇️ 正在下载完整 ZIP (约 15MB)...")
    print(f"   地址: {ZIP_URL}")
    
    try:
        response = requests.get(ZIP_URL, stream=True)
        if response.status_code != 200:
            print(f"❌ 下载失败，状态码: {response.status_code}")
            print("请手动复制上面的 URL 到浏览器下载。")
            return
        
        print("✅ 下载完成，正在提取模型...")
        
        extracted_count = 0
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            for filename in z.namelist():
                # 这个包里的结构通常是根目录下就有 models 文件夹
                if filename.endswith(".bin") or filename.endswith(".param"):
                    basename = os.path.basename(filename)
                    target_path = os.path.join(MODELS_DIR, basename)
                    
                    with open(target_path, "wb") as f:
                        f.write(z.read(filename))
                    
                    print(f"   -> 已恢复: {basename}")
                    extracted_count += 1

        print("-" * 50)
        if extracted_count > 0:
            print(f"🎉 成功提取了 {extracted_count} 个模型文件！")
            print("🚀 修复完成！请重新运行 main_gui.py")
        else:
            print("❌ 解压成功但未找到模型文件，请检查 ZIP 内容。")

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()