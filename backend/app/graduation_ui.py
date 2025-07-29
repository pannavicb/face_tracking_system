import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pandas as pd
import sqlite3
import qrcode
from PIL import ImageTk, Image
import os
import platform
import time

try:
    import serial  # type: ignore
except ImportError:
    serial = None

class GraduationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ระบบเรียกชื่อรับปริญญา")
        self.root.geometry("1200x750")
        self.root.resizable(False, False)

        self.students = []
        self.current_index = -1
        self.running = False
        self.selected_id = None
        self.start_time = None
        self.elapsed_seconds = 0
        self.call_interval_ms = 3000  # 3 วินาที

        self.conn = sqlite3.connect("graduation.db")
        self.create_table()
        self.load_students("students.csv")

        self.serial_port = None
        self.init_serial()

        self.create_ui()
        self.update_clock()
        self.update_elapsed_time()

    def init_serial(self):
        if serial is None:
            print("pyserial ไม่ได้ติดตั้ง - ข้ามการเชื่อมต่อ Serial")
            return
        try:
            port_name = "COM3" if platform.system() == "Windows" else "/dev/ttyUSB0"
            self.serial_port = serial.Serial(port_name, 9600, timeout=1)
            print(f"เชื่อมต่อ Serial: {port_name}")
        except Exception as e:
            print(f"Serial port ไม่พร้อมใช้งาน: {e}")
            self.serial_port = None

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
                for s in self.students:
                    c.execute("""
                        INSERT INTO graduates (order_no, student_id, name, status)
                        VALUES (?, ?, ?, ?)
                    """, (s.get("ลำดับ"), s.get("รหัสนักศึกษา", ""), s.get("ชื่อ-สกุล"), "รอเข้ารับ"))
                self.conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"โหลด CSV ไม่สำเร็จ: {e}")

    def create_ui(self):
        # หัวข้อหลัก
        year = datetime.now().year - 1
        tk.Label(self.root, text=f"พิธีพระราชทานปริญญาบัตร ประจำปีการศึกษา {year}",
                 font=("Arial", 28, "bold"), fg="navy").pack(pady=(15, 5))

        # แถบแสดงเวลา และข้อมูลเบื้องต้น
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", pady=5, padx=10)

        self.time_label = tk.Label(top_frame, text="เวลา: --:--:--", font=("Arial", 14))
        self.time_label.pack(side="left", padx=5)

        self.count_label = tk.Label(top_frame, text="เรียกแล้ว: 0 คน", font=("Arial", 14))
        self.count_label.pack(side="left", padx=15)

        self.elapsed_label = tk.Label(top_frame, text="เวลาที่ใช้: 0 วินาที", font=("Arial", 14))
        self.elapsed_label.pack(side="left", padx=15)

        # ปุ่มควบคุมหลัก
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", pady=10, padx=10)

        tk.Button(btn_frame, text="เริ่ม", bg="#4CAF50", fg="white", width=10, command=self.start_scroll).pack(side="left", padx=5)
        tk.Button(btn_frame, text="หยุด", bg="#f44336", fg="white", width=10, command=self.stop_scroll).pack(side="left", padx=5)
        tk.Button(btn_frame, text="รีเซ็ต", bg="#9E9E9E", fg="white", width=10, command=self.reset_status).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Export รายชื่อที่รับแล้ว", bg="#2196F3", fg="white", width=20, command=self.export_completed).pack(side="left", padx=5)
        tk.Button(btn_frame, text="◀ ย้อนกลับ", bg="#FF9800", fg="white", width=10, command=self.undo_last).pack(side="left", padx=15)
        tk.Button(btn_frame, text="▶ เรียกชื่อถัดไป", bg="#3F51B5", fg="white", width=15, font=("Arial", 12, "bold"), command=self.call_next).pack(side="right", padx=10)

        # ตารางแสดงข้อมูลพร้อม scrollbar
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=10)

        cols = ("id", "ลำดับ", "รหัสนักศึกษา", "ชื่อ", "เวลาเรียก", "สถานะ", "อัปเดตล่าสุด", "RFID", "สแกนครั้งที่ 1", "สแกนครั้งที่ 2")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=18)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=110 if col != "ชื่อ" else 200)

        self.tree.bind("<ButtonRelease-1>", self.on_row_select)
        self.tree.bind("<Double-1>", self.on_double_click_start_scroll)

        # แสดง QR Code
        self.qr_label = tk.Label(self.root)
        self.qr_label.pack(pady=10)

        # ปุ่มเปลี่ยนสถานะ
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=5)
        tk.Label(status_frame, text="เปลี่ยนสถานะเป็น:", font=("Arial", 12)).pack(side="left", padx=5)
        for s in ["รอเข้ารับ", "อยู่บนเวที", "รับเรียบร้อย", "ขาดการเข้ารับ"]:
            tk.Button(status_frame, text=s, width=12, command=lambda stat=s: self.update_status(stat)).pack(side="left", padx=5)

        self.update_table()
        self.update_count()

    def update_clock(self):
        now = datetime.now()
        now_str = now.strftime("%d/%m/%Y %H:%M:%S")
        self.time_label.config(text=f"เวลา: {now_str}")
        self.root.after(1000, self.update_clock)

    def update_elapsed_time(self):
        elapsed = self.elapsed_seconds
        if self.running and self.start_time is not None:
            elapsed += time.time() - self.start_time
        self.elapsed_label.config(text=f"เวลาที่ใช้: {int(elapsed)} วินาที")
        self.root.after(1000, self.update_elapsed_time)

    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        c = self.conn.cursor()
        c.execute("""
            SELECT id, order_no, student_id, name, call_time, status,
                   last_update, rfid, scan_time_1, scan_time_2
            FROM graduates ORDER BY order_no
        """)
        for row in c.fetchall():
            self.tree.insert("", "end", values=row)
        self.update_count()

    def update_count(self):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM graduates WHERE status IN ('เรียกแล้ว', 'รับเรียบร้อย')")
        count = c.fetchone()[0]
        self.count_label.config(text=f"เรียกแล้ว: {count} คน")

    def reset_status(self):
        if messagebox.askyesno("ยืนยัน", "คุณแน่ใจหรือไม่ว่าต้องการรีเซ็ตข้อมูลทั้งหมด?"):
            c = self.conn.cursor()
            c.execute("""
                UPDATE graduates SET call_time=NULL, status='รอเข้ารับ', last_update=NULL,
                    rfid=NULL, scan_time_1=NULL, scan_time_2=NULL
            """)
            self.conn.commit()
            self.current_index = -1
            self.elapsed_seconds = 0
            self.start_time = None
            self.running = False
            self.update_table()
            self.qr_label.config(image="")
            self.qr_label.image = None
            messagebox.showinfo("รีเซ็ตสำเร็จ", "ข้อมูลถูกรีเซ็ตเรียบร้อยแล้ว")

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

    def call_next(self):
        if self.current_index + 1 >= len(self.students):
            messagebox.showinfo("เสร็จแล้ว", "เรียกชื่อครบทั้งหมดแล้ว")
            self.running = False
            if self.start_time is not None:
                self.elapsed_seconds += time.time() - self.start_time
                self.start_time = None
            return
        self.current_index += 1
        student = self.students[self.current_index]
        now_str = datetime.now().strftime("%H:%M:%S")
        now_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c = self.conn.cursor()
        c.execute("""
            UPDATE graduates SET call_time=?, status=?, last_update=?
            WHERE order_no=?
        """, (now_str, "เรียกแล้ว", now_full, student.get("ลำดับ")))
        self.conn.commit()

        self.update_table()
        self.generate_qr(student.get("ชื่อ-สกุล"), student.get("ลำดับ"))
        self.send_serial(student.get("ชื่อ-สกุล"))
        self.highlight_current_row()

    def send_serial(self, text):
        if self.serial_port:
            try:
                self.serial_port.write(f"{text}\n".encode())
                print(f"ส่งข้อมูลไป Serial: {text}")
            except Exception as e:
                print("Serial write error:", e)

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
        self.highlight_current_row()

    def on_row_select(self, event):
        selected = self.tree.focus()
        if selected:
            values = self.tree.item(selected, "values")
            if values:
                self.selected_id = values[0]
            else:
                self.selected_id = None
        else:
            self.selected_id = None

    def update_status(self, new_status):
        if self.selected_id is None:
            messagebox.showwarning("กรุณาเลือก", "โปรดเลือกแถวจากตารางก่อน")
            return
        now_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c = self.conn.cursor()
        c.execute("""
            UPDATE graduates SET status=?, last_update=?
            WHERE id=?
        """, (new_status, now_full, self.selected_id))
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

    def on_double_click_start_scroll(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        children = self.tree.get_children()
        try:
            self.current_index = children.index(selected)
        except ValueError:
            self.current_index = 0
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.scroll_rows()
        else:
            self.highlight_current_row()

    def scroll_rows(self):
        if not self.running:
            return
        children = self.tree.get_children()
        if self.current_index >= len(children):
            messagebox.showinfo("สิ้นสุด", "ถึงบรรทัดสุดท้ายแล้ว")
            self.running = False
            if self.start_time is not None:
                self.elapsed_seconds += time.time() - self.start_time
                self.start_time = None
            return
        self.highlight_current_row()
        self.call_next()  # เรียกชื่ออัตโนมัติ
        self.current_index += 1
        self.root.after(self.call_interval_ms, self.scroll_rows)

    def highlight_current_row(self):
        self.tree.selection_remove(self.tree.selection())
        children = self.tree.get_children()
        if 0 <= self.current_index < len(children):
            self.tree.selection_set(children[self.current_index])
            self.tree.focus(children[self.current_index])
            self.tree.see(children[self.current_index])

    def start_scroll(self):
        if not self.students:
            messagebox.showwarning("ไม่มีข้อมูล", "ไม่มีข้อมูลนักศึกษาในระบบ")
            return

        if self.selected_id:
            children = self.tree.get_children()
            found_index = None
            for idx, child in enumerate(children):
                values = self.tree.item(child, "values")
                if values and str(values[0]) == str(self.selected_id):
                    found_index = idx
                    break
            self.current_index = found_index if found_index is not None else 0
        else:
            if self.current_index < 0 or self.current_index >= len(self.tree.get_children()):
                self.current_index = 0

        if not self.running:
            self.start_time = time.time()

        self.running = True
        self.scroll_rows()

    def stop_scroll(self):
        if self.running and self.start_time is not None:
            self.elapsed_seconds += time.time() - self.start_time
            self.start_time = None
        self.running = False

    def move_selection_up(self):
        children = self.tree.get_children()
        if self.current_index > 0:
            self.current_index -= 1
            self.highlight_current_row()

    def move_selection_down(self):
        children = self.tree.get_children()
        if self.current_index + 1 < len(children):
            self.current_index += 1
            self.highlight_current_row()


if __name__ == "__main__":
    root = tk.Tk()
    app = GraduationApp(root)
    root.mainloop()
