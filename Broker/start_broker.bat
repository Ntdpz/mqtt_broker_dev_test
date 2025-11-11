@echo off
echo ========================================
echo 🚀 เริ่มต้น Simple MQTT Broker
echo ========================================
echo.

REM ตรวจสอบว่ามี Python หรือไม่
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ไม่พบ Python! กรุณาติดตั้ง Python ก่อน
    echo 📥 ดาวน์โหลดได้ที่: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ พบ Python แล้ว
python --version

echo.
echo 🔍 ตรวจสอบไฟล์ที่จำเป็น...

if not exist "simple_broker.py" (
    echo ❌ ไม่พบไฟล์ simple_broker.py
    pause
    exit /b 1
)

if not exist "config.json" (
    echo ⚠️ ไม่พบไฟล์ config.json จะใช้ค่า default
)

echo ✅ ไฟล์พร้อมใช้งาน

echo.
echo 📋 ข้อมูล Broker:
echo 🌐 Host: localhost
echo 🚪 Port: 1883
echo 📝 Log File: broker.log

echo.
echo 🎯 กำลังเริ่มต้น MQTT Broker...
echo 💡 กด Ctrl+C เพื่อหยุดการทำงาน
echo.

REM เริ่มต้น broker
python simple_broker.py

echo.
echo 👋 MQTT Broker หยุดทำงานแล้ว
pause