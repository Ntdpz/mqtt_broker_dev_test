#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Simple MQTT Broker สำหรับ Docker
=================================

นี่คือ MQTT Broker ที่ปรับแต่งสำหรับ Docker environment
"""

import socket
import threading
import time
import json
import os
from datetime import datetime
from collections import defaultdict
import logging

class MQTTBroker:
    """🏠 MQTT Broker หลักสำหรับ Docker"""
    
    def __init__(self, host='0.0.0.0', port=1883):
        """🔧 เตรียมตัวแปรสำหรับ Broker"""
        self.host = host
        self.port = port
        self.running = False
        
        # 📚 Dictionary สำหรับจัดเก็บข้อมูล
        self.clients = {}              # เก็บข้อมูล client ที่เชื่อมต่อ
        self.subscriptions = defaultdict(set)  # เก็บการ subscribe
        self.retained_messages = {}    # เก็บข้อความที่ retain ไว้
        
        # 📊 สถิติการทำงาน
        self.stats = {
            'total_connections': 0,
            'current_connections': 0,
            'total_messages': 0,
            'start_time': datetime.now(),
            'last_activity': datetime.now()
        }
        
        # 🔧 ตั้งค่า logging
        self.setup_logging()
        
        # 🌐 ตั้งค่า socket
        self.server_socket = None
        
    def setup_logging(self):
        """📝 ตั้งค่าระบบ logging"""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('/app/logs/broker.log', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """🚀 เริ่มต้น MQTT Broker"""
        try:
            print("🚀 เตรียมเริ่ม Simple MQTT Broker")
            print("=" * 50)
            
            # สร้าง socket server
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            
            self.running = True
            self.logger.info("🚀 MQTT Broker เริ่มทำงานแล้ว!")
            self.logger.info(f"📍 รอรับการเชื่อมต่อที่ {self.host}:{self.port}")
            
            # เริ่ม thread สำหรับแสดงสถิติ
            stats_thread = threading.Thread(target=self._show_stats_periodically)
            stats_thread.daemon = True
            stats_thread.start()
            
            # รอรับการเชื่อมต่อ
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self._handle_new_client(client_socket, client_address)
                except Exception as e:
                    if self.running:
                        self.logger.error(f"❌ เกิดข้อผิดพลาดในการรับ connection: {e}")
                        
        except Exception as e:
            self.logger.error(f"💥 ไม่สามารถเริ่ม broker ได้: {e}")
            return False
            
        return True
        
    def _handle_new_client(self, client_socket, client_address):
        """👤 จัดการ client ใหม่"""
        client_id = f"client_{len(self.clients) + 1}_{int(time.time())}"
        
        # เก็บข้อมูล client
        self.clients[client_id] = {
            'socket': client_socket,
            'address': client_address,
            'subscriptions': set(),
            'connected_at': datetime.now(),
            'last_activity': datetime.now()
        }
        
        # อัพเดทสถิติ
        self.stats['total_connections'] += 1
        self.stats['current_connections'] = len(self.clients)
        self.stats['last_activity'] = datetime.now()
        
        self.logger.info(f"✅ Client ใหม่เชื่อมต่อ: {client_id} จาก {client_address}")
        
        # สร้าง thread สำหรับจัดการ client นี้
        client_thread = threading.Thread(
            target=self._handle_client_messages,
            args=(client_id, client_socket)
        )
        client_thread.daemon = True
        client_thread.start()
        
    def _handle_client_messages(self, client_id, client_socket):
        """📨 จัดการข้อความจาก client"""
        buffer = ""
        
        try:
            while self.running and client_id in self.clients:
                # รับข้อมูล
                data = client_socket.recv(1024).decode('utf-8')
                
                if not data:
                    break
                    
                buffer += data
                self.clients[client_id]['last_activity'] = datetime.now()
                
                # ประมวลผลข้อความที่สมบูรณ์
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self._process_message(client_id, line.strip())
                        
        except Exception as e:
            self.logger.error(f"❌ เกิดข้อผิดพลาดกับ client {client_id}: {e}")
        finally:
            self._disconnect_client(client_id)
            
    def _process_message(self, client_id, message_str):
        """⚙️ ประมวลผลข้อความที่ได้รับ"""
        try:
            message = json.loads(message_str)
            msg_type = message.get('type')
            
            if msg_type == 'subscribe':
                self._handle_subscribe(client_id, message)
            elif msg_type == 'unsubscribe':
                self._handle_unsubscribe(client_id, message)
            elif msg_type == 'publish':
                self._handle_publish(client_id, message)
            elif msg_type == 'ping':
                self._handle_ping(client_id, message)
            else:
                self.logger.warning(f"⚠️ ประเภทข้อความไม่รู้จัก: {msg_type}")
                
        except json.JSONDecodeError:
            self.logger.error(f"❌ ข้อความไม่ใช่ JSON ที่ถูกต้อง: {message_str}")
        except Exception as e:
            self.logger.error(f"💥 เกิดข้อผิดพลาดในการประมวลผล: {e}")
            
    def _handle_subscribe(self, client_id, message):
        """📥 จัดการการ subscribe"""
        topic = message.get('topic')
        if not topic:
            return
            
        # เพิ่มการ subscribe
        self.subscriptions[topic].add(client_id)
        self.clients[client_id]['subscriptions'].add(topic)
        
        self.logger.info(f"📥 {client_id} subscribe topic: '{topic}'")
        
        # ส่งข้อความที่ retain ไว้ (ถ้ามี)
        if topic in self.retained_messages:
            self._send_to_client(client_id, self.retained_messages[topic])
            
    def _handle_unsubscribe(self, client_id, message):
        """📤 จัดการการ unsubscribe"""
        topic = message.get('topic')
        if not topic:
            return
            
        # ลบการ subscribe
        self.subscriptions[topic].discard(client_id)
        self.clients[client_id]['subscriptions'].discard(topic)
        
        # ลบ topic ที่ไม่มีคนใช้แล้ว
        if not self.subscriptions[topic]:
            del self.subscriptions[topic]
            
        self.logger.info(f"📤 {client_id} unsubscribe topic: '{topic}'")
        
    def _handle_publish(self, client_id, message):
        """📤 จัดการการ publish"""
        topic = message.get('topic')
        payload = message.get('payload', '')
        retain = message.get('retain', False)
        
        if not topic:
            return
            
        # สร้างข้อความที่จะส่งต่อ
        forward_message = {
            'type': 'message',
            'topic': topic,
            'payload': payload,
            'timestamp': datetime.now().isoformat(),
            'from_client': client_id
        }
        
        # เก็บข้อความ retain (ถ้าต้องการ)
        if retain:
            self.retained_messages[topic] = forward_message
            
        # ส่งข้อความให้ subscriber ทั้งหมด
        sent_count = 0
        for subscriber_id in self.subscriptions.get(topic, set()):
            if subscriber_id != client_id:  # ไม่ส่งกลับไปหาผู้ส่ง
                if self._send_to_client(subscriber_id, forward_message):
                    sent_count += 1
                    
        # อัพเดทสถิติ
        self.stats['total_messages'] += 1
        self.stats['last_activity'] = datetime.now()
        
        self.logger.info(f"📤 {client_id} publish ไปยัง '{topic}': {payload}")
        
    def _handle_ping(self, client_id, message):
        """🏓 จัดการ ping/pong"""
        pong_message = {
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        }
        self._send_to_client(client_id, pong_message)
        
    def _send_to_client(self, client_id, message):
        """📬 ส่งข้อความไปยัง client"""
        if client_id not in self.clients:
            return False
            
        try:
            message_json = json.dumps(message, ensure_ascii=False) + '\n'
            self.clients[client_id]['socket'].send(message_json.encode('utf-8'))
            return True
        except Exception as e:
            self.logger.error(f"❌ ไม่สามารถส่งข้อความถึง {client_id}: {e}")
            self._disconnect_client(client_id)
            return False
            
    def _disconnect_client(self, client_id):
        """🔌 ตัดการเชื่อมต่อ client"""
        if client_id not in self.clients:
            return
            
        try:
            # ปิด socket
            self.clients[client_id]['socket'].close()
        except:
            pass
            
        # ลบการ subscribe ทั้งหมด
        for topic in self.clients[client_id]['subscriptions']:
            self.subscriptions[topic].discard(client_id)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
                
        # ลบ client
        del self.clients[client_id]
        
        # อัพเดทสถิติ
        self.stats['current_connections'] = len(self.clients)
        
        self.logger.info(f"👋 Client {client_id} ตัดการเชื่อมต่อ")
        
    def _show_stats_periodically(self):
        """📊 แสดงสถิติเป็นระยะ"""
        while self.running:
            time.sleep(30)  # แสดงทุก 30 วินาที
            if self.running:
                self._show_stats()
                
    def _show_stats(self):
        """📊 แสดงสถิติปัจจุบัน"""
        uptime = datetime.now() - self.stats['start_time']
        
        self.logger.info("📊 ===== สถิติ MQTT Broker =====")
        self.logger.info(f"🕒 เวลาทำงาน: {uptime}")
        self.logger.info(f"🔗 การเชื่อมต่อทั้งหมด: {self.stats['total_connections']}")
        self.logger.info(f"🟢 การเชื่อมต่อปัจจุบัน: {self.stats['current_connections']}")
        self.logger.info(f"📨 ข้อความทั้งหมด: {self.stats['total_messages']}")
        self.logger.info(f"📥 subscription ทั้งหมด: {sum(len(subs) for subs in self.subscriptions.values())}")
        self.logger.info(f"📂 Topic ที่มีการใช้งาน: {len(self.subscriptions)}")
        self.logger.info(f"💾 ข้อความที่เก็บไว้: {len(self.retained_messages)}")
        self.logger.info("================================")
        
    def stop(self):
        """⏹️ หยุดการทำงานของ broker"""
        self.logger.info("⏹️ กำลังหยุดการทำงาน...")
        self.running = False
        
        # ปิดการเชื่อมต่อทั้งหมด
        for client_id in list(self.clients.keys()):
            self._disconnect_client(client_id)
            
        # ปิด server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        self.logger.info("✅ หยุดการทำงานเรียบร้อย")


def main():
    """🎯 ฟังก์ชันหลักสำหรับเริ่มต้น MQTT Broker"""
    # อ่านค่า config จาก environment variables
    host = os.getenv('BROKER_HOST', '0.0.0.0')
    port = int(os.getenv('BROKER_PORT', '1883'))
    
    # สร้าง broker instance
    broker = MQTTBroker(host=host, port=port)
    
    try:
        # เริ่ม broker
        if not broker.start():
            exit(1)
    except KeyboardInterrupt:
        print("\n👋 ได้รับสัญญาณหยุดการทำงาน")
    except Exception as e:
        print(f"💥 เกิดข้อผิดพลาด: {e}")
    finally:
        broker.stop()

if __name__ == "__main__":
    main()