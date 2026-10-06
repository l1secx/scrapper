#!/usr/bin/env python3
"""
Multi-Language Message Bus
Languages communicate through shared message queues
"""

import json
import sys
import time
import threading
from pathlib import Path
from collections import defaultdict
import subprocess


class MessageBus:
    """Shared communication channel between languages"""
    
    def __init__(self):
        self.messages = defaultdict(list)
        self.lock = threading.Lock()
    
    def send(self, sender, receiver, message_type, data):
        """Send a message from one language to another"""
        with self.lock:
            msg = {
                'sender': sender,
                'receiver': receiver,
                'type': message_type,
                'data': data,
                'timestamp': time.time()
            }
            self.messages[receiver].append(msg)
            print(f"📨 {sender} → {receiver}: {message_type}")
    
    def receive(self, receiver):
        """Get messages for a specific language"""
        with self.lock:
            msgs = self.messages[receiver].copy()
            self.messages[receiver].clear()
            return msgs
    
    def broadcast(self, sender, message_type, data):
        """Send message to all languages"""
        for receiver in ['python', 'rust', 'go']:
            if receiver != sender:
                self.send(sender, receiver, message_type, data)


class CollaborativeAgent:
    """Base class for language agents"""
    
    def __init__(self, name, message_bus):
        self.name = name
        self.bus = message_bus
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the agent thread"""
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the agent"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def run(self):
        """Main agent loop"""
        while self.running:
            self.process_messages()
            time.sleep(0.1)
    
    def process_messages(self):
        """Process incoming messages"""
        msgs = self.bus.receive(self.name)
        for msg in msgs:
            self.handle_message(msg)
    
    def handle_message(self, msg):
        """Handle a specific message"""
        msg_type = msg['type']
        sender = msg['sender']
        data = msg['data']
        
        print(f"📩 {self.name} received from {sender}: {msg_type}")
        
        # Default handler
        self.send_response(sender, "ack", {"status": "received"})
    
    def send_response(self, receiver, msg_type, data):
        """Send a response message"""
        self.bus.send(self.name, receiver, msg_type, data)


class PythonAgent(CollaborativeAgent):
    """Python handles orchestration and coordination"""
    
    def __init__(self, message_bus):
        super().__init__('python', message_bus)
        self.rate_limiter = None
        self.proxy_list = []
    
    def handle_message(self, msg):
        """Handle Python-specific messages"""
        if msg['type'] == 'request_url':
            # Rust or Go asking for a URL to process
            url = self.get_next_url()
            self.send_response(msg['sender'], 'url_assignment', {'url': url})
        
        elif msg['type'] == 'report_status':
            # Another language reporting status
            status = msg['data']
            print(f"🐍 Python logs: {msg['sender']} status: {status}")
        
        elif msg['type'] == 'rate_limit_check':
            # Check if rate limit allows request
            allowed = self.check_rate_limit()
            self.send_response(msg['sender'], 'rate_limit_response', {'allowed': allowed})
        
        else:
            super().handle_message(msg)
    
    def get_next_url(self):
        """Get next URL from queue"""
        # In real implementation, this would read from a shared queue
        return "https://example.com/page"
    
    def check_rate_limit(self):
        """Check if rate limit allows request"""
        # In real implementation, this would use token bucket
        return True


class RustAgent(CollaborativeAgent):
    """Rust handles high-speed crawling"""
    
    def __init__(self, message_bus):
        super().__init__('rust', message_bus)
        self.crawl_speed = 0.05  # Simulated speed
    
    def handle_message(self, msg):
        """Handle Rust-specific messages"""
        if msg['type'] == 'url_assignment':
            # Python assigned a URL to crawl
            url = msg['data']['url']
            result = self.crawl_url(url)
            self.broadcast('rust', 'crawl_result', result)
        
        elif msg['type'] == 'extract_links':
            # Extract links from HTML
            html = msg['data']['html']
            links = self.extract_links_fast(html)
            self.send_response(msg['sender'], 'links_extracted', {'links': links})
        
        else:
            super().handle_message(msg)
    
    def crawl_url(self, url):
        """Crawl a URL using Rust's speed"""
        print(f"🦀 Rust crawling: {url}")
        
        # Call actual Rust subprocess
        try:
            rust_path = Path("rust-scraper/target/release/turbo-scraper")
            if rust_path.exists():
                result = subprocess.run(
                    [str(rust_path), url],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {'url': url, 'status': 'success', 'links': []}
        except:
            pass
        
        # Simulate
        time.sleep(self.crawl_speed)
        return {'url': url, 'status': 'success', 'links': []}
    
    def extract_links_fast(self, html):
        """Extract links using Rust's speed"""
        # In real implementation, call Rust for link extraction
        return []


class GoAgent(CollaborativeAgent):
    """Go handles concurrent I/O and downloads"""
    
    def __init__(self, message_bus):
        super().__init__('go', message_bus)
        self.download_speed = 0.03  # Simulated speed
    
    def handle_message(self, msg):
        """Handle Go-specific messages"""
        if msg['type'] == 'url_assignment':
            # Python assigned a URL to download
            url = msg['data']['url']
            result = self.download_file(url)
            self.broadcast('go', 'download_result', result)
        
        elif msg['type'] == 'download_file':
            # Download a specific file
            url = msg['data']['url']
            result = self.download_file(url)
            self.send_response(msg['sender'], 'file_downloaded', result)
        
        else:
            super().handle_message(msg)
    
    def download_file(self, url):
        """Download a file using Go's concurrency"""
        print(f"🐹 Go downloading: {url}")
        
        # Call actual Go subprocess
        try:
            go_path = Path("go-scraper/turbo-scraper")
            if go_path.exists():
                result = subprocess.run(
                    [str(go_path), url],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {'url': url, 'status': 'success'}
        except:
            pass
        
        # Simulate
        time.sleep(self.download_speed)
        return {'url': url, 'status': 'success'}


class CollaborativeSystem:
    """Manages the multi-language collaboration"""
    
    def __init__(self):
        self.bus = MessageBus()
        self.agents = {
            'python': PythonAgent(self.bus),
            'rust': RustAgent(self.bus),
            'go': GoAgent(self.bus)
        }
        self.running = False
    
    def start(self):
        """Start all agents"""
        print("\n" + "="*70)
        print("🤝 Multi-Language Collaboration System")
        print("="*70)
        print("🐍 Python: Orchestration, Rate Limiting, Proxy Management")
        print("🦀 Rust: High-Speed Crawling, Link Extraction")
        print("🐹 Go: Concurrent I/O, File Downloads")
        print("="*70 + "\n")
        
        self.running = True
        for agent in self.agents.values():
            agent.start()
        
        print("✅ All agents started and communicating!\n")
    
    def stop(self):
        """Stop all agents"""
        self.running = False
        for agent in self.agents.values():
            agent.stop()
    
    def run_scenario(self, scenario_name):
        """Run a collaborative scenario"""
        print(f"\n🎬 Running scenario: {scenario_name}")
        print("-" * 70)
        
        if scenario_name == "full_scan":
            self.run_full_scan()
        elif scenario_name == "distributed_crawl":
            self.run_distributed_crawl()
        else:
            print("Unknown scenario")
    
    def run_full_scan(self):
        """Full collaborative scan scenario"""
        # Python orchestrates
        self.agents['python'].bus.send('python', 'rust', 'start_crawl', {'url': 'https://example.com'})
        self.agents['python'].bus.send('python', 'go', 'start_download', {'url': 'https://example.com'})
        
        time.sleep(2)
        
        # Rust reports back
        self.agents['rust'].bus.send('rust', 'python', 'crawl_complete', {'pages': 100})
        
        # Go reports back
        self.agents['go'].bus.send('go', 'python', 'download_complete', {'files': 50})
        
        time.sleep(1)
    
    def run_distributed_crawl(self):
        """Distributed crawl where languages share work"""
        urls = [
            'https://example.com/page1',
            'https://example.com/page2',
            'https://example.com/page3',
            'https://example.com/page4',
            'https://example.com/page5',
        ]
        
        # Python distributes URLs
        for i, url in enumerate(urls):
            if i % 2 == 0:
                self.agents['python'].bus.send('python', 'rust', 'crawl_url', {'url': url})
            else:
                self.agents['python'].bus.send('python', 'go', 'download_url', {'url': url})
        
        time.sleep(3)
    
    def print_message_log(self):
        """Print all messages exchanged"""
        print("\n" + "="*70)
        print("📋 Message Log")
        print("="*70)
        
        all_msgs = []
        for receiver, msgs in self.bus.messages.items():
            all_msgs.extend(msgs)
        
        for msg in all_msgs:
            sender = msg['sender']
            receiver = msg['receiver']
            msg_type = msg['type']
            emoji = {'python': '🐍', 'rust': '🦀', 'go': '🐹'}
            print(f"{emoji[sender]} {sender} → {emoji[receiver]} {receiver}: {msg_type}")
        
        print("="*70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python message_bus.py <scenario>")
        print("\nScenarios:")
        print("  full_scan         - Full collaborative scan")
        print("  distributed_crawl - Distributed crawl with work sharing")
        print("\nExample:")
        print("  python message_bus.py full_scan")
        sys.exit(1)
    
    scenario = sys.argv[1]
    
    system = CollaborativeSystem()
    system.start()
    
    time.sleep(1)  # Let agents initialize
    
    system.run_scenario(scenario)
    
    time.sleep(2)  # Let messages process
    
    system.print_message_log()
    
    system.stop()
    
    print("\n✅ Collaboration complete!")


if __name__ == '__main__':
    main()
