# 🐳 Dockerfile สำหรับ MQTT Broker
FROM python:3.11-alpine

# 📦 ติดตั้ง dependencies พื้นฐาน
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers

# 👤 สร้าง non-root user สำหรับ security
RUN addgroup -g 1000 mqtt && \
    adduser -D -s /bin/sh -u 1000 -G mqtt mqtt

# 📁 สร้าง working directory
WORKDIR /app

# 📄 Copy requirements และ install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 📋 Copy source code
COPY . .

# 🔧 สร้าง directories สำหรับ logs และ data
RUN mkdir -p /app/logs /app/data && \
    chown -R mqtt:mqtt /app

# 🔐 เปลี่ยนเป็น non-root user
USER mqtt

# 🌐 Expose port
EXPOSE 1883

# 📊 Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost',1883)); s.close()" || exit 1

# 🚀 เริ่มต้น broker
CMD ["python", "simple_broker.py"]