#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Simple MQTT Broker สำหรับมือใหม่
=================================

นี่คือ MQTT Broker เบื้องต้นที่สร้างขึ้นด้วย Python
เหมาะสำหรับการเรียนรู้และทดสอบ

ความสามารถ:
- รับ-ส่งข้อความ MQTT
- จัดการ Topic ต่างๆ
- แสดงสถิติการทำงาน
- บันทึกกิจกรรมทั้งหมด
"""

import socket
import threading
import time
import json
from datetime import datetime
from collections import defaultdict
import logging

# ========================================
# 📋 ตั้งค่าพื้นฐาน
# ========================================

class MQTTBroker:
    """
    🏠 MQTT Broker หลัก
    
    คลาสนี้จะทำหน้าที่เป็น:
    - ตัวรับข้อความจาก Publisher
    - ตัวจัดเก็บและจัดการ Topic
    - ตัวส่งข้อความไปยัง Subscriber
    """
    
    def __init__(self, host='localhost', port=1883):
        """
        🔧 เตรียมตัวแปรสำหรับ Broker
        
        Args:
            host (str): ที่อยู่ IP ที่จะรอรับการเชื่อมต่อ
            port (int): พอร์ตที่จะใช้ (1883 เป็นมาตรฐาน MQTT)
        """
        self.host = host
        self.port = port
        self.running = False
        
        # 📚 Dictionary สำหรับจัดเก็บข้อมูล
        self.clients = {}               # เก็บข้อมูล Client ที่เชื่อมต่อ
        self.subscriptions = defaultdict(set)  # เก็บ Topic ที่แต่ละ Client Subscribe
        self.topics = defaultdict(list) # เก็บข้อความล่าสุดของแต่ละ Topic
        
        # 📊 ตัวแปรสำหรับสถิติ
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'total_messages': 0,
            'total_subscriptions': 0,
            'start_time': None
        }
        
        # 🌐 Socket หลักสำหรับรอรับการเชื่อมต่อ
        self.server_socket = None
        
        # 🔒 Lock สำหรับ Thread Safety
        self.lock = threading.Lock()
        
        # ตั้งค่า Logging
        self.setup_logging()
        
    def setup_logging(self):
        """
        📝 ตั้งค่าระบบ Logging
        
        จะสร้างไฟล์ log เพื่อบันทึกกิจกรรมทั้งหมด
        """
        # สร้าง formatter สำหรับจัดรูปแบบ log
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # ตั้งค่า console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # ตั้งค่า file handler
        file_handler = logging.FileHandler('broker.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # ตั้งค่า main logger
        self.logger = logging.getLogger('MQTTBroker')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
    def start(self):
        """
        🚀 เริ่มต้น MQTT Broker
        
        สร้าง socket และเริ่มรอรับการเชื่อมต่อ
        """
        try:
            # สร้าง socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # bind กับ host และ port
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)  # รอรับการเชื่อมต่อได้สูงสุด 5 คิว
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            self.logger.info(f"🚀 MQTT Broker เริ่มทำงานแล้ว!")
            self.logger.info(f"📍 รอรับการเชื่อมต่อที่ {self.host}:{self.port}")
            
            # เริ่ม thread สำหรับแสดงสถิติ
            stats_thread = threading.Thread(target=self.show_stats_periodically)
            stats_thread.daemon = True
            stats_thread.start()
            
            # รอรับการเชื่อมต่อ
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    
                    # สร้างข้อมูล client ใหม่
                    client_id = f"client_{len(self.clients) + 1}_{int(time.time())}"
                    
                    with self.lock:
                        self.clients[client_id] = {
                            'socket': client_socket,
                            'address': client_address,
                            'connected_at': datetime.now(),
                            'subscribed_topics': set(),
                            'last_activity': datetime.now()
                        }
                        self.stats['total_connections'] += 1
                        self.stats['active_connections'] += 1
                    
                    self.logger.info(f"✅ Client ใหม่เชื่อมต่อ: {client_id} จาก {client_address}")
                    
                    # สร้าง thread สำหรับจัดการ client นี้
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_id, client_socket)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        self.logger.error(f"❌ เกิดข้อผิดพลาดในการรอรับการเชื่อมต่อ: {e}")
                    
        except Exception as e:
            self.logger.error(f"💥 เกิดข้อผิดพลาดร้ายแรง: {e}")
        finally:
            self.stop()
            
    def handle_client(self, client_id, client_socket):
        """
        🤝 จัดการ Client แต่ละตัว
        
        Args:
            client_id (str): ID ของ client
            client_socket (socket): socket ของ client
        """
        try:
            while self.running:
                try:
                    # รอรับข้อมูลจาก client (timeout 1 วินาที)
                    client_socket.settimeout(1.0)
                    data = client_socket.recv(1024)
                    
                    if not data:
                        break
                    
                    # อัพเดทเวลาการใช้งานล่าสุด
                    with self.lock:
                        if client_id in self.clients:
                            self.clients[client_id]['last_activity'] = datetime.now()
                    
                    # ประมวลผลข้อมูลที่รับมา
                    self.process_message(client_id, data)
                    
                except socket.timeout:
                    # Timeout ปกติ ไม่ต้องทำอะไร
                    continue
                except socket.error:
                    break
                    
        except Exception as e:
            self.logger.error(f"❌ เกิดข้อผิดพลาดกับ client {client_id}: {e}")
        finally:
            # ปิดการเชื่อมต่อและลบข้อมูล client
            self.disconnect_client(client_id)
            
    def process_message(self, client_id, data):
        """
        📨 ประมวลผลข้อความที่รับมา
        
        ในตัวอย่างนี้เราจะใช้รูปแบบ JSON ง่ายๆ
        แทน MQTT Protocol จริง (เพื่อความเข้าใจง่าย)
        
        Args:
            client_id (str): ID ของ client ที่ส่งมา
            data (bytes): ข้อมูลที่ได้รับ
        """
        try:
            # แปลงข้อมูลเป็น string และ parse JSON
            message_str = data.decode('utf-8').strip()
            message = json.loads(message_str)
            
            # เพิ่มจำนวนข้อความทั้งหมด
            with self.lock:
                self.stats['total_messages'] += 1
            
            # ตรวจสอบประเภทของข้อความ
            msg_type = message.get('type')
            
            if msg_type == 'publish':
                self.handle_publish(client_id, message)
            elif msg_type == 'subscribe':
                self.handle_subscribe(client_id, message)
            elif msg_type == 'unsubscribe':
                self.handle_unsubscribe(client_id, message)
            elif msg_type == 'ping':
                self.handle_ping(client_id)
            else:
                self.logger.warning(f"⚠️ ได้รับข้อความประเภทไม่รู้จาก {client_id}: {msg_type}")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ ข้อมูลจาก {client_id} ไม่ใช่ JSON ที่ถูกต้อง: {e}")
        except Exception as e:
            self.logger.error(f"💥 เกิดข้อผิดพลาดในการประมวลผลข้อความจาก {client_id}: {e}")
            
    def handle_publish(self, client_id, message):
        """
        📤 จัดการข้อความประเภท Publish
        
        Args:
            client_id (str): ID ของ client ที่ส่ง
            message (dict): ข้อความที่ได้รับ
        """
        try:
            topic = message.get('topic')
            payload = message.get('payload')
            
            if not topic:
                self.logger.warning(f"⚠️ {client_id} ส่ง publish แต่ไม่มี topic")
                return
            
            # เก็บข้อความใน topic (เก็บ 10 ข้อความล่าสุด)
            message_data = {
                'payload': payload,
                'client_id': client_id,
                'timestamp': datetime.now().isoformat(),
                'qos': message.get('qos', 0)
            }
            
            with self.lock:
                self.topics[topic].append(message_data)
                # เก็บเฉพาะ 10 ข้อความล่าสุด
                if len(self.topics[topic]) > 10:
                    self.topics[topic] = self.topics[topic][-10:]
            
            self.logger.info(f"📤 {client_id} publish ไปยัง '{topic}': {payload}")
            
            # ส่งข้อความไปยัง subscriber ทั้งหมด
            self.broadcast_to_subscribers(topic, message_data)
            
        except Exception as e:
            self.logger.error(f"💥 เกิดข้อผิดพลาดใน handle_publish: {e}")
            
    def handle_subscribe(self, client_id, message):
        """
        📥 จัดการข้อความประเภท Subscribe
        
        Args:
            client_id (str): ID ของ client
            message (dict): ข้อความที่ได้รับ
        """
        try:
            topic = message.get('topic')
            
            if not topic:
                self.logger.warning(f"⚠️ {client_id} ส่ง subscribe แต่ไม่มี topic")
                return
            
            with self.lock:
                # เพิ่ม topic ให้กับ client
                if client_id in self.clients:
                    self.clients[client_id]['subscribed_topics'].add(topic)
                
                # เพิ่ม client ใน subscription list
                self.subscriptions[topic].add(client_id)
                self.stats['total_subscriptions'] += 1
            
            self.logger.info(f"📥 {client_id} subscribe topic: '{topic}'")
            
            # ส่งข้อความล่าสุดใน topic นี้ให้ client (ถ้ามี)
            if topic in self.topics and self.topics[topic]:
                latest_message = self.topics[topic][-1]
                self.send_to_client(client_id, {
                    'type': 'message',
                    'topic': topic,
                    'payload': latest_message['payload'],
                    'timestamp': latest_message['timestamp']
                })
                
        except Exception as e:
            self.logger.error(f"💥 เกิดข้อผิดพลาดใน handle_subscribe: {e}")
            
    def handle_unsubscribe(self, client_id, message):
        """
        📤 จัดการข้อความประเภท Unsubscribe
        
        Args:
            client_id (str): ID ของ client
            message (dict): ข้อความที่ได้รับ
        """
        try:
            topic = message.get('topic')
            
            if not topic:
                self.logger.warning(f"⚠️ {client_id} ส่ง unsubscribe แต่ไม่มี topic")
                return
            
            with self.lock:
                # ลบ topic จาก client
                if client_id in self.clients:
                    self.clients[client_id]['subscribed_topics'].discard(topic)
                
                # ลบ client จาก subscription list
                self.subscriptions[topic].discard(client_id)
                
                # ถ้าไม่มี subscriber แล้ว ลบ topic ออก
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
            
            self.logger.info(f"📤 {client_id} unsubscribe topic: '{topic}'")
            
        except Exception as e:
            self.logger.error(f"💥 เกิดข้อผิดพลาดใน handle_unsubscribe: {e}")
            
    def handle_ping(self, client_id):
        """
        🏓 ตอบกลับ Ping
        
        Args:
            client_id (str): ID ของ client
        """
        response = {'type': 'pong', 'timestamp': datetime.now().isoformat()}
        self.send_to_client(client_id, response)
        
    def broadcast_to_subscribers(self, topic, message_data):
        """
        📢 ส่งข้อความไปยัง subscriber ทั้งหมดใน topic
        
        Args:
            topic (str): topic ที่จะส่ง
            message_data (dict): ข้อมูลข้อความ
        """
        if topic not in self.subscriptions:
            return
        
        # สร้างข้อความที่จะส่ง
        broadcast_message = {
            'type': 'message',
            'topic': topic,
            'payload': message_data['payload'],
            'timestamp': message_data['timestamp'],
            'from_client': message_data['client_id']
        }
        
        # ส่งให้ subscriber ทั้งหมด
        subscribers = self.subscriptions[topic].copy()  # copy เพื่อ thread safety
        
        for subscriber_id in subscribers:
            if subscriber_id != message_data['client_id']:  # ไม่ส่งกลับให้ผู้ส่ง
                self.send_to_client(subscriber_id, broadcast_message)
                
    def send_to_client(self, client_id, message):
        """
        📨 ส่งข้อความไปยัง client ที่ระบุ
        
        Args:
            client_id (str): ID ของ client
            message (dict): ข้อความที่จะส่ง
        """
        try:
            with self.lock:
                if client_id not in self.clients:
                    return False
                
                client_socket = self.clients[client_id]['socket']
            
            # แปลงข้อความเป็น JSON และส่ง
            message_json = json.dumps(message, ensure_ascii=False) + '\n'
            client_socket.send(message_json.encode('utf-8'))
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ไม่สามารถส่งข้อความไปยัง {client_id}: {e}")
            self.disconnect_client(client_id)
            return False
            
    def disconnect_client(self, client_id):
        """
        🔌 ตัดการเชื่อมต่อ client
        
        Args:
            client_id (str): ID ของ client
        """
        try:
            with self.lock:
                if client_id not in self.clients:
                    return
                
                # ปิด socket
                try:
                    self.clients[client_id]['socket'].close()
                except:
                    pass
                
                # ลบ subscription ทั้งหมดของ client นี้
                subscribed_topics = self.clients[client_id]['subscribed_topics'].copy()
                for topic in subscribed_topics:
                    self.subscriptions[topic].discard(client_id)
                    if not self.subscriptions[topic]:
                        del self.subscriptions[topic]
                
                # ลบข้อมูล client
                del self.clients[client_id]
                self.stats['active_connections'] -= 1
            
            self.logger.info(f"🔌 {client_id} ตัดการเชื่อมต่อแล้ว")
            
        except Exception as e:
            self.logger.error(f"💥 เกิดข้อผิดพลาดในการตัดการเชื่อมต่อ {client_id}: {e}")
            
    def show_stats_periodically(self):
        """
        📊 แสดงสถิติทุกๆ 30 วินาที
        """
        while self.running:
            time.sleep(30)
            if self.running:
                self.show_stats()
                
    def show_stats(self):
        """
        📊 แสดงสถิติปัจจุบัน
        """
        with self.lock:
            stats = self.stats.copy()
            active_topics = len(self.subscriptions)
            total_messages_in_topics = sum(len(messages) for messages in self.topics.values())
        
        uptime = datetime.now() - stats['start_time'] if stats['start_time'] else 0
        
        self.logger.info("📊 ===== สถิติ MQTT Broker =====")
        self.logger.info(f"🕒 เวลาทำงาน: {uptime}")
        self.logger.info(f"🔗 การเชื่อมต่อทั้งหมด: {stats['total_connections']}")
        self.logger.info(f"🟢 การเชื่อมต่อปัจจุบัน: {stats['active_connections']}")
        self.logger.info(f"📨 ข้อความทั้งหมด: {stats['total_messages']}")
        self.logger.info(f"📥 subscription ทั้งหมด: {stats['total_subscriptions']}")
        self.logger.info(f"📂 Topic ที่มีการใช้งาน: {active_topics}")
        self.logger.info(f"💾 ข้อความที่เก็บไว้: {total_messages_in_topics}")
        self.logger.info("================================")
        
    def stop(self):
        """
        🛑 หยุดการทำงานของ Broker
        """
        self.logger.info("🛑 กำลังหยุด MQTT Broker...")
        
        self.running = False
        
        # ปิดการเชื่อมต่อของ client ทั้งหมด
        with self.lock:
            client_ids = list(self.clients.keys())
        
        for client_id in client_ids:
            self.disconnect_client(client_id)
        
        # ปิด server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.logger.info("✅ MQTT Broker หยุดทำงานแล้ว")


# ========================================
# 🏃‍♂️ ส่วนเริ่มต้นโปรแกรม
# ========================================

def main():
    """
    🎯 ฟังก์ชันหลักสำหรับเริ่มต้น Broker
    """
    print("🚀 เตรียมเริ่ม Simple MQTT Broker")
    print("=" * 50)
    
    # สร้าง broker instance
    broker = MQTTBroker(host='localhost', port=1883)
    
    try:
        # เริ่มทำงาน
        broker.start()
    except KeyboardInterrupt:
        print("\n🛑 รับคำสั่งหยุดจาก keyboard...")
    except Exception as e:
        print(f"💥 เกิดข้อผิดพลาด: {e}")
    finally:
        broker.stop()
        print("👋 ขอบคุณที่ใช้ Simple MQTT Broker!")

if __name__ == "__main__":
    main()