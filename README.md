# Face Recognition Tracking System

## Features
- Real-time people counting
- Face recognition via webcam
- Telegram alert with image
- Admin dashboard with statistics
- Export data to CSV / PDF

🎓 Smart Graduation Ceremony System
ระบบเรียกชื่อ-ติดตามสถานะนักศึกษาขึ้นรับพระราชทานปริญญาบัตรแบบอัตโนมัติ

🧭 ภาพรวมระบบ (System Overview)
ระบบนี้ถูกออกแบบเพื่อจัดการกระบวนการเรียกชื่อนักศึกษา ขึ้นรับปริญญา แบบอัตโนมัติ โดยใช้ เซนเซอร์, ESP32, Flask API, และ WebSocket Dashboard เพื่อให้เจ้าหน้าที่ควบคุม, ผู้บริหาร และฝ่ายพิธีการสามารถเห็นสถานะของนักศึกษาแบบ Real-Time พร้อมระบบจัดเก็บข้อมูล

🧩 องค์ประกอบของระบบ
ส่วนประกอบ	รายละเอียด
🎓 GUI Desktop (GraduationApp)	เรียกชื่อจาก Excel/CSV + เชื่อมฐานข้อมูล
📡 ESP32 + Sensor	ตรวจจับการเคลื่อนไหวของนักศึกษา (IR/Loadcell/Touch/RFID)
🌐 Flask API	รับข้อมูล POST จาก ESP32 และอัปเดตฐานข้อมูล SQLite
🔄 Flask-SocketIO	ส่งข้อมูลเปลี่ยนสถานะแบบสดๆ ไปยัง Dashboard (WebSocket)
🖥️ Web Dashboard	หน้าเว็บเรียลไทม์ แสดงสถานะนักศึกษาแบบไลฟ์
🗃️ SQLite	ฐานข้อมูล local เก็บลำดับ/ชื่อ/สถานะ/เวลา

🔧 การทำงานของระบบ
เจ้าหน้าที่เปิดระบบ GraduationApp

นักศึกษาถูกเรียกชื่อ → สถานะเริ่มต้น รอเข้ารับ

เมื่อนักศึกษาเดินผ่าน sensor หน้าเวที → ESP32 ส่ง อยู่บนเวที

เมื่อนักศึกษาเดินผ่าน sensor หลังเวที → ESP32 ส่ง รับเรียบร้อย

ถ้านักศึกษาไม่ขึ้นภายในเวลา (5 นาที) → ระบบ mark เป็น ขาดการเข้ารับ

Dashboard แสดงผลสถานะสด ๆ ทันทีด้วย WebSocket

✅ ฟีเจอร์หลัก (Core Features)
ฟีเจอร์	รายละเอียด
📂 อ่านข้อมูลจาก CSV/Excel	ชื่อ-นามสกุล, ลำดับ
🧠 SQLite Database	เก็บข้อมูลลำดับ, ชื่อ, สถานะ, เวลา
🎛️ GUI เรียกชื่อ (Tkinter)	มีปุ่ม "เรียกชื่อถัดไป", highlight อัตโนมัติ
🎨 Real-Time Web Dashboard	แสดงสถานะด้วยสี: เหลือง, ฟ้า, เขียว, แดง
🔄 WebSocket	หน้าเว็บเปลี่ยนทันทีเมื่อมีการอัปเดต
📡 ESP32 ส่ง POST ผ่าน WiFi	ส่งสถานะไปยัง API (offline/local network ได้)
📠 QR Code Generator	สร้าง QR อัตโนมัติเมื่อเรียกชื่อ
🖨️ รองรับการพิมพ์บัตร	พร้อมสร้างปุ่ม “พิมพ์” แบบอัตโนมัติ
🕒 ตรวจจับคนที่ “ขาดการเข้ารับ”	อัตโนมัติถ้าไม่มีการเคลื่อนไหวในเวลา X นาที
🚀 รองรับติดตั้งบน Raspberry Pi	ทำงานแบบ Local / Offline ได้ 100%

🎯 สถานะที่ใช้ในระบบ
สถานะ	ความหมาย	สีที่แสดงใน Dashboard
รอเข้ารับ	ถูกเรียกแล้ว แต่ยังไม่ขึ้นเวที	เหลืองอ่อน
อยู่บนเวที	นักศึกษาอยู่ระหว่างรับปริญญา	ฟ้า
รับเรียบร้อย	รับเสร็จและเดินลงเวทีแล้ว	เขียว
ขาดการเข้ารับ	ไม่ปรากฏตัวภายในเวลาที่กำหนด	แดง

⚙️ เทคโนโลยีที่ใช้
ด้าน	เทคโนโลยี
Hardware	ESP32, IR Sensor, Load Cell, RFID (เลือกได้)
Backend	Python (Flask), SQLite, Flask-SocketIO
Frontend	HTML5 + JavaScript + Socket.IO
Desktop	Python Tkinter GUI
Embedded	Arduino Framework (ESP32)
Deployment	Raspberry Pi / Laptop (Local Network)