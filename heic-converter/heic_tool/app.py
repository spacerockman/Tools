import streamlit as st
from PIL import Image
from pillow_heif import register_heif_opener
import io
import zipfile

# 1. 注册 HEIC 支持 (让 PIL 能读懂 HEIC)
register_heif_opener()

# 2. 页面配置
st.set_page_config(
    page_title="万能图片格式转换器",
    page_icon="🎨",
    layout="centered"
)

# 3. 样式优化 (CSS)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #4CAF50; /* 换个清新的绿色 */
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    /* 调整上传区域样式 */
    [data-testid="stFileUploader"] {
        padding: 2rem;
        border-radius: 10px;
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

def convert_image(upload_file, target_format):
    """
    通用转换函数
    """
    # 打开图片 (PIL 会自动识别 JPG, PNG, WEBP, HEIC 等)
    image = Image.open(upload_file)
    
    # 获取原始文件名（不带后缀）
    file_name = upload_file.name.rsplit('.', 1)[0]
    
    # === 兼容性处理 ===
    # 如果目标格式不支持透明度 (JPEG, PDF)，或者原图是 P 模式(调色板)，需要转为 RGB
    # 比如：把透明背景的 PNG 转为 JPG，背景需要变成白色，否则会变黑
    if target_format in ["JPEG", "PDF"] and image.mode in ("RGBA", "LA", "P"):
        # 创建一个白色背景的图像
        background = Image.new("RGB", image.size, (255, 255, 255))
        # 处理带透明通道的图
        if image.mode == 'RGBA' or image.mode == 'LA':
            # 使用 alpha 通道作为掩码进行粘贴
            background.paste(image, mask=image.split()[-1])
        else:
            # P 模式直接转换
            image = image.convert("RGBA")
            background.paste(image, mask=image.split()[-1])
        image = background
    elif target_format != "PDF":
        # 如果不是转 PDF，且不是转 JPG，通常保持原模式或转为 RGB 以防万一
        if image.mode == "P":
            image = image.convert("RGBA")

    output_buffer = io.BytesIO()
    
    # 修正 PIL 的格式名称 (JPG -> JPEG)
    save_format = "JPEG" if target_format == "JPG" else target_format
    
    # === 保存逻辑 ===
    if target_format == "PDF":
        # save_all=True 即使只有一张图也是好的实践
        image.save(output_buffer, format=save_format, resolution=100.0, save_all=True)
    else:
        # 图片格式通常设置一下质量
        image.save(output_buffer, format=save_format, quality=95)
    
    output_buffer.seek(0)
    
    # 生成新后缀
    new_ext = target_format.lower()
    new_filename = f"{file_name}.{new_ext}"
    
    return output_buffer, new_filename

def main():
    st.title("🎨 万能图片格式转换器")
    st.markdown("支持 **HEIC, PNG, JPG, WEBP, BMP, TIFF** 等格式互转。")

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 输出设置")
        target_format = st.selectbox(
            "要把图片转换成什么格式？",
            options=["JPG", "PNG", "PDF", "WEBP", "BMP", "ICO"],
            index=0 # 默认选 JPG
        )
        
        st.info(f"""
        **转换说明：**
        - 输入：支持几乎所有常见图片
        - 输出：目前选择转换为 **{target_format}**
        - 透明图转 JPG/PDF 会自动填充白底
        """)

    # 文件上传区 - 关键修改：扩大 type 列表
    allowed_types = ["heic", "png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif"]
    uploaded_files = st.file_uploader(
        "📂 拖拽图片到这里 (支持多选)", 
        type=allowed_types, 
        accept_multiple_files=True
    )

    if uploaded_files:
        st.divider()
        st.write(f"已加载 **{len(uploaded_files)}** 张图片 ➡️ 准备转换为 **{target_format}**")

        if st.button("🚀 开始转换"):
            
            # === 单张处理模式 ===
            if len(uploaded_files) == 1:
                with st.spinner("正在转换..."):
                    try:
                        img_buffer, new_name = convert_image(uploaded_files[0], target_format)
                        st.success("✅ 转换成功！")
                        
                        # 设置 MIME type
                        mime_type = "application/pdf" if target_format == "PDF" else f"image/{target_format.lower()}"
                        
                        st.download_button(
                            label=f"⬇️ 下载 {new_name}",
                            data=img_buffer,
                            file_name=new_name,
                            mime=mime_type
                        )
                    except Exception as e:
                        st.error(f"转换失败: {e}")
            
            # === 批量处理模式 (打包 ZIP) ===
            else:
                zip_buffer = io.BytesIO()
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("正在批量转换并打包..."):
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        success_count = 0
                        for i, file in enumerate(uploaded_files):
                            status_text.text(f"正在处理: {file.name} ...")
                            try:
                                img_data, new_name = convert_image(file, target_format)
                                zf.writestr(new_name, img_data.getvalue())
                                success_count += 1
                            except Exception as e:
                                st.warning(f"跳过文件 {file.name}: {e}")
                            
                            # 更新进度条
                            progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.empty() # 清空状态文字
                zip_buffer.seek(0)
                
                if success_count > 0:
                    st.success(f"✅ 完成！成功转换 {success_count} / {len(uploaded_files)} 张图片。")
                    st.download_button(
                        label="📦 下载所有图片 (ZIP压缩包)",
                        data=zip_buffer,
                        file_name=f"converted_images_{target_format}.zip",
                        mime="application/zip"
                    )
                else:
                    st.error("所有图片转换失败，请检查文件是否损坏。")

if __name__ == "__main__":
    main()