from flask import Flask, request, jsonify, render_template
from datetime import datetime
import sqlite3

app = Flask(__name__)

# -- DB INIT --
def init_db():
    conn = sqlite3.connect("graduation.db")
    c = conn.cursor()
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
    conn.commit()
    conn.close()

# -- DB Schema Ensure --
def ensure_columns_exist():
    conn = sqlite3.connect("graduation.db")
    c = conn.cursor()
    fields = [
        ("student_id", "TEXT"),
        ("last_update", "TEXT"),
        ("rfid", "TEXT"),
        ("scan_time_1", "TEXT"),
        ("scan_time_2", "TEXT"),
    ]
    for col, col_type in fields:
        try:
            c.execute(f"ALTER TABLE graduates ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            continue  # Column already exists
    conn.commit()
    conn.close()

@app.route("/")
def dashboard():
    conn = sqlite3.connect("graduation.db")
    c = conn.cursor()
    c.execute("SELECT order_no, student_id, name, call_time, status, last_update FROM graduates ORDER BY order_no")
    rows = c.fetchall()
    conn.close()
    return render_template("dashboard.html", rows=rows)

@app.route("/update_status", methods=["POST"])
def update_status():
    data = request.json
    order_no = data.get("order_no")
    status = data.get("status")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not order_no or not status:
        return jsonify({"error": "Missing fields"}), 400

    try:
        conn = sqlite3.connect("graduation.db")
        c = conn.cursor()
        c.execute("UPDATE graduates SET status = ?, last_update = ? WHERE order_no = ?", (status, now, order_no))
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Status updated",
            "order_no": order_no,
            "status": status,
            "last_update": now
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    ensure_columns_exist()
    app.run(host="0.0.0.0", port=8000, debug=True)
