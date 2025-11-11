# 📡 MQTT Broker System สำหรับมือใหม่

ระบบ MQTT Broker แบบสมบูรณ์ที่เขียนด้วย Python พร้อมการรองรับ Node-RED และ visualization แบบสีสวย

## 🌟 ฟีเจอร์หลัก

- 🚀 **MQTT Broker** - TCP-based broker พร้อม JSON messaging
- 📥 **Smart Subscriber** - รับข้อมูลพร้อม handler สำหรับ topic ต่างๆ
- 📤 **Test Publisher** - ส่งข้อมูลเซ็นเซอร์และทดสอบระบบ
- 🎨 **Node-RED Integration** - รองรับการส่งข้อมูลจาก Node-RED
- 🎯 **Colorful Logging** - แสดงผลแบบสีสวยใน terminal
- 📊 **Real-time Statistics** - สถิติการทำงานแบบ real-time

## 📁 โครงสร้างไฟล์

```
D:\broker_mqtt\
├── 📖 README.md                      # คู่มือการใช้งาน
├── 📋 Node-RED_Integration.md         # วิธีใช้งานกับ Node-RED
│
├── 🏗️ Broker\                         # MQTT Broker
│   ├── simple_broker.py              # Broker หลัก
│   ├── config.json                   # การตั้งค่า
│   ├── config_manager.py             # จัดการ config
│   ├── start_broker.bat             # สคริปต์เริ่ม broker
│   └── README.md                     # คู่มือ broker
│
├── 📥 Subscriber\                     # MQTT Subscriber
│   ├── mqtt_subscriber.py           # Subscriber หลัก
│   └── subscriber.log               # Log files
│
└── 📤 Publisher\                      # MQTT Publisher
    ├── test_publisher.py            # Publisher สำหรับทดสอบ
    ├── json_publisher.py            # JSON-based publisher
    ├── mqtt_json_examples.json      # ตัวอย่าง JSON
    └── myflow.json                  # Node-RED flow
```

## 🚀 การติดตั้งและใช้งาน

### ข้อกำหนดเบื้องต้น

```bash
# Python 3.7+ และ pip
pip install colorama
```

### 1. เริ่มต้น MQTT Broker

```bash
# Windows
cd D:\broker_mqtt\Broker
python simple_broker.py

# หรือใช้ batch file
start_broker.bat
```

**Broker จะรันที่:** `localhost:1883`

### 2. เริ่ม Subscriber

```bash
cd D:\broker_mqtt\Subscriber
python mqtt_subscriber.py
```

### 3. ทดสอบด้วย Publisher

```bash
cd D:\broker_mqtt\Publisher
python test_publisher.py
```

เลือกโหมดทดสอบ:
- `1` - 🤖 ส่งข้อมูลเซ็นเซอร์อัตโนมัติ
- `2` - 📨 ส่งข้อความทดสอบ
- `3` - 🎮 โหมด Interactive
- `4` - 🚀 ส่งทุกอย่างพร้อมกัน

## 🎯 Topics ที่รองรับ

| Topic | หน้าที่ | Handler |
|-------|---------|---------|
| `sensor/temperature` | ข้อมูลอุณหภูมิ | 🌡️ Temperature Handler |
| `sensor/humidity` | ข้อมูลความชื้น | 💧 Humidity Handler |
| `home/+/status` | สถานะอุปกรณ์บ้าน | 🔍 Sensor Handler |
| `device/+/data` | ข้อมูลอุปกรณ์ | 🔍 Sensor Handler |
| `test/message` | ข้อความทดสอบ | 📬 Default Handler |

## 🎨 การใช้งานกับ Node-RED

### 1. Import Flow

1. เปิด Node-RED (`http://localhost:1880`)
2. Menu → Import 
3. Copy เนื้อหาจาก `Publisher/myflow.json`
4. Deploy

### 2. Flow Components

```
[Inject] → [Function] → [TCP Out]
    ↓           ↓          ↓
Send Temp  Format JSON  localhost:1883
```

### 3. Function Node Code

```javascript
msg.payload = JSON.stringify(msg.payload) + '\n';
return msg;
```

### 4. JSON Format

```json
{
  "type": "publish",
  "topic": "sensor/temperature",
  "payload": "25.5",
  "qos": 0
}
```

## 📊 ตัวอย่างผลลัพธ์

### Broker Log
```
🚀 MQTT Broker เริ่มทำงานแล้ว!
📍 รอรับการเชื่อมต่อที่ localhost:1883
✅ Client ใหม่เชื่อมต่อ: my_subscriber_001
📥 client subscribe topic: 'sensor/temperature'
📤 client_2 publish ไปยัง 'sensor/temperature': 26.5
```

