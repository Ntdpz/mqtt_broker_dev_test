#!/bin/bash

# 🐳 สคริปต์เริ่มต้น Docker Compose สำหรับ MQTT Broker

echo "🚀 เริ่มต้น MQTT Broker Docker Setup"
echo "=================================="

# เช็คว่ามี .env file หรือไม่
if [ ! -f .env ]; then
    echo "📄 สร้างไฟล์ .env จาก .env.example"
    cp .env.example .env
fi

echo "🔄 Building Docker images..."
docker-compose build

echo "🚀 เริ่มต้นบริการ..."
docker-compose up -d

echo "📊 เช็คสถานะบริการ..."
docker-compose ps

echo ""
echo "✅ MQTT Broker พร้อมใช้งานแล้ว!"
echo "📍 Broker: localhost:1883"
echo "📋 ดูลอก: docker-compose logs -f"
echo "⏹️ หยุดบริการ: docker-compose down"