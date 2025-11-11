#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT Publisher for Testing

Features:
- Connect to MQTT Broker
- Send test data to various Topics
- Simulate IoT sensors and devices
"""

import json
import random
import threading
import time
import uuid
from datetime import datetime

import paho.mqtt.client as mqtt
import colorama  # type: ignore
from colorama import Fore, Style

# Enable colors in Windows
colorama.init(autoreset=True)


class MQTTTestPublisher:
    """
    MQTT Test Publisher
    """

    def __init__(self, broker_host='localhost', broker_port=1883,
                 client_id=None):
        """
        Initialize variables for Publisher
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"test_publisher_{uuid.uuid4().hex[:8]}"
        
        # MQTT Client
        self.client = mqtt.Client(client_id=self.client_id)
        self.connected = False
        
        # Statistics
        self.messages_sent = 0

    def connect(self):
        """
        Connect to MQTT Broker
        """
        try:
            print(f"{Fore.CYAN}Connecting to "
                  f"{self.broker_host}:{self.broker_port}{Style.RESET_ALL}")
            
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            self.connected = True
            
            print(f"{Fore.GREEN}Connected successfully! "
                  f"Client ID: {self.client_id}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}Connection failed: {e}{Style.RESET_ALL}")
            return False

    def publish_message(self, topic, payload, qos=0):
        """
        Send message
        """
        if not self.connected:
            print(f"{Fore.RED}Not connected to Broker{Style.RESET_ALL}")
            return False
        
        try:
            # Convert to JSON if payload is dict
            if isinstance(payload, dict):
                payload = json.dumps(payload, ensure_ascii=False, indent=2)
            
            # Send message
            result = self.client.publish(topic, payload, qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.messages_sent += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Published | "
                      f"{Fore.CYAN}{topic}{Style.RESET_ALL} | "
                      f"{Fore.YELLOW}{payload}{Style.RESET_ALL}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"{Fore.RED}Failed to send message: {e}{Style.RESET_ALL}")
            return False

    def disconnect(self):
        """
        Disconnect
        """
        if self.connected:
            self.client.loop_stop()
            try:
                self.client.disconnect()
            except Exception:
                pass
            self.connected = False
        
        print(f"{Fore.GREEN}Disconnected successfully{Style.RESET_ALL}")


def simulate_temperature_sensor(publisher: MQTTTestPublisher):
    """
    Temperature sensor simulation
    """
    print(f"{Fore.BLUE}Temperature sensor started{Style.RESET_ALL}")
    
    for _ in range(10):
        # Random temperature
        temp = round(random.uniform(20.0, 35.0), 1)
        
        payload = {
            'temperature': temp,
            'unit': 'C',
            'timestamp': datetime.now().isoformat()
        }
        
        publisher.publish_message('sensor/temperature', payload)
        time.sleep(2)


def simulate_humidity_sensor(publisher: MQTTTestPublisher):
    """
    Humidity sensor simulation
    """
    print(f"{Fore.BLUE}Humidity sensor started{Style.RESET_ALL}")
    
    for _ in range(10):
        # Random humidity
        humidity = round(random.uniform(30.0, 80.0), 1)
        
        payload = {
            'humidity': humidity,
            'unit': '%',
            'timestamp': datetime.now().isoformat()
        }
        
        publisher.publish_message('sensor/humidity', payload)
        time.sleep(3)


def simulate_device_status(publisher: MQTTTestPublisher):
    """
    Home device status simulation
    """
    devices = [
        ('device/fan/status', ['on', 'off', 'speed:1', 'speed:2', 'speed:3']),
        ('device/light/status', ['on', 'off', 'dimmed']),
        ('device/light/data', ['brightness:50', 'brightness:80', 
                               'brightness:100', 'off'])
    ]
    
    print(f"{Fore.BLUE}Device simulation started{Style.RESET_ALL}")
    
    for _ in range(15):
        # Random device and status
        topic, statuses = random.choice(devices)
        status = random.choice(statuses)
        
        payload = {
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        publisher.publish_message(topic, payload)
        time.sleep(1.5)


def send_test_messages(publisher: MQTTTestPublisher):
    """
    Send general test messages
    """
    test_messages = [
        ('test/message', 'Hello from MQTT Publisher'),
        ('test/number', random.randint(1, 100)),
        ('test/json', {'key': 'value', 'number': 42, 'active': True}),
        ('system/info', {
            'publisher_id': publisher.client_id,
            'timestamp': datetime.now().isoformat(),
            'message_count': publisher.messages_sent
        })
    ]
    
    print(f"{Fore.BLUE}Sending test messages{Style.RESET_ALL}")
    
    for topic, payload in test_messages:
        publisher.publish_message(topic, payload)
        time.sleep(1)


def interactive_mode(publisher: MQTTTestPublisher):
    """
    Interactive message sending mode
    """
    print(f"\n{Fore.YELLOW}Interactive Mode{Style.RESET_ALL}")
    print("Type command: <topic> <message>")
    print("Example: sensor/temp 25.5")
    print("Type 'quit' to exit")
    
    while True:
        try:
            user_input = input(f"\n{Fore.CYAN}> {Style.RESET_ALL}").strip()
            
            if user_input.lower() == 'quit':
                break
            
            if ' ' in user_input:
                topic, message = user_input.split(' ', 1)
                publisher.publish_message(topic, message)
            else:
                print(f"{Fore.RED}Invalid format. "
                      f"Use: <topic> <message>{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            break


def main():
    """
    Main function
    """
    print("MQTT Test Publisher")
    print("=" * 50)
    
    # Create publisher
    publisher = MQTTTestPublisher(
        broker_host='localhost',
        broker_port=1883
    )
    
    try:
        # Connect
        if not publisher.connect():
            return
        
        print(f"\n{Fore.YELLOW}Select test mode:{Style.RESET_ALL}")
        print("1. Automatic sensor data")
        print("2. Send test messages")
        print("3. Interactive mode")
        print("4. Send everything together")
        
        choice = input(f"\n{Fore.CYAN}Choose (1-4): "
                      f"{Style.RESET_ALL}").strip()
        
        if choice == '1':
            print(f"\n{Fore.GREEN}Starting sensor simulation..."
                  f"{Style.RESET_ALL}")
            
            # Start threads for different sensors
            threads = [
                threading.Thread(target=simulate_temperature_sensor,
                               args=(publisher,)),
                threading.Thread(target=simulate_humidity_sensor,
                               args=(publisher,)),
                threading.Thread(target=simulate_device_status,
                               args=(publisher,))
            ]
            
            for thread in threads:
                thread.start()
            
            # Wait for threads to complete
            for thread in threads:
                thread.join()
                
        elif choice == '2':
            print(f"\n{Fore.GREEN}Sending test messages..."
                  f"{Style.RESET_ALL}")
            send_test_messages(publisher)
            
        elif choice == '3':
            interactive_mode(publisher)
            
        elif choice == '4':
            print(f"\n{Fore.GREEN}Sending everything together..."
                  f"{Style.RESET_ALL}")
            
            # Start all threads
            threads = [
                threading.Thread(target=simulate_temperature_sensor,
                               args=(publisher,)),
                threading.Thread(target=simulate_humidity_sensor,
                               args=(publisher,)),
                threading.Thread(target=simulate_device_status,
                               args=(publisher,)),
                threading.Thread(target=send_test_messages,
                               args=(publisher,))
            ]
            
            for thread in threads:
                thread.start()
            
            # Wait for threads to complete
            for thread in threads:
                thread.join()
                
        else:
            print(f"{Fore.RED}Invalid selection{Style.RESET_ALL}")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopping operation...{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error occurred: {e}{Style.RESET_ALL}")
    finally:
        print(f"\n📊 Total messages sent: {publisher.messages_sent}")
        publisher.disconnect()
        print(f"{Fore.GREEN}Thank you for using Test Publisher!"
              f"{Style.RESET_ALL}")


if __name__ == "__main__":
    main()