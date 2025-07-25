import sqlite3
from datetime import datetime, timedelta

def mark_absent(timeout_minutes=5):
    now = datetime.now()
    timeout = now - timedelta(minutes=timeout_minutes)

    conn = sqlite3.connect("graduation.db")
    c = conn.cursor()
    c.execute("SELECT id, last_update FROM graduates WHERE status = 'รอเข้ารับ'")
    rows = c.fetchall()

    for row in rows:
        last = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        if last < timeout:
            print(f"เปลี่ยน ID {row[0]} → ขาดการเข้ารับ")
            c.execute("UPDATE graduates SET status = 'ขาดการเข้ารับ' WHERE id = ?", (row[0],))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    mark_absent()
