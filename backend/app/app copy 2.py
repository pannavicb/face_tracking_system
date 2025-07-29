import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
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
        self.root.geometry("1200x750")
        self.students = []
        self.current_index = -1
        self.running = False
        self.start_time = None
        self.elapsed_seconds = 0.0
        self.selected_id = None

        self.auto_scroll_running = False
        self.auto_scroll_interval = 3000  # ค่าเริ่มต้น 3 วินาที

        self.conn = sqlite3.connect("graduation.db")
        self.create_table()

        self.load_students("students.csv")
        self.create_ui()
        self.update_clock()

    def create_table(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS graduates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no INTEGER NOT NULL,
                student_id TEXT,
                name TEXT NOT NULL,
                call_time TEXT,
                status TEXT DEFAULT 'รอเข้ารับ',
                last_update TEXT,
                rfid TEXT UNIQUE,
                scan_time_1 TEXT,
                scan_time_2 TEXT
            )
        """)
        self.conn.commit()

    def load_students(self, filename):
        try:
            df = pd.read_csv(filename)
            self.students = df.to_dict(orient="records")
            c = self.conn.cursor()
            c.execute("SELECT COUNT(*) FROM graduates")
            count = c.fetchone()[0]
            if count == 0:
                for student in self.students:
                    c.execute("""
                        INSERT INTO graduates (order_no, student_id, name, status)
                        VALUES (?, ?, ?, ?)
                    """, (
                        student.get("ลำดับ"),
                        student.get("รหัสนักศึกษา", ""),
                        student.get("ชื่อ-สกุล"),
                        "รอเข้ารับ"
                    ))
                self.conn.commit()
            self.update_table()
        except Exception as e:
            messagebox.showerror("Error", f"โหลด CSV ไม่สำเร็จ: {e}")

    def create_ui(self):
        year = datetime.now().year - 1
        tk.Label(
            self.root,
            text=f"พิธีพระราชทานปริญญาบัตร ประจำปีการศึกษา {year}",
            font=("Arial", 30, "bold"),
            fg="navy"
        ).pack(pady=(20, 10))

        top = tk.Frame(self.root)
        top.pack(fill="x", pady=5)

        self.time_label = tk.Label(top, text="เวลา: --:--:-- | เวลาที่ใช้ไป: 00:00:00", font=("Arial", 12))
        self.time_label.pack(side="left", padx=10)

        self.count_label = tk.Label(top, text="เรียกแล้ว: 0 คน", font=("Arial", 12))
        self.count_label.pack(side="left", padx=10)

        tk.Button(top, text="เริ่ม", command=self.start_time_count).pack(side="left")
        tk.Button(top, text="หยุด", command=self.stop_time).pack(side="left")
        tk.Button(top, text="รีเซ็ต", bg="red", fg="white", command=self.reset_status).pack(side="left", padx=10)
        tk.Button(top, text="Export รายชื่อที่รับแล้ว", command=self.export_completed).pack(side="left")

        tk.Button(top, text="◀ ย้อนกลับ", bg="orange", command=self.undo_last).pack(side="left", padx=10)
        tk.Button(top, text="▶ นำเข้าชื่อถัดไป", bg="green", fg="white", font=("Arial", 12, "bold"),
                  command=self.call_next).pack(side="right", padx=10)

        # Dropdown เลือกความเร็วการเลื่อนอัตโนมัติ
        speed_label = tk.Label(top, text="ความเร็วเลื่อน (ms):", font=("Arial", 11))
        speed_label.pack(side="right", padx=(20, 5))

        self.speed_var = tk.StringVar(value=str(self.auto_scroll_interval))
        speed_options = ["1000", "1500", "3000"]
        self.speed_dropdown = ttk.Combobox(top, values=speed_options, textvariable=self.speed_var, width=5, state="readonly")
        self.speed_dropdown.pack(side="right")

        # ปุ่มเลื่อนอัตโนมัติ
        self.auto_scroll_btn = tk.Button(top, text="▶ เริ่มเลื่อนอัตโนมัติ", bg="blue", fg="white", font=("Arial", 12, "bold"),
                                         command=self.toggle_auto_scroll)
        self.auto_scroll_btn.pack(side="right", padx=10)

        cols = ("ลำดับ", "รหัสนักศึกษา", "ชื่อ", "เวลาเรียก", "สถานะ", "อัปเดตล่าสุด", "RFID", "สแกนครั้งที่ 1", "สแกนครั้งที่ 2")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", height=20)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)
        self.tree.bind("<ButtonRelease-1>", self.on_row_select)

        self.qr_label = tk.Label(self.root)
        self.qr_label.pack(pady=5)

        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=5)
        tk.Label(status_frame, text="เปลี่ยนสถานะเป็น:", font=("Arial", 11)).pack(side="left")
        for s in ["รอเข้ารับ", "อยู่บนเวที", "รับเรียบร้อย", "ขาดการเข้ารับ"]:
            tk.Button(status_frame, text=s, command=lambda stat=s: self.update_status(stat)).pack(side="left", padx=5)

    def update_clock(self):
        now = datetime.now()
        now_str = now.strftime("%d/%m/%Y %H:%M:%S")

        elapsed_str = "00:00:00"
        if self.start_time:
            elapsed = datetime.now() - self.start_time + timedelta(seconds=self.elapsed_seconds)
            elapsed_str = str(elapsed).split('.')[0]  # ตัด microseconds ออก

        self.time_label.config(text=f"เวลา: {now_str} | เวลาที่ใช้ไป: {elapsed_str}")
        self.update_count()
        self.root.after(1000, self.update_clock)

    def start_time_count(self):
        if not self.running:
            self.running = True
            if self.start_time is None:
                self.start_time = datetime.now()

    def stop_time(self):
        if self.running:
            self.running = False
            if self.start_time:
                delta = datetime.now() - self.start_time
                self.elapsed_seconds += delta.total_seconds()
                self.start_time = None

    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        c = self.conn.cursor()
        c.execute("""
            SELECT order_no, student_id, name, call_time, status,
                   last_update, rfid, scan_time_1, scan_time_2 
            FROM graduates ORDER BY order_no
        """)
        for row in c.fetchall():
            self.tree.insert("", "end", values=row)

    def update_count(self):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM graduates WHERE status IN ('เรียกแล้ว', 'รับเรียบร้อย')")
        count = c.fetchone()[0]
        self.count_label.config(text=f"เรียกแล้ว: {count} คน")

    def reset_status(self):
        if messagebox.askyesno("ยืนยัน", "คุณแน่ใจหรือไม่ว่าต้องการรีเซ็ตข้อมูลทั้งหมด?"):
            self.stop_auto_scroll()
            c = self.conn.cursor()
            c.execute("""
                UPDATE graduates
                SET call_time=NULL, status='รอเข้ารับ', last_update=NULL,
                    scan_time_1=NULL, scan_time_2=NULL
            """)
            self.conn.commit()
            self.current_index = -1
            self.start_time = None
            self.elapsed_seconds = 0.0
            self.running = False
            self.update_table()
            self.qr_label.config(image="")
            self.qr_label.image = None
            messagebox.showinfo("รีเซ็ตสำเร็จ", "ข้อมูลถูกรีเซ็ตเรียบร้อยแล้ว")
            self.selected_id = None
            self.update_count()

    def export_completed(self):
        c = self.conn.cursor()
        c.execute("""
            SELECT order_no, student_id, name, call_time, status,
                   last_update, rfid, scan_time_1, scan_time_2 
            FROM graduates WHERE status = 'รับเรียบร้อย'
        """)
        rows = c.fetchall()
        if not rows:
            messagebox.showinfo("ไม่มีข้อมูล", "ยังไม่มีผู้รับเรียบร้อย")
            return
        df = pd.DataFrame(rows, columns=["ลำดับ", "รหัสนักศึกษา", "ชื่อ", "เวลาเรียก", "สถานะ",
                                         "อัปเดตล่าสุด", "RFID", "สแกนครั้งที่ 1", "สแกนครั้งที่ 2"])
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if file_path:
            df.to_csv(file_path, index=False, encoding="utf-8-sig")
            messagebox.showinfo("ส่งออกสำเร็จ", f"บันทึกไฟล์: {file_path}")

    def call_next(self, print_qr=True):
        if self.current_index + 1 >= len(self.students):
            messagebox.showinfo("เสร็จแล้ว", "เรียกชื่อครบทั้งหมดแล้ว")
            self.stop_auto_scroll()
            self.auto_scroll_btn.config(text="▶ เริ่มเลื่อนอัตโนมัติ", bg="blue")
            return
        self.current_index += 1
        student = self.students[self.current_index]
        now = datetime.now().strftime("%H:%M:%S")
        c = self.conn.cursor()
        c.execute("""
            UPDATE graduates SET call_time=?, status=?, last_update=?
            WHERE order_no=?
        """, (now, "เรียกแล้ว", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), student.get("ลำดับ")))
        self.conn.commit()
        self.update_table()
        self.update_count()
        self.highlight_current_row()
        if print_qr:
            self.generate_qr(student.get("ชื่อ-สกุล"), student.get("ลำดับ"))

    def undo_last(self):
        if self.current_index < 0:
            messagebox.showinfo("ข้อมูลหมด", "ไม่มีข้อมูลที่จะย้อนกลับ")
            return
        student = self.students[self.current_index]
        c = self.conn.cursor()
        c.execute("""
            UPDATE graduates SET call_time=NULL, status='รอเข้ารับ', last_update=NULL
            WHERE order_no=?
        """, (student.get("ลำดับ"),))
        self.conn.commit()
        self.current_index = max(0, self.current_index - 1)
        self.update_table()
        self.qr_label.config(image="")
        self.qr_label.image = None
        self.update_count()
        self.highlight_current_row()

    def on_row_select(self, event):
        selected = self.tree.focus()
        if selected:
            item = self.tree.item(selected)
            values = item.get("values")
            if values:
                order_no = values[0]
                c = self.conn.cursor()
                c.execute("SELECT id FROM graduates WHERE order_no=?", (order_no,))
                row = c.fetchone()
                if row:
                    self.selected_id = row[0]

    def update_status(self, new_status):
        if self.selected_id is None:
            messagebox.showwarning("กรุณาเลือก", "โปรดเลือกแถวจากตารางก่อน")
            return
        c = self.conn.cursor()
        c.execute("UPDATE graduates SET status=?, last_update=? WHERE id=?",
                  (new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.selected_id))
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

        if platform.system() == "Windows":
            try:
                os.startfile(qr_path, "print")
            except Exception as e:
                print("พิมพ์ไม่สำเร็จ:", e)

    def highlight_current_row(self):
        children = self.tree.get_children()
        if 0 <= self.current_index < len(children):
            self.tree.selection_set(children[self.current_index])
            self.tree.focus(children[self.current_index])
            self.tree.see(children[self.current_index])

    def toggle_auto_scroll(self):
        if self.auto_scroll_running:
            self.stop_auto_scroll()
            self.auto_scroll_btn.config(text="▶ เริ่มเลื่อนอัตโนมัติ", bg="blue")
            self.stop_time()  # หยุดนับเวลาเมื่อหยุดเลื่อนอัตโนมัติ
        else:
            try:
                speed = int(self.speed_var.get())
                if speed <= 0:
                    raise ValueError
                self.auto_scroll_interval = speed
            except Exception:
                messagebox.showwarning("ค่าไม่ถูกต้อง", "กรุณาเลือกความเร็วที่ถูกต้อง")
                return

            self.start_auto_scroll()
            self.auto_scroll_btn.config(text="■ หยุดเลื่อนอัตโนมัติ", bg="red")
            self.start_time_count()  # เริ่มนับเวลาต่อเมื่อเริ่มเลื่อนอัตโนมัติ


    def start_auto_scroll(self):
        if not self.auto_scroll_running:
            self.auto_scroll_running = True
            self._auto_scroll()

    def stop_auto_scroll(self):
        self.auto_scroll_running = False

    def _auto_scroll(self):
        if not self.auto_scroll_running:
            return
        if self.current_index + 1 >= len(self.students):
            messagebox.showinfo("เสร็จแล้ว", "เรียกชื่อครบทั้งหมดแล้ว")
            self.stop_auto_scroll()
            self.auto_scroll_btn.config(text="▶ เลื่อนอัตโนมัติ", bg="blue")
            return
        self.call_next(print_qr=False)  # เลื่อนแต่ไม่พิมพ์ QR
        self.root.after(self.auto_scroll_interval, self._auto_scroll)


if __name__ == "__main__":
    root = tk.Tk()
    app = GraduationApp(root)
    root.mainloop()
