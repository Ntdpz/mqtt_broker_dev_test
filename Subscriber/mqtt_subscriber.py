#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📥 MQTT Subscriber สำหรับมือใหม่
================================

Subscriber นี้จะ:
- เชื่อมต่อกับ MQTT Broker
- รับข้อมูลจาก Topic ต่างๆ
- แสดงและบันทึก Log ข้อมูลที่ได้รับ
- รองรับการ Subscribe หลาย Topic พร้อมกัน
"""

import socket
import json
import threading
import time
import logging
from datetime import datetime
from typing import List, Dict, Callable
import colorama
from colorama import Fore, Back, Style

# เปิดใช้งานสีใน Windows
colorama.init()

class MQTTSubscriber:
    """
    📥 MQTT Subscriber หลัก
    
    รับผิดชอบการเชื่อมต่อกับ Broker และรับข้อมูล
    """
    
    def __init__(self, broker_host='localhost', broker_port=1883, client_id=None):
        """
        🔧 เตรียมตัวแปรสำหรับ Subscriber
        
        Args:
            broker_host (str): ที่อยู่ของ MQTT Broker
            broker_port (int): พอร์ตของ Broker
            client_id (str): ID ของ Client นี้
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"subscriber_{int(time.time())}"
        
        # การเชื่อมต่อ
        self.socket = None
        self.connected = False
        self.running = False
        
        # การจัดการข้อความ
        self.subscribed_topics = set()
        self.message_handlers = {}
        self.default_handler = None
        
        # สถิติ
        self.stats = {
            'messages_received': 0,
            'connection_time': None,
            'last_message_time': None,
            'topics_count': 0,
            'errors': 0
        }
        
        # Threading
        self.receive_thread = None
        self.heartbeat_thread = None
        
        # ตั้งค่า Logging
        self.setup_logging()
        
    def setup_logging(self):
        """
        📝 ตั้งค่าระบบ Logging แบบสวยงาม
        """
        # สร้าง custom formatter
        class ColorfulFormatter(logging.Formatter):
            """Formatter ที่มีสี"""
            
            COLORS = {
                'DEBUG': Fore.CYAN,
                'INFO': Fore.GREEN,
                'WARNING': Fore.YELLOW,
                'ERROR': Fore.RED,
                'CRITICAL': Fore.RED + Back.WHITE
            }
            
            def format(self, record):
                color = self.COLORS.get(record.levelname, Fore.WHITE)
                
                # จัดรูปแบบข้อความ
                if record.levelname == 'INFO' and 'MSG' in record.getMessage():
                    # ข้อความที่รับมา - ใช้สีพิเศษ
                    formatted = f"{Fore.BLUE}📨 {record.getMessage()}{Style.RESET_ALL}"
                else:
                    # ข้อความทั่วไป
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    formatted = f"{color}[{timestamp}] {record.getMessage()}{Style.RESET_ALL}"
                
                return formatted
        
        # ตั้งค่า console logger
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColorfulFormatter())
        
        # ตั้งค่า file logger (ไม่มีสี)
        file_handler = logging.FileHandler('subscriber.log', encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # ตั้งค่า main logger
        self.logger = logging.getLogger('MQTTSubscriber')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
    def connect(self) -> bool:
        """
        🔌 เชื่อมต่อกับ MQTT Broker
        
        Returns:
            bool: True ถ้าเชื่อมต่อสำเร็จ
        """
        try:
            self.logger.info(f"🔄 กำลังเชื่อมต่อกับ {self.broker_host}:{self.broker_port}")
            
            # สร้าง socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # timeout 10 วินาที
            
            # เชื่อมต่อ
            self.socket.connect((self.broker_host, self.broker_port))
            
            self.connected = True
            self.running = True
            self.stats['connection_time'] = datetime.now()
            
            self.logger.info(f"✅ เชื่อมต่อสำเร็จ! Client ID: {self.client_id}")
            
            # เริ่ม thread สำหรับรับข้อความ
            self.receive_thread = threading.Thread(target=self._receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # เริ่ม heartbeat thread
            self.heartbeat_thread = threading.Thread(target=self._heartbeat)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ไม่สามารถเชื่อมต่อได้: {e}")
            self.stats['errors'] += 1
            return False
            
    def subscribe(self, topic: str, handler: Callable = None):
        """
        📥 Subscribe Topic
        
        Args:
            topic (str): Topic ที่ต้องการ subscribe
            handler (Callable): Function สำหรับจัดการข้อความ (optional)
        """
        if not self.connected:
            self.logger.error("❌ ไม่ได้เชื่อมต่อกับ Broker")
            return False
        
        try:
            # ส่งคำสั่ง subscribe
            message = {
                'type': 'subscribe',
                'topic': topic,
                'client_id': self.client_id
            }
            
            self._send_message(message)
            
            # เพิ่มใน list
            self.subscribed_topics.add(topic)
            if handler:
                self.message_handlers[topic] = handler
            
            self.stats['topics_count'] = len(self.subscribed_topics)
            
            self.logger.info(f"📥 Subscribe topic: '{topic}' เรียบร้อย")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ไม่สามารถ subscribe '{topic}': {e}")
            self.stats['errors'] += 1
            return False
            
    def unsubscribe(self, topic: str):
        """
        📤 Unsubscribe Topic
        
        Args:
            topic (str): Topic ที่ต้องการ unsubscribe
        """
        if not self.connected:
            self.logger.error("❌ ไม่ได้เชื่อมต่อกับ Broker")
            return False
        
        try:
            # ส่งคำสั่ง unsubscribe
            message = {
                'type': 'unsubscribe',
                'topic': topic,
                'client_id': self.client_id
            }
            
            self._send_message(message)
            
            # ลบจาก list
            self.subscribed_topics.discard(topic)
            if topic in self.message_handlers:
                del self.message_handlers[topic]
            
            self.stats['topics_count'] = len(self.subscribed_topics)
            
            self.logger.info(f"📤 Unsubscribe topic: '{topic}' เรียบร้อย")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ไม่สามารถ unsubscribe '{topic}': {e}")
            self.stats['errors'] += 1
            return False
            
    def set_default_handler(self, handler: Callable):
        """
        🎯 ตั้งค่า Handler เริ่มต้นสำหรับข้อความที่ไม่มี Handler เฉพาะ
        
        Args:
            handler (Callable): Function สำหรับจัดการข้อความ
        """
        self.default_handler = handler
        self.logger.info("🎯 ตั้งค่า default handler เรียบร้อย")
        
    def _send_message(self, message: dict):
        """
        📤 ส่งข้อความไปยัง Broker
        
        Args:
            message (dict): ข้อความที่จะส่ง
        """
        message_json = json.dumps(message, ensure_ascii=False) + '\n'
        self.socket.send(message_json.encode('utf-8'))
        
    def _receive_messages(self):
        """
        📨 Thread สำหรับรับข้อความจาก Broker
        """
        buffer = ""
        
        while self.running:
            try:
                # รับข้อมูล
                data = self.socket.recv(1024).decode('utf-8')
                
                if not data:
                    break
                
                buffer += data
                
                # แยกข้อความที่สมบูรณ์
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        print(f"🔍 [DEBUG] Raw message received: {line.strip()}")
                        self._process_received_message(line.strip())
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"❌ เกิดข้อผิดพลาดในการรับข้อความ: {e}")
                    self.stats['errors'] += 1
                break
                
        self._cleanup()
        
    def _process_received_message(self, message_str: str):
        """
        ⚙️ ประมวลผลข้อความที่ได้รับ
        
        Args:
            message_str (str): ข้อความในรูปแบบ JSON string
        """
        try:
            message = json.loads(message_str)
            msg_type = message.get('type')
            print(f"🔍 [DEBUG] Parsed JSON: {message}")
            print(f"🔍 [DEBUG] Message type: {msg_type}")
            
            # จัดการข้อความจาก Node-RED (nested JSON structure)
            if msg_type == 'publish':
                print(f"🎨 [DEBUG] Node-RED message detected!")
                self._handle_node_red_message(message)
            elif msg_type == 'message':
                self._handle_data_message(message)
            elif msg_type == 'pong':
                self._handle_pong(message)
            else:
                self.logger.debug(f"📬 ได้รับข้อความประเภท: {msg_type}")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ ข้อความไม่ใช่ JSON ที่ถูกต้อง: {e}")
            self.stats['errors'] += 1
        except Exception as e:
            self.logger.error(f"💥 เกิดข้อผิดพลาดในการประมวลผลข้อความ: {e}")
            self.stats['errors'] += 1
            
    def _handle_node_red_message(self, message: dict):
        """
        🎨 จัดการข้อความจาก Node-RED (nested JSON structure)
        
        Args:
            message (dict): ข้อความจาก Node-RED
                            รูปแบบ: {"type":"publish","topic":"sensor/temperature","payload":"25.5","qos":0}
        """
        print(f"🎨 [DEBUG] _handle_node_red_message called with: {message}")
        topic = message.get('topic', 'unknown')
        payload = message.get('payload', '')
        qos = message.get('qos', 0)
        from_client = 'Node-RED'  # ระบุว่ามาจาก Node-RED
        print(f"🎨 [DEBUG] Extracted - Topic: {topic}, Payload: {payload}, QoS: {qos}")
        
        # อัพเดทสถิติ
        self.stats['messages_received'] += 1
        self.stats['last_message_time'] = datetime.now()
        
        # สร้างข้อความ log แบบสวยงาม สำหรับ Node-RED
        log_msg = f"🎨 Node-RED | Topic: {Fore.CYAN}{topic}{Style.RESET_ALL} | "
        log_msg += f"QoS: {Fore.GREEN}{qos}{Style.RESET_ALL} | "
        log_msg += f"Data: {Fore.YELLOW}{payload}{Style.RESET_ALL}"
        
        self.logger.info(log_msg)
        
        # เรียก handler ถ้ามี
        if topic in self.message_handlers:
            try:
                # สร้าง message object ให้ handler
                handler_message = {
                    'topic': topic,
                    'payload': payload,
                    'timestamp': datetime.now().isoformat(),
                    'from_client': from_client,
                    'qos': qos,
                    'source': 'node-red'
                }
                self.message_handlers[topic](topic, payload, handler_message)
            except Exception as e:
                self.logger.error(f"❌ Error in handler for '{topic}': {e}")
        elif self.default_handler:
            try:
                # สร้าง message object ให้ default handler
                handler_message = {
                    'topic': topic,
                    'payload': payload,
                    'timestamp': datetime.now().isoformat(),
                    'from_client': from_client,
                    'qos': qos,
                    'source': 'node-red'
                }
                self.default_handler(topic, payload, handler_message)
            except Exception as e:
                self.logger.error(f"❌ Error in default handler: {e}")
    
    def _handle_data_message(self, message: dict):
        """
        📨 จัดการข้อความข้อมูลที่ได้รับ (จาก Python clients)
        
        Args:
            message (dict): ข้อความข้อมูล
        """
        topic = message.get('topic', 'unknown')
        payload = message.get('payload', '')
        timestamp = message.get('timestamp', datetime.now().isoformat())
        from_client = message.get('from_client', 'unknown')
        
        # อัพเดทสถิติ
        self.stats['messages_received'] += 1
        self.stats['last_message_time'] = datetime.now()
        
        # สร้างข้อความ log แบบสวยงาม
        log_msg = f"MSG | Topic: {Fore.CYAN}{topic}{Style.RESET_ALL} | "
        log_msg += f"From: {Fore.MAGENTA}{from_client}{Style.RESET_ALL} | "
        log_msg += f"Data: {Fore.YELLOW}{payload}{Style.RESET_ALL}"
        
        self.logger.info(log_msg)
        
        # เรียก handler ถ้ามี
        if topic in self.message_handlers:
            try:
                self.message_handlers[topic](topic, payload, message)
            except Exception as e:
                self.logger.error(f"❌ Error in handler for '{topic}': {e}")
        elif self.default_handler:
            try:
                self.default_handler(topic, payload, message)
            except Exception as e:
                self.logger.error(f"❌ Error in default handler: {e}")
                
    def _handle_pong(self, message: dict):
        """
        🏓 จัดการข้อความ pong
        """
        self.logger.debug("🏓 Received pong from broker")
        
    def _heartbeat(self):
        """
        💓 ส่ง heartbeat ไปยัง Broker
        """
        while self.running:
            try:
                time.sleep(30)  # ส่งทุก 30 วินาที
                if self.running and self.connected:
                    ping_msg = {'type': 'ping', 'client_id': self.client_id}
                    self._send_message(ping_msg)
                    
            except Exception as e:
                if self.running:
                    self.logger.error(f"❌ Error sending heartbeat: {e}")
                    
    def show_stats(self):
        """
        📊 แสดงสถิติการทำงาน
        """
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"📊 สถิติ MQTT Subscriber")
        print(f"{'='*50}{Style.RESET_ALL}")
        
        uptime = datetime.now() - self.stats['connection_time'] if self.stats['connection_time'] else 0
        
        print(f"🆔 Client ID: {Fore.YELLOW}{self.client_id}{Style.RESET_ALL}")
        print(f"🌐 Broker: {Fore.CYAN}{self.broker_host}:{self.broker_port}{Style.RESET_ALL}")
        print(f"🕒 เชื่อมต่อมาแล้ว: {Fore.GREEN}{uptime}{Style.RESET_ALL}")
        print(f"📨 ข้อความที่ได้รับ: {Fore.MAGENTA}{self.stats['messages_received']}{Style.RESET_ALL}")
        print(f"📂 Topic ที่ Subscribe: {Fore.BLUE}{self.stats['topics_count']}{Style.RESET_ALL}")
        print(f"❌ จำนวน Error: {Fore.RED}{self.stats['errors']}{Style.RESET_ALL}")
        
        if self.subscribed_topics:
            print(f"\n📥 Topics ที่กำลัง Subscribe:")
            for topic in self.subscribed_topics:
                handler_info = "✅ มี Handler" if topic in self.message_handlers else "📋 Default Handler"
                print(f"  • {Fore.CYAN}{topic}{Style.RESET_ALL} ({handler_info})")
                
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")
        
    def disconnect(self):
        """
        🔌 ตัดการเชื่อมต่อ
        """
        self.logger.info("🔄 กำลังตัดการเชื่อมต่อ...")
        self.running = False
        self.connected = False
        
    def _cleanup(self):
        """
        🧹 ทำความสะอาดทรัพยากร
        """
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        self.logger.info("🔌 ตัดการเชื่อมต่อเรียบร้อย")
        
    def wait_for_messages(self):
        """
        ⏰ รอรับข้อความ (Blocking)
        """
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("👋 ได้รับสัญญาณหยุดการทำงาน")
            self.disconnect()


