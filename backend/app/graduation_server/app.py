from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)

# -- DB INIT --
def init_db():
    conn = sqlite3.connect("graduation.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS graduates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no INTEGER,
            name TEXT,
            call_time TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def dashboard():
    conn = sqlite3.connect("graduation.db")
    c = conn.cursor()
    c.execute("SELECT order_no, name, call_time, status FROM graduates ORDER BY order_no")
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

        # อัปเดตสถานะ + เวลาล่าสุด
        c.execute("UPDATE graduates SET status = ?, last_update = ? WHERE order_no = ?", (status, now, order_no))
        conn.commit()
        conn.close()

        return jsonify({"message": "Status updated", "order_no": order_no, "status": status}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)
