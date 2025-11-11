#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 ทดสอบระบบ MQTT Docker
========================

Publisher สำหรับทดสอบระบบ MQTT ที่ใช้ Docker
ส่งข้อความไปยัง Broker ในคอนเทนเนอร์
"""

import socket
import json
import time
import random
from datetime import datetime
from colorama import Fore, Style, init

# เปิดใช้งานสีใน Windows
init()

class DockerMQTTTester:
    """🧪 คลาสสำหรับทดสอบ MQTT Docker System"""
    
    def __init__(self, broker_host='localhost', broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = f"docker_tester_{int(time.time())}"
        self.socket = None
        
    def connect(self):
        """เชื่อมต่อกับ Broker"""
        try:
            print(f"🔌 กำลังเชื่อมต่อ {self.broker_host}:{self.broker_port}...")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.broker_host, self.broker_port))
            
            print(f"✅ เชื่อมต่อสำเร็จ! Client ID: {self.client_id}")
            return True
            
        except Exception as e:
            print(f"❌ เชื่อมต่อไม่ได้: {e}")
            return False
            
    def send_message(self, topic, payload):
        """ส่งข้อความ"""
        try:
            message = {
                'type': 'publish',
                'topic': topic,
                'payload': str(payload),
                'timestamp': datetime.now().isoformat(),
                'from_client': self.client_id,
                'qos': 0
            }
            
            message_json = json.dumps(message, ensure_ascii=False) + '\n'
            self.socket.send(message_json.encode('utf-8'))
            
            print(f"📤 ส่งข้อความ: {Fore.CYAN}{topic}{Style.RESET_ALL} = {Fore.YELLOW}{payload}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"❌ ส่งข้อความไม่ได้: {e}")
            return False
            
    def disconnect(self):
        """ตัดการเชื่อมต่อ"""
        if self.socket:
            self.socket.close()
        print("🔌 ตัดการเชื่อมต่อแล้ว")
        
    def run_test_sequence(self):
        """เรียกใช้การทดสอบแบบอัตโนมัติ"""
        if not self.connect():
            return
            
        print(f"\n{Fore.GREEN}🧪 เริ่มการทดสอบระบบ MQTT Docker{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            # ทดสอบ 1: ข้อมูลอุณหภูมิ
            print(f"\n{Fore.BLUE}🌡️ ทดสอบ #1: ข้อมูลอุณหภูมิ{Style.RESET_ALL}")
            for i in range(3):
                temp = round(random.uniform(15, 35), 1)
                self.send_message('sensor/temperature', temp)
                time.sleep(2)
                
            # ทดสอบ 2: ข้อมูลความชื้น
            print(f"\n{Fore.CYAN}💧 ทดสอบ #2: ข้อมูลความชื้น{Style.RESET_ALL}")
            for i in range(3):
                humidity = round(random.uniform(30, 90), 1)
                self.send_message('sensor/humidity', humidity)
                time.sleep(2)
                
            # ทดสอบ 3: ข้อมูลอุปกรณ์ต่างๆ
            print(f"\n{Fore.MAGENTA}📱 ทดสอบ #3: ข้อมูลอุปกรณ์{Style.RESET_ALL}")
            devices = ['bedroom', 'kitchen', 'living_room']
            for device in devices:
                status = random.choice(['online', 'offline', 'maintenance'])
                self.send_message(f'home/{device}/status', status)
                time.sleep(1)
                
            # ทดสอบ 4: ข้อมูล device data
            print(f"\n{Fore.YELLOW}🔧 ทดสอบ #4: Device Data{Style.RESET_ALL}")
            for i in range(2):
                device_id = f"device_{random.randint(1, 5)}"
                data = {
                    'battery': random.randint(10, 100),
                    'signal': random.randint(1, 5),
                    'status': 'active'
                }
                self.send_message(f'device/{device_id}/data', json.dumps(data))
                time.sleep(1)
                
            # ทดสอบ 5: ข้อความทั่วไป
            print(f"\n{Fore.WHITE}📬 ทดสอบ #5: ข้อความทั่วไป{Style.RESET_ALL}")
            messages = [
                "Hello from Docker!",
                "System is running perfectly!",
                "Testing MQTT containerization",
                "Docker Compose is working!"
            ]
            
            for msg in messages:
                self.send_message('test/message', msg)
                time.sleep(1)
                
            print(f"\n{Fore.GREEN}✅ การทดสอบเสร็จสิ้น!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 ตรวจสอบ logs ของ subscriber ด้วยคำสั่ง:{Style.RESET_ALL}")
            print(f"   docker-compose logs mqtt-subscriber --tail=20")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⏹️ หยุดการทดสอบ{Style.RESET_ALL}")
        finally:
            self.disconnect()

def main():
    """ฟังก์ชันหลัก"""
    print(f"{Fore.CYAN}🧪 MQTT Docker System Tester{Style.RESET_ALL}")
    print(f"{'=' * 40}")
    
    # ใช้ localhost เพราะ connect จากนอกคอนเทนเนอร์
    tester = DockerMQTTTester('localhost', 1883)
    
    try:
        choice = input(f"\n{Fore.YELLOW}เลือกการทดสอบ:{Style.RESET_ALL}\n"
                      f"1. ทดสอบอัตโนมัติ (แนะนำ)\n"
                      f"2. ส่งข้อความเดียว\n"
                      f"3. ส่งข้อความหลายข้อความ\n"
                      f"เลือก (1-3): ")
        
        if choice == '1':
            tester.run_test_sequence()
            
        elif choice == '2':
            topic = input("Topic: ")
            payload = input("Payload: ")
            
            if tester.connect():
                tester.send_message(topic, payload)
                time.sleep(1)
                tester.disconnect()
                
        elif choice == '3':
            if tester.connect():
                print(f"{Fore.GREEN}เชื่อมต่อแล้ว! พิมพ์ 'quit' เพื่อออก{Style.RESET_ALL}")
                
                while True:
                    topic = input("Topic (หรือ quit): ")
                    if topic.lower() == 'quit':
                        break
                    payload = input("Payload: ")
                    tester.send_message(topic, payload)
                    
                tester.disconnect()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 ออกจากโปรแกรม{Style.RESET_ALL}")

if __name__ == "__main__":
    main()