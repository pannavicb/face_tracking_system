#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
const char* serverURL = "http://<your-pc-ip>:8000/update_status";  // เช่น http://192.168.1.10:8000

int sensorPin = 4; // ขา GPIO สำหรับเซนเซอร์ (เช่น IR, Touch)
int studentID = 1; // ลำดับของนักศึกษา (จะเปลี่ยนตาม RFID หรือ Trigger)

void setup() {
  Serial.begin(115200);
  pinMode(sensorPin, INPUT);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("WiFi connected");
}

void loop() {
  if (digitalRead(sensorPin) == HIGH) {
    sendStatus(studentID, "อยู่บนเวที");
    delay(3000); // ป้องกันส่งซ้ำ
  }
}

void sendStatus(int order_no, String status) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"order_no\": " + String(order_no) + ", \"status\": \"" + status + "\"}";
    int httpResponseCode = http.POST(payload);

    Serial.println("Sent: " + payload);
    Serial.println("Response code: " + String(httpResponseCode));

    http.end();
  }
}
