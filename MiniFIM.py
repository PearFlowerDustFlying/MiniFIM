import os
import hashlib
import json
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
    except Exception as e:
        return None

def scan_directory(directory):
    """遍历目录，记录所有文件的 Hash，返回一个字典"""
    file_hashes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            file_hash = calculate_hash(filepath)
            if file_hash:
                file_hashes[filepath] = file_hash
    return file_hashes

class FIMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("简易文件完整性监控器 (FIM) - GUI版")
        self.root.geometry("600x450")
        self.root.configure(padx=20, pady=20)

        # --- UI 组件定义 ---
        # 1. 目录选择区
        self.dir_frame = tk.Frame(root)
        self.dir_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(self.dir_frame, text="监控目录: ", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.dir_var = tk.StringVar()
        tk.Entry(self.dir_frame, textvariable=self.dir_var, width=50).pack(side=tk.LEFT, padx=10)
        tk.Button(self.dir_frame, text="📁 浏览...", command=self.browse_dir).pack(side=tk.LEFT)

        # 2. 按钮操作区
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=10)

        tk.Button(self.btn_frame, text="🛡️ 1. 建立基线 (保存当前安全状态)", command=self.do_init, 
                  bg="#d4edda", fg="#155724", font=("Arial", 10, "bold"), padx=10).pack(side=tk.LEFT, padx=15)
        
        tk.Button(self.btn_frame, text="🔍 2. 检查完整性 (找出被篡改文件)", command=self.do_check, 
                  bg="#f8d7da", fg="#721c24", font=("Arial", 10, "bold"), padx=10).pack(side=tk.LEFT, padx=15)

        # 3. 日志输出区
        tk.Label(root, text="运行日志与报告:", anchor="w").pack(fill=tk.X)
        self.log_text = tk.Text(root, height=15, width=70, bg="#f4f4f4", font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def log(self, message):
        """将信息打印到界面上的文本框中"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END) # 自动滚动到最底部

    def browse_dir(self):
        """打开文件夹选择对话框"""
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.dir_var.set(selected_dir)

    def do_init(self):
        """执行建立基线逻辑"""
        directory = self.dir_var.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("错误", "请先选择一个有效的文件夹！")
            return

        self.log(f"[*] 正在为目录建立基线: {directory} ...")
        self.root.update() # 刷新界面防止卡顿
        
        baseline_data = scan_directory(directory)
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(baseline_data, f, indent=4)

        self.log(f"[+] 基线建立完成！共扫描了 {len(baseline_data)} 个文件。")
        self.log(f"[+] 数据已保存至 {DB_FILE}\n")

    def do_check(self):
        """执行检查逻辑"""
        directory = self.dir_var.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("错误", "请先选择一个有效的文件夹！")
            return

        if not os.path.exists(DB_FILE):
            messagebox.showwarning("警告", "找不到基线数据！请先点击左侧按钮【建立基线】。")
            return

        self.log(f"[*] 正在检查完整性，请稍候...")
        self.root.update()

        with open(DB_FILE, 'r', encoding='utf-8') as f:
            baseline_data = json.load(f)

        current_data = scan_directory(directory)

        # 集合运算找出差异
        baseline_files = set(baseline_data.keys())
        current_files = set(current_data.keys())

        added_files = current_files - baseline_files
        deleted_files = baseline_files - current_files
        
        modified_files = []
        common_files = baseline_files.intersection(current_files)
        for file in common_files:
            if baseline_data[file] != current_data[file]:
                modified_files.append(file)

        # 打印报告到界面
        self.log("\n========= 完整性检查报告 =========")
        if not added_files and not deleted_files and not modified_files:
            self.log("[+] ✅ 安全！没有发现任何文件被篡改、新增或删除。")
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
        self.log("==================================\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = FIMApp(root)
    root.mainloop()
