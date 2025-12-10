import streamlit as st
from PIL import Image
from pillow_heif import register_heif_opener
import io
import zipfile

# 1. 注册 HEIC 打开器
register_heif_opener()

# 2. 页面配置
st.set_page_config(
    page_title="HEIC 图片转换器",
    page_icon="📸",
    layout="centered"
)

# 3. 样式优化
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background-color: #FF4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

def convert_image(upload_file, target_format):
    """转换核心逻辑"""
    image = Image.open(upload_file)
    file_name = upload_file.name.rsplit('.', 1)[0]
    
    # 兼容性处理：JPG/PDF 不支持透明背景，转为 RGB
    if target_format in ["JPEG", "PDF"] and image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[3]) # 使用 alpha 通道作为 mask
        else:
            background.paste(image)
        image = background
    
    output_buffer = io.BytesIO()
    
    save_format = "JPEG" if target_format == "JPG" else target_format
    
    # 保存
    if target_format == "PDF":
        image.save(output_buffer, format=save_format, resolution=100.0, save_all=True)
    else:
        image.save(output_buffer, format=save_format, quality=95)
    
    output_buffer.seek(0)
    new_filename = f"{file_name}.{target_format.lower()}"
    
    return output_buffer, new_filename

def main():
    st.title("📸 iPhone HEIC 转换器")
    st.markdown("基于 Python Streamlit 构建，本地运行，保护隐私。")

    with st.sidebar:
        st.header("⚙️ 选项")
        target_format = st.selectbox(
            "目标格式",
            options=["JPG", "PNG", "PDF", "WEBP", "BMP"],
            index=0
        )
        st.info("💡 提示：PDF 格式会保留原图比例。")

    uploaded_files = st.file_uploader(
        "📂 将 HEIC 照片拖拽到这里", 
        type=["heic", "HEIC"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        st.divider()
        st.write(f"已加载 **{len(uploaded_files)}** 张图片。目标格式：**{target_format}**")

        if st.button("🚀 开始转换"):
            # 单张下载
            if len(uploaded_files) == 1:
                with st.spinner("正在转换..."):
                    img_buffer, new_name = convert_image(uploaded_files[0], target_format)
                    st.success("✅ 转换完成！")
                    st.download_button(
                        label="⬇️ 点击下载",
                        data=img_buffer,
                        file_name=new_name,
                        mime=f"image/{target_format.lower()}" if target_format != "PDF" else "application/pdf"
                    )
            
            # 批量打包下载
            else:
                zip_buffer = io.BytesIO()
                progress_bar = st.progress(0)
                
                with st.spinner("正在批量转换并打包..."):
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        for i, file in enumerate(uploaded_files):
                            img_data, new_name = convert_image(file, target_format)
                            zf.writestr(new_name, img_data.getvalue())
                            progress_bar.progress((i + 1) / len(uploaded_files))
                
                zip_buffer.seek(0)
                st.success(f"✅ 全部 {len(uploaded_files)} 张图片转换完毕！")
                st.download_button(
                    label="📦 下载 ZIP 压缩包",
                    data=zip_buffer,
                    file_name=f"heic_converted_{target_format}.zip",
                    mime="application/zip"
                )

if __name__ == "__main__":
    main()