# ========================================
# 🎯 ตัวอย่าง Handler Functions
# ========================================

def temperature_handler(topic: str, payload: str, full_message: dict):
    """
    🌡️ Handler สำหรับข้อมูลอุณหภูมิ
    """
    print(f"🌡️ [DEBUG] Temperature handler called!")
    print(f"🌡️ [DEBUG] Topic: {topic}, Payload: {payload}")
    try:
        temp = float(payload)
        if temp > 30:
            print(f"🔥 {Fore.RED}เตือน: อุณหภูมิสูง {temp}°C!{Style.RESET_ALL}")
        elif temp < 10:
            print(f"🧊 {Fore.BLUE}เตือน: อุณหภูมิต่ำ {temp}°C!{Style.RESET_ALL}")
        else:
            print(f"🌡️ อุณหภูมิปกติ: {temp}°C")
    except:
        print(f"⚠️ ข้อมูลอุณหภูมิไม่ถูกต้อง: {payload}")

def humidity_handler(topic: str, payload: str, full_message: dict):
    """
    💧 Handler สำหรับข้อมูลความชื้น
    """
    try:
        humidity = float(payload)
        if humidity > 80:
            print(f"💧 {Fore.BLUE}ความชื้นสูง: {humidity}%{Style.RESET_ALL}")
        elif humidity < 30:
            print(f"🏜️ {Fore.YELLOW}ความชื้นต่ำ: {humidity}%{Style.RESET_ALL}")
        else:
            print(f"💧 ความชื้นปกติ: {humidity}%")
    except:
        print(f"⚠️ ข้อมูลความชื้นไม่ถูกต้อง: {payload}")

