import os
import hashlib
import json
import time
import tkinter as tk
from tkinter import filedialog, messagebox

# 数据库文件，用来存放基线 Hash 数据
DB_FILE = "fim_baseline.json"

def calculate_hash(filepath):
    """计算单个文件的 SHA-256 Hash 值"""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def scan_directory(directory, ignore_exts):
    """遍历目录，记录所有文件的 Hash，支持排除特定后缀"""
    file_hashes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            # 【新功能】检查文件后缀是否在忽略列表中
            if any(file.lower().endswith(ext.lower()) for ext in ignore_exts):
                continue
                
            filepath = os.path.join(root, file)
            file_hash = calculate_hash(filepath)
            if file_hash:
                file_hashes[filepath] = file_hash
    return file_hashes

class FIMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MiniFIM - 文件完整性监控器 v2.0")
        self.root.geometry("650x550")
        self.root.configure(padx=20, pady=20)

        # --- 1. 目录与过滤设置区 ---
        setting_frame = tk.LabelFrame(root, text="扫描设置", font=("Arial", 10, "bold"), padx=10, pady=10)
        setting_frame.pack(fill=tk.X, pady=(0, 15))

        # 目录选择
        dir_inner_frame = tk.Frame(setting_frame)
        dir_inner_frame.pack(fill=tk.X, pady=5)
        tk.Label(dir_inner_frame, text="监控目录: ").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar()
        tk.Entry(dir_inner_frame, textvariable=self.dir_var, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(dir_inner_frame, text="📁 浏览", command=self.browse_dir).pack(side=tk.LEFT)

        # 【新功能】忽略后缀设置
        ignore_inner_frame = tk.Frame(setting_frame)
        ignore_inner_frame.pack(fill=tk.X, pady=5)
        tk.Label(ignore_inner_frame, text="忽略后缀: ").pack(side=tk.LEFT)
        self.ignore_var = tk.StringVar(value=".log, .tmp, .cache") # 默认忽略这三种
        tk.Entry(ignore_inner_frame, textvariable=self.ignore_var, width=50).pack(side=tk.LEFT, padx=5)
        tk.Label(ignore_inner_frame, text="(用逗号分隔)", fg="gray").pack(side=tk.LEFT)

        # --- 2. 按钮操作区 ---
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=10)

        tk.Button(self.btn_frame, text="🛡️ 1. 建立基线", command=self.do_init, 
                  bg="#d4edda", fg="#155724", font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT, padx=10)
        
        tk.Button(self.btn_frame, text="🔍 2. 检查完整性", command=self.do_check, 
                  bg="#f8d7da", fg="#721c24", font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT, padx=10)
                  
        # 【新功能】导出报告按钮
        tk.Button(self.btn_frame, text="💾 导出报告", command=self.export_report, 
                  bg="#cce5ff", fg="#004085", font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT, padx=10)

        # --- 3. 日志输出区 ---
        tk.Label(root, text="运行日志与报告:", anchor="w").pack(fill=tk.X)
        self.log_text = tk.Text(root, height=15, width=70, bg="#f4f4f4", font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def log(self, message):
        """将信息打印到界面上的文本框中"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def get_ignore_list(self):
        """解析用户输入的忽略后缀"""
        raw_str = self.ignore_var.get()
        # 将输入字符串按逗号分割，去除空格
        return [ext.strip() for ext in raw_str.split(",") if ext.strip()]

    def browse_dir(self):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.dir_var.set(selected_dir)

    def do_init(self):
        directory = self.dir_var.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("错误", "请先选择一个有效的文件夹！")
            return

        ignore_list = self.get_ignore_list()
        self.log(f"[*] 开始建立基线: {directory} (忽略后缀: {ignore_list})")
        self.root.update()
        
        start_time = time.time() # 记录开始时间
        baseline_data = scan_directory(directory, ignore_list)
        end_time = time.time()   # 记录结束时间
        
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(baseline_data, f, indent=4)

        self.log(f"[+] 基线建立完成！共扫描了 {len(baseline_data)} 个文件。")
        self.log(f"[+] 耗时: {end_time - start_time:.2f} 秒，数据已保存至 {DB_FILE}\n")

    def do_check(self):
        directory = self.dir_var.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("错误", "请先选择一个有效的文件夹！")
            return

        if not os.path.exists(DB_FILE):
            messagebox.showwarning("警告", "找不到基线数据！请先点击【建立基线】。")
            return

        ignore_list = self.get_ignore_list()
        self.log(f"[*] 正在检查完整性...")
        self.root.update()

        with open(DB_FILE, 'r', encoding='utf-8') as f:
            baseline_data = json.load(f)

        start_time = time.time()
        current_data = scan_directory(directory, ignore_list)
        end_time = time.time()

        baseline_files = set(baseline_data.keys())
        current_files = set(current_data.keys())

        added_files = current_files - baseline_files
        deleted_files = baseline_files - current_files
        
        modified_files = []
        common_files = baseline_files.intersection(current_files)
        for file in common_files:
            if baseline_data[file] != current_data[file]:
                modified_files.append(file)

        self.log("\n========= 完整性检查报告 =========")
        if not added_files and not deleted_files and not modified_files:
            self.log("[+] ✅ 安全！没有发现任何文件被篡改。")
        else:
            if added_files:
                self.log(f"\n[!] ⚠️ 发现 {len(added_files)} 个未授权的新增文件:")
                for f in added_files: self.log(f"  + {f}")
            if deleted_files:
                self.log(f"\n[!] ⚠️ 发现 {len(deleted_files)} 个文件被悄悄删除:")
                for f in deleted_files: self.log(f"  - {f}")
            if modified_files:
                self.log(f"\n[!] ❌ 危险！发现 {len(modified_files)} 个被篡改的文件:")
                for f in modified_files: self.log(f"  ~ {f}")
        self.log(f"--- 检查完毕，耗时 {end_time - start_time:.2f} 秒 ---\n")

    def export_report(self):
        """【新功能】将文本框内容导出为 TXT 文件"""
        log_content = self.log_text.get("1.0", tk.END).strip()
        if not log_content:
            messagebox.showinfo("提示", "当前没有可以导出的日志！")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt", 
            filetypes=[("Text Files", "*.txt")],
            title="保存审计报告",
            initialfile="MiniFIM_Audit_Report.txt"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(log_content)
                messagebox.showinfo("成功", f"报告已成功保存至:\n{filepath}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FIMApp(root)
    root.mainloop()
