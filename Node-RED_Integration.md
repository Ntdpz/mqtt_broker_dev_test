# 🔴 Node-RED Integration กับ MQTT Broker
## คู่มือการใช้งาน Node-RED ส่งข้อมูลมายัง MQTT Broker

### 📋 ข้อมูล Connection
- **Host:** `localhost` หรือ `127.0.0.1`
- **Port:** `1883`
- **Protocol:** `TCP`
- **Format:** `JSON`

---

## 🚀 วิธีติดตั้ง Node-RED

### 1. ติดตั้ง Node.js
```bash
# ดาวน์โหลดจาก https://nodejs.org/
# หรือใช้ chocolatey (Windows)
choco install nodejs
```

### 2. ติดตั้ง Node-RED
```bash
npm install -g node-red
```

### 3. เริ่ม Node-RED
```bash
node-red
```
จากนั้นเปิดเบราว์เซอร์ไปที่: `http://localhost:1880`

---

## 🔧 การตั้งค่า MQTT Node ใน Node-RED

### 1. เพิ่ม MQTT Out Node
- ลาก `mqtt out` node จาก palette มาใส่ใน flow
- Double-click เพื่อตั้งค่า

### 2. ตั้งค่า Server
```
Server: localhost
Port: 1880
```

### 3. ตั้งค่า Topic
ตัวอย่าง Topics:
- `sensor/temperature`
- `sensor/humidity`  
- `home/living_room/status`
- `device/fan/data`
- `test/message`

---

## 📨 รูปแบบข้อความ JSON

### เนื่องจาก Broker ของเราใช้ JSON format แทน MQTT standard:

### ✅ ส่งข้อมูลอุณหภูมิ:
```json
{
  "type": "publish",
  "topic": "sensor/temperature",
  "payload": "25.5",
  "qos": 0
}
```

### ✅ ส่งข้อมูลความชื้น:
```json
{
  "type": "publish", 
  "topic": "sensor/humidity",
  "payload": "65.2",
  "qos": 0
}
```

### ✅ ส่งสถานะอุปกรณ์:
```json
{
  "type": "publish",
  "topic": "home/living_room/status", 
  "payload": "on",
  "qos": 0
}
```

---

## 🎯 ตัวอย่าง Flow ใน Node-RED

### Flow 1: ส่งข้อมูลเซ็นเซอร์
```
[Inject] → [Function] → [TCP Out]
   ↓         ↓           ↓
 Timer    Format JSON  localhost:1883
```

**Function Node Code:**
```javascript
// สำหรับอุณหภูมิ
var temp = (Math.random() * 20 + 15).toFixed(1); // 15-35°C
msg.payload = JSON.stringify({
    "type": "publish",
    "topic": "sensor/temperature", 
    "payload": temp,
    "qos": 0
});
return msg;
```

### Flow 2: ส่งข้อมูลความชื้น
```javascript
// สำหรับความชื้น
var humidity = (Math.random() * 60 + 30).toFixed(1); // 30-90%
msg.payload = JSON.stringify({
    "type": "publish",
    "topic": "sensor/humidity",
    "payload": humidity,
    "qos": 0
});
return msg;
```

### Flow 3: ส่งสถานะอุปกรณ์
```javascript
// สำหรับสถานะอุปกรณ์
var states = ["on", "off", "standby"];
var randomState = states[Math.floor(Math.random() * states.length)];

msg.payload = JSON.stringify({
    "type": "publish",
    "topic": "home/living_room/status",
    "payload": randomState,
    "qos": 0
});
return msg;
```

---

## 🔌 การตั้งค่า TCP Connection

### ใน Node-RED ใช้ `tcp out` node แทน `mqtt out`:

**TCP Out Node Settings:**
- **Type:** Connect to
- **Host:** localhost
- **Port:** 1883
- **Output:** stream of String

**เหตุผล:** เนื่องจาก Broker เราใช้ TCP Socket + JSON แทน MQTT Protocol มาตรฐาน

---

## 🎮 ตัวอย่าง Complete Flow

### Import โค้ดนี้ใน Node-RED:

```json
[
    {
        "id": "temp_inject",
        "type": "inject",
        "name": "Send Temperature",
        "repeat": "5",
        "crontab": "",
        "once": false,
        "onceDelay": 0.1,
        "topic": "",
        "payload": "",
        "payloadType": "date"
    },
    {
        "id": "temp_function", 
        "type": "function",
        "name": "Format Temperature",
        "func": "var temp = (Math.random() * 20 + 15).toFixed(1);\nmsg.payload = JSON.stringify({\n    'type': 'publish',\n    'topic': 'sensor/temperature',\n    'payload': temp,\n    'qos': 0\n}) + '\\n';\nreturn msg;",
        "outputs": 1
    },
    {
        "id": "tcp_out",
        "type": "tcp out",
        "name": "MQTT Broker",
        "host": "localhost",
        "port": "1883",
        "beserver": "client",
        "base64": false,
        "end": false,
        "newline": ""
    }
]
```

---

## 🐛 Troubleshooting

### ปัญหาที่พบบ่อย:

**1. Connection Refused**
```
Error: connect ECONNREFUSED 127.0.0.1:1883
```
**วิธีแก้:** ตรวจสอบว่า MQTT Broker ทำงานอยู่หรือไม่

**2. ข้อมูลไม่ถูกส่ง**
- ตรวจสอบรูปแบบ JSON
- เพิ่ม `\\n` ท้ายข้อความ
- ใช้ `tcp out` แทน `mqtt out`

**3. Subscriber ไม่ได้รับข้อมูล**
- ตรวจสอบ topic ที่ subscribe
- ดูใน log ของ Broker

---

## 📊 การตรวจสอบ

### 1. ใน Node-RED Debug Panel:
เพิ่ม `debug` node เพื่อดูข้อมูลที่ส่ง

### 2. ใน MQTT Broker Log:
```
📤 client_1 publish ไปยัง 'sensor/temperature': 25.5
📥 client_2 subscribe topic: 'sensor/temperature'
```

### 3. ใน MQTT Subscriber:
```
📨 MSG | Topic: sensor/temperature | From: tcp_client_xxx | Data: 25.5
```

---

## 🎯 Best Practices

1. **ใส่ timestamp** ในข้อมูล
2. **ใช้ topic ที่มีความหมาย** เช่น `building/floor/room/device/measurement`
3. **จำกัดขนาดข้อมูล** ไม่เกิน 1KB
4. **ส่งข้อมูลเป็นระยะ** ไม่ถี่เกินไป
5. **จัดการ Error** ในฟังก์ชัน Node-RED

---

**💡 หมายเหตุ:** ถ้าต้องการใช้ MQTT จริง สามารถติดตั้ง Mosquitto Broker และใช้ `mqtt` nodes ปกติได้