def sensor_handler(topic: str, payload: str, full_message: dict):
    """
    🔍 Handler ทั่วไปสำหรับเซ็นเซอร์
    """
    timestamp = full_message.get('timestamp', 'N/A')
    from_client = full_message.get('from_client', 'Unknown')
    
    print(f"🔍 {Fore.GREEN}Sensor Data{Style.RESET_ALL}")
    print(f"  📍 Topic: {topic}")
    print(f"  📊 Value: {payload}")
    print(f"  ⏰ Time: {timestamp}")
    print(f"  👤 From: {from_client}")

def default_message_handler(topic: str, payload: str, full_message: dict):
    """
    📬 Handler เริ่มต้นสำหรับข้อความทั่วไป
    """
    from_client = full_message.get('from_client', 'Unknown')
    source = full_message.get('source', 'mqtt')
    
    if source == 'node-red':
        print(f"🎨 {Fore.MAGENTA}Node-RED Message{Style.RESET_ALL}")
        print(f"  📂 Topic: {Fore.CYAN}{topic}{Style.RESET_ALL}")
        print(f"  💬 Data: {Fore.YELLOW}{payload}{Style.RESET_ALL}")
        if 'qos' in full_message:
            print(f"  📊 QoS: {Fore.GREEN}{full_message['qos']}{Style.RESET_ALL}")
    else:
        print(f"📬 {Fore.WHITE}General Message{Style.RESET_ALL}")
        print(f"  📂 Topic: {Fore.CYAN}{topic}{Style.RESET_ALL}")
        print(f"  👤 From: {Fore.MAGENTA}{from_client}{Style.RESET_ALL}")
        print(f"  💬 Message: {Fore.YELLOW}{payload}{Style.RESET_ALL}")


