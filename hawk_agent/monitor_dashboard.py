#!/usr/bin/env python3
"""
Real-time monitoring dashboard for AgentCore
"""
import psutil
import time
import os
import json
from datetime import datetime

class AgentMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.token_count = 0
        self.network_start = psutil.net_io_counters()
        
    def get_stats(self):
        """Get current system stats"""
        process = psutil.Process(os.getpid())
        net = psutil.net_io_counters()
        
        return {
            'memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),
            'cpu_percent': round(process.cpu_percent(), 2),
            'network_sent_mb': round((net.bytes_sent - self.network_start.bytes_sent) / 1024 / 1024, 2),
            'network_recv_mb': round((net.bytes_recv - self.network_start.bytes_recv) / 1024 / 1024, 2),
            'uptime_sec': round(time.time() - self.start_time, 2),
            'token_usage': self.token_count
        }
    
    def update_tokens(self, tokens):
        """Update token count"""
        self.token_count += tokens
    
    def display_dashboard(self):
        """Display real-time dashboard"""
        while True:
            os.system('clear')
            stats = self.get_stats()
            
            print("🔍 AgentCore Monitor Dashboard")
            print("=" * 40)
            print(f"⏱️  Uptime: {stats['uptime_sec']}s")
            print(f"🧠 Memory: {stats['memory_mb']} MB")
            print(f"⚡ CPU: {stats['cpu_percent']}%")
            print(f"📤 Network Out: {stats['network_sent_mb']} MB")
            print(f"📥 Network In: {stats['network_recv_mb']} MB")
            print(f"🎯 Tokens Used: {stats['token_usage']}")
            print(f"🕐 Last Update: {datetime.now().strftime('%H:%M:%S')}")
            print("\nPress Ctrl+C to exit")
            
            time.sleep(2)

if __name__ == "__main__":
    monitor = AgentMonitor()
    try:
        monitor.display_dashboard()
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped")