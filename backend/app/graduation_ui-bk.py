import tkinter as tk
from tkinter import ttk
from datetime import datetime

class GraduationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("รายชื่อผู้เข้ารับปริญญาบัตร 2069")
        self.root.geometry("1000x600")  # ขนาดเริ่มต้น
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        # --- Sidebar: สถานะ ---
        self.status_frame = tk.Frame(root, padx=10, pady=10)
        self.status_frame.grid(row=0, column=0, rowspan=2, sticky="nsw")
        tk.Label(self.status_frame, text="สถานะ:", font=("Arial", 12, "bold")).pack(anchor="w")
        for status in ["เรียกแล้ว", "รอเรียก", "ขาด"]:
            tk.Label(self.status_frame, text=f"• {status}", font=("Arial", 10)).pack(anchor="w")

        # --- Top Frame ---
        self.top_frame = tk.Frame(root, pady=10)
        self.top_frame.grid(row=0, column=1, sticky="ew")
        self.top_frame.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.time_label = tk.Label(self.top_frame, text="เวลา : 00:00:00", font=("Arial", 12))
        self.time_label.grid(row=0, column=0, padx=5, sticky="w")
        self.running = False
        tk.Button(self.top_frame, text="เริ่ม", command=self.start_time).grid(row=0, column=1, padx=5)
        tk.Button(self.top_frame, text="หยุด", command=self.stop_time).grid(row=0, column=2, padx=5)

        tk.Label(self.top_frame, text="รายชื่อผู้เข้ารับปริญญาบัตร\nสำเร็จการศึกษา ประจำปี 2069", font=("Arial", 14)).grid(row=0, column=3, padx=10, columnspan=1)

        self.date_entry = tk.Entry(self.top_frame)
        self.date_entry.insert(0, "วัน เดือน ปี")
        self.date_entry.grid(row=0, column=4, padx=5, sticky="e")

        self.order_entry = tk.Entry(self.top_frame)
        self.order_entry.insert(0, "ลำดับเข้ารับ")
        self.order_entry.grid(row=0, column=5, padx=5, sticky="e")

        # --- Table Frame ---
        self.table_frame = tk.Frame(root)
        self.table_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.table_frame.columnconfigure(0, weight=1)
        self.table_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(self.table_frame, columns=("ลำดับ", "ชื่อ-สกุล", "เวลา", "สถานะ"), show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)

        for col in ["ลำดับ", "ชื่อ-สกุล", "เวลา", "สถานะ"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=100)

        # --- Footer ---
        self.footer = tk.Frame(root)
        self.footer.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        for label in ["รอเข้ารับ", "อยู่บนเวที", "รับเรียบร้อย", "ขาดการเข้ารับ"]:
            tk.Button(self.footer, text=label, width=15).pack(side="left", padx=5, pady=5)

        self.update_clock()

    def update_clock(self):
        if self.running:
            now = datetime.now().strftime("%H:%M:%S")
            self.time_label.config(text=f"เวลา : {now}")
        self.root.after(1000, self.update_clock)

    def start_time(self):
        self.running = True

    def stop_time(self):
        self.running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = GraduationApp(root)
    root.mainloop()