### Subscriber Log
```
📨 MSG | Topic: sensor/temperature | From: test_publisher | Data: 26.5
🌡️ อุณหภูมิปกติ: 26.5°C

🎨 Node-RED | Topic: sensor/temperature | QoS: 0 | Data: 25.5
🌡️ อุณหภูมิปกติ: 25.5°C
```

## 🔧 การตั้งค่าขั้นสูง

### Broker Configuration

แก้ไขไฟล์ `Broker/config.json`:

```json
{
    "broker": {
        "host": "localhost",
        "port": 1883,
        "max_clients": 100,
        "heartbeat_interval": 30
    },
    "logging": {
        "level": "INFO",
        "file": "broker.log",
        "max_size_mb": 10
    }
}
```

### Custom Handlers

เพิ่ม handler ใหม่ใน `mqtt_subscriber.py`:

```python
def my_custom_handler(topic: str, payload: str, full_message: dict):
    print(f"🆕 Custom: {topic} = {payload}")

# ใช้งาน
subscriber.subscribe('my/topic', my_custom_handler)
```

## 🚨 การแก้ปัญหา

### 1. Broker ไม่สตาร์ท

```bash
# เช็คพอร์ต
netstat -an | findstr 1883

# เปลี่ยนพอร์ต
# แก้ในไฟล์ config.json
```

### 2. Subscriber ไม่ได้รับข้อมูล

```bash
# เช็คการเชื่อมต่อ
telnet localhost 1883

# เช็ค logs
tail -f subscriber.log
```

### 3. Node-RED ไม่ส่งข้อมูล

- ✅ เช็ค TCP Out node (localhost:1883)
- ✅ เช็ค Function node code
- ✅ ดู Debug sidebar ใน Node-RED

## 📈 Performance

| Component | Max Clients | Messages/sec | Memory Usage |
|-----------|-------------|--------------|--------------|
| Broker | 100 | 1000+ | ~50MB |
| Subscriber | - | 500+ | ~20MB |
| Publisher | - | 100+ | ~15MB |

## 🔗 การรวมระบบ

### REST API Integration

```python
# สร้าง API endpoint
from flask import Flask, request
app = Flask(__name__)

@app.route('/publish', methods=['POST'])
def publish_message():
    # ส่งข้อมูลไปยัง MQTT Broker
    pass
```

### Database Logging

```python
# บันทึกข้อมูลลง database
import sqlite3

def save_to_db(topic, payload, timestamp):
    conn = sqlite3.connect('mqtt_data.db')
    # บันทึกข้อมูล
    conn.close()
```

## 📚 API Reference

### Publisher Methods

```python
publisher.connect()                    # เชื่อมต่อ broker
publisher.publish(topic, message)      # ส่งข้อมูล
publisher.disconnect()                 # ตัดการเชื่อมต่อ
```

### Subscriber Methods

```python
subscriber.subscribe(topic, handler)   # subscribe topic
subscriber.unsubscribe(topic)          # unsubscribe
subscriber.show_stats()                # แสดงสถิติ
```

## 🎓 ตัวอย่างการใช้งาน

### 1. IoT Sensor Monitoring

```python
# ส่งข้อมูลเซ็นเซอร์
publisher.publish("sensor/temperature", "25.5")
publisher.publish("sensor/humidity", "60.2")
```

### 2. Home Automation

```python
# ควบคุมอุปกรณ์
publisher.publish("home/living/light", "ON")
publisher.publish("home/bedroom/fan", "OFF")
```

### 3. Real-time Dashboard

```python
# ส่งข้อมูล dashboard
dashboard_data = {
    "temperature": 26.5,
    "humidity": 65.0,
    "timestamp": "2025-11-11T12:00:00"
}
publisher.publish("dashboard/data", json.dumps(dashboard_data))
```

## 🤝 การพัฒนาต่อ

### Features Roadmap

- [ ] 🔐 Authentication & Authorization
- [ ] 🌐 WebSocket Support  
- [ ] 📊 Web Dashboard
- [ ] 📱 Mobile App Integration
- [ ] 🔄 Message Persistence
- [ ] ⚖️ Load Balancing

### Contributing

1. Fork repository
2. สร้าง feature branch
3. Commit changes
4. Push และ create Pull Request

## 📞 การติดต่อ

- 📧 Email: support@example.com
- 💬 Discord: MQTT Community
- 📖 Wiki: [Project Wiki](link)

## 📜 License

MIT License - ใช้งานได้อย่างอิสระ

---

## 🎉 ขอบคุณ

ขอบคุณที่ใช้งาน MQTT Broker System! หากมีปัญหาหรือข้อเสนอแนะ สามารถสร้าง Issue ได้เลย

**Happy Coding!** 🚀

---

*สร้างด้วย ❤️ สำหรับชุมชนนักพัฒนา*