# ========================================
# 🚀 ส่วนเริ่มต้นโปรแกรม
# ========================================

def main():
    """
    🎯 ฟังก์ชันหลักสำหรับเริ่มต้น Subscriber
    """
    print(f"{Fore.CYAN}{'='*60}")
    print(f"📥 MQTT Subscriber สำหรับมือใหม่")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    # สร้าง subscriber
    subscriber = MQTTSubscriber(
        broker_host='localhost',
        broker_port=1883,
        client_id='my_subscriber_001'
    )
    
    # ตั้งค่า handlers
    subscriber.set_default_handler(default_message_handler)
    
    try:
        # เชื่อมต่อ
        if not subscriber.connect():
            print("❌ ไม่สามารถเชื่อมต่อได้")
            return
        
        # Subscribe topics ต่างๆ
        print(f"\n{Fore.YELLOW}🔄 กำลังทำการ Subscribe...{Style.RESET_ALL}")
        
        subscriber.subscribe('sensor/temperature', temperature_handler)
        subscriber.subscribe('sensor/humidity', humidity_handler)
        subscriber.subscribe('home/+/status', sensor_handler)  # wildcard
        subscriber.subscribe('device/+/data', sensor_handler)
        subscriber.subscribe('test/message')  # ใช้ default handler
        
        print(f"{Fore.GREEN}✅ พร้อมรับข้อมูล!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 กด Ctrl+C เพื่อหยุดการทำงาน{Style.RESET_ALL}")
        
        # แสดงสถิติเริ่มต้น
        time.sleep(1)
        subscriber.show_stats()
        
        # รอรับข้อความ
        subscriber.wait_for_messages()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 กำลังหยุดการทำงาน...{Style.RESET_ALL}")
    except Exception as e:
        print(f"💥 เกิดข้อผิดพลาด: {e}")
    finally:
        subscriber.show_stats()
        subscriber.disconnect()
        print(f"{Fore.GREEN}👋 ขอบคุณที่ใช้ MQTT Subscriber!{Style.RESET_ALL}")

if __name__ == "__main__":
    main()