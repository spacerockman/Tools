import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import datetime
from pathlib import Path

class JohnnyDecimalRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("Johnny.Decimal 文件重命名工具")
        self.root.geometry("600x550")
        
        # 预设你的分类数据 (根据你的截图整理)
        self.categories = {
            "10_Personal Documents": [
                "10.01_身份类 (身份证/户口本)",
                "10.02_婚姻类 (结婚证)",
                "10.03_护照类 (护照/签证)",
                "10.04_在日证件 (MyNumber/住民票)",
                "10.05_年金・医疗关联",
                "10.06_海外证件",
                "10.07_医疗保险证"
            ],
            "20_Immigration": [
                "20.01_Japan",
                "20.02_USA"
            ],
            "30_Life": [
                "30.01_Housing",
                "30.02_Healthcare",
                "30.03_Travel",
                "30.04_Shopping",
                "30.05_Insurance",
                "30.06_Education"
            ],
            "40_Finance": [
                "40.01_Bank",
                "40.02_Tax",
                "40.03_NISA",
                "40.04_iDeCo",
                "40.05_Investment"
            ],
            "50_Career": [
                "50.01_Resume",
                "50.02_Job_Search",
                "50.03_Certifications",
                "50.04_Salary",
                "50.05_Work_History"
            ],
            "60_Projects": [], # 截图未展开，可自行补充
            "80_Entrepreneurship": [], # 截图未展开，可自行补充
            "90_Archive": [
                "90.01_Old_Work",
                "90.02_Old_Documents",
                "90.03_Old_Photos"
            ]
        }

        # 变量存储
        self.selected_file_path = tk.StringVar()
        self.category_main = tk.StringVar()
        self.category_sub = tk.StringVar()
        self.date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        self.desc_var = tk.StringVar()
        self.preview_var = tk.StringVar(value="请先选择文件...")

        # 界面布局
        self.create_widgets()

    def create_widgets(self):
        # 1. 文件选择区域
        file_frame = tk.LabelFrame(self.root, text="1. 选择原始文件", padx=10, pady=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        btn_select = tk.Button(file_frame, text="📁 选择文件", command=self.select_file, bg="#e1e1e1")
        btn_select.pack(side="left")

        lbl_file = tk.Label(file_frame, textvariable=self.selected_file_path, fg="gray", wraplength=450)
        lbl_file.pack(side="left", padx=10)

        # 2. 信息录入区域
        info_frame = tk.LabelFrame(self.root, text="2. 构建新名称", padx=10, pady=10)
        info_frame.pack(fill="x", padx=10, pady=5)

        # 主分类
        tk.Label(info_frame, text="主分类 (Area):").grid(row=0, column=0, sticky="w", pady=5)
        self.cb_main = ttk.Combobox(info_frame, textvariable=self.category_main, state="readonly", width=40)
        self.cb_main['values'] = list(self.categories.keys())
        self.cb_main.grid(row=0, column=1, sticky="w", pady=5)
        self.cb_main.bind("<<ComboboxSelected>>", self.update_sub_categories)

        # 子分类
        tk.Label(info_frame, text="子分类 (Category):").grid(row=1, column=0, sticky="w", pady=5)
        self.cb_sub = ttk.Combobox(info_frame, textvariable=self.category_sub, state="readonly", width=40)
        self.cb_sub.grid(row=1, column=1, sticky="w", pady=5)
        self.cb_sub.bind("<<ComboboxSelected>>", self.update_preview)

        # 日期
        tk.Label(info_frame, text="日期 (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", pady=5)
        entry_date = tk.Entry(info_frame, textvariable=self.date_var, width=43)
        entry_date.grid(row=2, column=1, sticky="w", pady=5)
        self.date_var.trace_add("write", lambda *args: self.update_preview())

        # 描述
        tk.Label(info_frame, text="文件描述 (Description):").grid(row=3, column=0, sticky="w", pady=5)
        entry_desc = tk.Entry(info_frame, textvariable=self.desc_var, width=43)
        entry_desc.grid(row=3, column=1, sticky="w", pady=5)
        entry_desc.bind("<KeyRelease>", self.update_preview)

        # 3. 预览区域
        preview_frame = tk.LabelFrame(self.root, text="3. 预览结果", padx=10, pady=10, bg="#f0f8ff")
        preview_frame.pack(fill="x", padx=10, pady=10)

        lbl_preview_title = tk.Label(preview_frame, text="新文件名:", bg="#f0f8ff", font=("Arial", 10, "bold"))
        lbl_preview_title.pack(anchor="w")

        lbl_preview = tk.Label(preview_frame, textvariable=self.preview_var, bg="#f0f8ff", fg="#0056b3", font=("Arial", 12))
        lbl_preview.pack(pady=5)

        # 4. 执行按钮
        btn_rename = tk.Button(self.root, text="确认重命名 (Rename)", command=self.rename_file, 
                               bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), height=2)
        btn_rename.pack(fill="x", padx=20, pady=10)

        # 底部提示
        tk.Label(self.root, text="提示: 重命名成功后文件将保留在原文件夹", fg="gray").pack()

    def select_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.selected_file_path.set(filename)
            self.update_preview()

    def update_sub_categories(self, event=None):
        main_cat = self.category_main.get()
        if main_cat in self.categories:
            subs = self.categories[main_cat]
            self.cb_sub['values'] = subs
            if subs:
                self.cb_sub.current(0)
            else:
                self.cb_sub.set("")
        self.update_preview()

    def get_jd_code(self):
        # 从 "40.04_iDeCo" 中提取 "40.04"
        full_str = self.category_sub.get()
        if not full_str:
            return ""
        # 简单的提取逻辑：取下划线前的部分
        return full_str.split("_")[0] if "_" in full_str else full_str

    def generate_new_name(self):
        original_file = self.selected_file_path.get()
        if not original_file:
            return None, "请选择文件"
        
        jd_code = self.get_jd_code()
        date_str = self.date_var.get()
        description = self.desc_var.get().strip()
        
        if not jd_code:
            return None, "请选择分类"
        if not description:
            description = "Description" # 占位符

        # 获取原文件扩展名
        ext = os.path.splitext(original_file)[1]
        
        # 拼接: Code_Date_Description.ext
        new_name = f"{jd_code}_{date_str}_{description}{ext}"
        return new_name, ""

    def update_preview(self, event=None):
        new_name, error = self.generate_new_name()
        if error:
            self.preview_var.set(f"等待输入: {error}")
        else:
            self.preview_var.set(new_name)

    def rename_file(self):
        original_path = self.selected_file_path.get()
        new_name, error = self.generate_new_name()
        
        if not original_path or not os.path.exists(original_path):
            messagebox.showerror("错误", "原文件不存在或未选择")
            return

        if not self.category_sub.get():
            messagebox.showwarning("警告", "请选择一个分类 (Category)")
            return

        if not self.desc_var.get():
            messagebox.showwarning("警告", "请输入文件描述")
            return

        dir_path = os.path.dirname(original_path)
        new_full_path = os.path.join(dir_path, new_name)

        try:
            os.rename(original_path, new_full_path)
            messagebox.showinfo("成功", f"文件已重命名为:\n{new_name}")
            # 重置部分选项以便处理下一个文件
            self.selected_file_path.set("")
            self.desc_var.set("")
            self.preview_var.set("请选择下一个文件...")
        except Exception as e:
            messagebox.showerror("错误", f"重命名失败:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = JohnnyDecimalRenamer(root)
    root.mainloop()