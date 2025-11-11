#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎛️ Configuration Manager สำหรับ MQTT Broker
============================================

ไฟล์นี้จัดการการอ่าน config และตั้งค่าต่างๆ
"""

import json
import os
from typing import Dict, Any

class BrokerConfig:
    """
    🔧 คลาสจัดการ Configuration
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        เริ่มต้น Configuration Manager
        
        Args:
            config_file (str): ไฟล์ config
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """
        📖 อ่านไฟล์ config
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"✅ โหลด config จาก {self.config_file} สำเร็จ")
            else:
                print(f"⚠️ ไม่พบไฟล์ {self.config_file} ใช้ค่า default")
                self.create_default_config()
        except Exception as e:
            print(f"❌ ไม่สามารถอ่านไฟล์ config: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """
        🏗️ สร้าง config เริ่มต้น
        """
        self.config = {
            "broker": {
                "host": "localhost",
                "port": 1883,
                "max_connections": 100,
                "keepalive_timeout": 60
            },
            "logging": {
                "level": "INFO",
                "console": True,
                "file": True,
                "filename": "broker.log"
            },
            "performance": {
                "stats_interval": 30,
                "client_timeout": 300
            }
        }
    
    def get(self, section: str, key: str = None, default=None):
        """
        🔍 ดึงค่า config
        
        Args:
            section (str): ส่วนของ config
            key (str): key ที่ต้องการ
            default: ค่า default
        """
        if key is None:
            return self.config.get(section, default)
        
        section_data = self.config.get(section, {})
        return section_data.get(key, default)
    
    def get_broker_host(self) -> str:
        """🌐 ดึง host ของ broker"""
        return self.get("broker", "host", "localhost")
    
    def get_broker_port(self) -> int:
        """🚪 ดึง port ของ broker"""
        return self.get("broker", "port", 1883)
    
    def get_log_level(self) -> str:
        """📝 ดึง log level"""
        return self.get("logging", "level", "INFO")
    
    def get_log_filename(self) -> str:
        """📄 ดึงชื่อไฟล์ log"""
        return self.get("logging", "filename", "broker.log")
    
    def get_stats_interval(self) -> int:
        """📊 ดึงช่วงเวลาแสดงสถิติ"""
        return self.get("performance", "stats_interval", 30)
    
    def is_console_logging_enabled(self) -> bool:
        """🖥️ ตรวจสอบว่าจะแสดง log ใน console ไหม"""
        return self.get("logging", "console", True)
    
    def is_file_logging_enabled(self) -> bool:
        """💾 ตรวจสอบว่าจะเก็บ log ในไฟล์ไหม"""
        return self.get("logging", "file", True)