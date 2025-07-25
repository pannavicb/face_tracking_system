import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pandas as pd
import sqlite3
import qrcode
from PIL import ImageTk, Image
import os
import platform

class GraduationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ระบบเรียกชื่อรับปริญญา")
        self.root.geometry("1150x700")
        self.students = []
        self.current_index = -1
        self.running = False

        self.conn = sqlite3.connect("graduation.db")
        self.create_table()

        self.load_students("students.csv")
        self.create_ui()
        self.update_clock()

        self.calling = False  # สถานะ auto เรียกชื่อ
        self.selected_id = None

    def create_table(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS graduates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no INTEGER,
                name TEXT,
                call_time TEXT,
                status TEXT
            )
        """)
        self.conn.commit()

    def load_students(self, filename):
        try:
            df = pd.read_csv(filename)
            self.students = df.to_dict(orient="records")
        except Exception as e:
            messagebox.showerror("Error", f"โหลด CSV ไม่สำเร็จ: {e}")

    def create_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill="x", pady=5)

        self.time_label = tk.Label(top, text="เวลา: --:--:--", font=("Arial", 16))
        self.time_label.pack(side="left", padx=10)

        tk.Button(top, text="เริ่ม", command=self.start_time).pack(side="left")
        tk.Button(top, text="หยุด", command=self.stop_time).pack(side="left")

        tk.Button(top, text="◀ ย้อนกลับ", bg="orange", command=self.undo_last).pack(side="left", padx=10)
        tk.Button(top, text="▶ เรียกชื่อถัดไป", bg="green", fg="white", font=("Arial", 16, "bold"), command=self.call_next).pack(side="right", padx=10)

        self.tree = ttk.Treeview(self.root, columns=("ลำดับ", "ชื่อ", "เวลา", "สถานะ"), show="headings", height=18)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        for col in ["ลำดับ", "ชื่อ", "เวลา", "สถานะ"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)

        self.tree.bind("<ButtonRelease-1>", self.on_row_select)
        self.tree.bind("<Double-1>", self.on_double_click_and_scroll)  # เพิ่ม bind สำหรับดับเบิลคลิก

        # QR Code Display
        self.qr_label = tk.Label(self.root)
        self.qr_label.pack(pady=5)

        # แก้ไขสถานะ
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=5)
        tk.Label(status_frame, text="เปลี่ยนสถานะเป็น:", font=("Arial", 20)).pack(side="left")
        for s in ["รอเข้ารับ", "อยู่บนเวที", "รับเรียบร้อย", "ขาดการเข้ารับ"]:
            tk.Button(status_frame, text=s, command=lambda stat=s: self.update_status(stat)).pack(side="left", padx=5)

    def update_clock(self):
        if self.running:
            now = datetime.now().strftime("%H:%M:%S")
            self.time_label.config(text=f"เวลา: {now}")
        self.root.after(1000, self.update_clock)

    def start_time(self):
        self.running = True

    def stop_time(self):
        self.running = False

    def on_double_click_and_scroll(self, event):
        selected = self.tree.focus()
        if not selected:
            return

        item_values = self.tree.item(selected)["values"]
        selected_order = item_values[0]  # สมมุติว่า "ลำดับ" คือคอลัมน์แรก

        for i, student in enumerate(self.students):
            if str(student["ลำดับ"]) == str(selected_order):
                self.current_index = i
                break
        else:
            return

        self.scroll_until_end()

    def scroll_until_end(self):
        if self.current_index >= len(self.students):
            messagebox.showinfo("สิ้นสุด", "ถึงบรรทัดสุดท้ายแล้ว")
            return

        self.highlight_current_row()
        self.current_index += 1

        self.root.after(1000, self.scroll_until_end)

    def highlight_current_row(self):
        for item in self.tree.selection():
            self.tree.selection_remove(item)

        items = self.tree.get_children()
        if 0 <= self.current_index < len(items):
            current_item = items[self.current_index]
            self.tree.selection_set(current_item)
            self.tree.focus(current_item)
            self.tree.see(current_item)

    def undo_last(self):
        c = self.conn.cursor()
        c.execute("SELECT id FROM graduates ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if row:
            c.execute("DELETE FROM graduates WHERE id = ?", (row[0],))
            self.conn.commit()
            self.current_index = max(0, self.current_index - 1)
            self.update_table()
            self.qr_label.config(image="")
            self.qr_label.image = None
        else:
            messagebox.showinfo("ไม่มีข้อมูล", "ยังไม่มีการเรียกชื่อ")

    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        c = self.conn.cursor()
        c.execute("SELECT id, order_no, name, call_time, status FROM graduates ORDER BY order_no")
        for row in c.fetchall():
            self.tree.insert("", "end", values=row[1:], iid=row[0])

    def call_next(self):
        if self.current_index + 1 >= len(self.students):
            messagebox.showinfo("เสร็จแล้ว", "เรียกชื่อครบทั้งหมดแล้ว")
            return

        self.current_index += 1
        student = self.students[self.current_index]
        now = datetime.now().strftime("%H:%M:%S")

        c = self.conn.cursor()
        c.execute("INSERT INTO graduates (order_no, name, call_time, status) VALUES (?, ?, ?, ?)",
                  (student["ลำดับ"], student["ชื่อ-สกุล"], now, "เรียกแล้ว"))
        self.conn.commit()
        self.update_table()

        self.generate_qr(student["ชื่อ-สกุล"], student["ลำดับ"])

    def on_row_select(self, event):
        selected = self.tree.focus()
        if selected:
            self.selected_id = selected

    def update_status(self, new_status):
        if self.selected_id is None:
            messagebox.showwarning("กรุณาเลือก", "โปรดเลือกแถวจากตารางก่อน")
            return
        c = self.conn.cursor()
        c.execute("UPDATE graduates SET status = ? WHERE id = ?", (new_status, self.selected_id))
        self.conn.commit()
        self.update_table()

    def generate_qr(self, name, order_no):
        text = f"ลำดับ: {order_no}\nชื่อ: {name}"
        qr = qrcode.make(text)
        qr_path = "qr_current.png"
        qr.save(qr_path)

        img = Image.open(qr_path).resize((200, 200))
        img_tk = ImageTk.PhotoImage(img)
        self.qr_label.config(image=img_tk)
        self.qr_label.image = img_tk

        # พิมพ์ QR (Windows เท่านั้น)
        if platform.system() == "Windows":
            try:
                os.startfile(qr_path, "print")
            except Exception as e:
                print("พิมพ์ไม่สำเร็จ:", e)


if __name__ == "__main__":
    root = tk.Tk()
    app = GraduationApp(root)
    root.mainloop()
