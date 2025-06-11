import json
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
import os

class BrowserManager:
    def __init__(self, db_path: str = "browsers.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Browsers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS browsers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                browser_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                proxy_id INTEGER,
                email_account_id INTEGER,
                fingerprint TEXT NOT NULL,
                status TEXT DEFAULT 'inactive',
                to_interact BOOLEAN DEFAULT 0,
                last_interaction DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT,
                viewport_width INTEGER,
                viewport_height INTEGER,
                timezone TEXT,
                locale TEXT,
                platform TEXT
            )
        ''')
        
        # Commands table for generated commands
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                browser_id TEXT NOT NULL,
                command_type TEXT NOT NULL,
                command_data TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                scheduled_time DATETIME,
                executed_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (browser_id) REFERENCES browsers (browser_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_fingerprint(self) -> Dict[str, Any]:
        """Generate a unique browser fingerprint"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        viewports = [
            (1920, 1080), (1366, 768), (1440, 900), (1536, 864), (1280, 720)
        ]
        
        timezones = [
            "America/New_York", "America/Los_Angeles", "Europe/London", 
            "Europe/Paris", "Asia/Tokyo", "Australia/Sydney"
        ]
        
        locales = ["en-US", "en-GB", "fr-FR", "de-DE", "es-ES", "ja-JP"]
        platforms = ["Win32", "MacIntel", "Linux x86_64"]
        
        viewport = random.choice(viewports)
        
        fingerprint = {
            "user_agent": random.choice(user_agents),
            "viewport": {"width": viewport[0], "height": viewport[1]},
            "timezone": random.choice(timezones),
            "locale": random.choice(locales),
            "platform": random.choice(platforms),
            "screen": {
                "width": viewport[0],
                "height": viewport[1],
                "colorDepth": random.choice([24, 32]),
                "pixelDepth": random.choice([24, 32])
            },
            "webgl_vendor": random.choice(["Google Inc.", "NVIDIA Corporation", "AMD"]),
            "webgl_renderer": f"ANGLE (Direct3D11 vs_5_0 ps_5_0, D3D11-{random.randint(10000, 99999)})",
            "canvas_fingerprint": ''.join(random.choices(string.ascii_letters + string.digits, k=32)),
            "audio_fingerprint": random.uniform(100, 200),
            "fonts": random.sample([
                "Arial", "Times New Roman", "Helvetica", "Georgia", "Verdana", 
                "Courier New", "Comic Sans MS", "Trebuchet MS", "Impact"
            ], k=random.randint(5, 9))
        }
        
        return fingerprint
    


    def generate_launch_command(self, browser_id: str, headless: bool = False, use_proxy: bool = True ) -> Dict[str, Any]:
        """Generate Playwright launch command for a specific browser"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM browsers WHERE browser_id = ?', (browser_id,))
        browser = cursor.fetchone()

        if not browser:
            conn.close()
            raise ValueError(f"Browser {browser_id} not found")

        fingerprint = json.loads(browser[5])  # fingerprint column

        command = {
            "browser_id": browser_id,
            "launch_options": {
                "headless": headless,
                "args": [
                    f"--user-agent={fingerprint['user_agent']}",
                    f"--window-size={fingerprint['viewport']['width']},{fingerprint['viewport']['height']}",
                    "--no-default-browser-check",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            },
            "context_options": {
                "user_agent": fingerprint['user_agent'],
                "viewport": fingerprint['viewport'],
                "timezone_id": fingerprint['timezone'],
                "locale": fingerprint['locale'],
                "screen": fingerprint['screen'],
                "extra_http_headers": {
                    "Accept-Language": f"{fingerprint['locale']},en;q=0.9"
                }
            },
            "fingerprint_overrides": {
                "webgl_vendor": fingerprint['webgl_vendor'],
                "webgl_renderer": fingerprint['webgl_renderer'],
                "canvas_fingerprint": fingerprint['canvas_fingerprint'],
                "audio_fingerprint": fingerprint['audio_fingerprint'],
                "fonts": fingerprint['fonts']
            }
        }

        # Only add proxy if use_proxy is True and proxy exists
        if use_proxy and browser[3]:  # proxy_id column
            cursor.execute('SELECT host, port, username, password FROM proxies WHERE id = ?', (browser[3],))
            proxy_data = cursor.fetchone()
            if proxy_data:
                command["context_options"]["proxy"] = {
                    "server": f"http://{proxy_data[0]}:{proxy_data[1]}",
                    "username": proxy_data[2] if proxy_data[2] else None,
                    "password": proxy_data[3] if proxy_data[3] else None
                }

        conn.close()
        return command


    def create_browser(self, name: str, proxy_id: Optional[int] = None, 
                      email_account_id: Optional[int] = None, 
                      to_interact: bool = False) -> str:
        """Create a new browser with unique fingerprint"""
        browser_id = str(uuid.uuid4())
        fingerprint = self.generate_fingerprint()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO browsers (browser_id, name, proxy_id, email_account_id, 
                                fingerprint, to_interact, user_agent, viewport_width, 
                                viewport_height, timezone, locale, platform)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            browser_id, name, proxy_id, email_account_id,
            json.dumps(fingerprint), to_interact,
            fingerprint['user_agent'], fingerprint['viewport']['width'],
            fingerprint['viewport']['height'], fingerprint['timezone'],
            fingerprint['locale'], fingerprint['platform']
        ))
        
        conn.commit()
        conn.close()
        
        return browser_id
    
    def create_browsers_bulk(self, browsers_data: List[Dict]) -> List[str]:
        """Create multiple browsers from CSV data"""
        browser_ids = []
        
        for browser_data in browsers_data:
            browser_id = self.create_browser(
                name=browser_data.get('name', f"Browser_{random.randint(1000, 9999)}"),
                proxy_id=browser_data.get('proxy_id'),
                email_account_id=browser_data.get('email_account_id'),
                to_interact=browser_data.get('to_interact', False)
            )
            browser_ids.append(browser_id)
            
        return browser_ids
    
   
    def generate_interaction_commands(self, browser_id: str) -> List[Dict[str, Any]]:
        """Generate interaction commands for daily automation"""
        commands = []
        
        # Gmail/Outlook login and interaction
        email_commands = [
            {
                "type": "navigate",
                "url": "https://gmail.com",
                "wait_for": "input[type='email']"
            },
            {
                "type": "fill",
                "selector": "input[type='email']",
                "value": "{{email_address}}"  # Will be replaced with actual email
            },
            {
                "type": "click",
                "selector": "#identifierNext"
            },
            {
                "type": "wait",
                "duration": 2000
            },
            {
                "type": "fill",
                "selector": "input[type='password']",
                "value": "{{email_password}}"
            },
            {
                "type": "click",
                "selector": "#passwordNext"
            },
            {
                "type": "wait_for_navigation"
            },
            {
                "type": "scroll",
                "direction": "down",
                "amount": 300
            },
            {
                "type": "click",
                "selector": "[data-tooltip='Inbox']"
            },
            {
                "type": "custom_action",
                "action": "process_emails",
                "description": "Check spam, move important emails, reply with AI"
            }
        ]
        
        # Random browsing actions
        browsing_commands = [
            {
                "type": "navigate",
                "url": random.choice([
                    "https://news.google.com",
                    "https://www.reddit.com",
                    "https://stackoverflow.com"
                ])
            },
            {
                "type": "scroll",
                "direction": "down",
                "amount": random.randint(200, 500)
            },
            {
                "type": "wait",
                "duration": random.randint(1000, 3000)
            },
            {
                "type": "click",
                "selector": "a",
                "index": random.randint(0, 5)
            }
        ]
        
        commands.extend(email_commands)
        commands.extend(browsing_commands)
        
        return commands
    
    def schedule_browser_batch(self, batch_size: int = 350, interval_minutes: int = 5) -> Dict[str, Any]:
        """Generate command to schedule browser batches"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT browser_id FROM browsers 
            WHERE to_interact = 1 AND status != 'running'
            ORDER BY last_interaction ASC NULLS FIRST
            LIMIT ?
        ''', (batch_size,))
        
        browsers = cursor.fetchall()
        conn.close()
        
        batch_command = {
            "type": "batch_execution",
            "browser_ids": [browser[0] for browser in browsers],
            "batch_size": batch_size,
            "interval_minutes": interval_minutes,
            "scheduled_time": datetime.now().isoformat(),
            "next_batch_time": (datetime.now() + timedelta(minutes=interval_minutes)).isoformat()
        }
        
        return batch_command
    
    def save_command(self, browser_id: str, command_type: str, 
                    command_data: Dict, scheduled_time: Optional[datetime] = None):
        """Save a generated command to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO commands (browser_id, command_type, command_data, scheduled_time)
            VALUES (?, ?, ?, ?)
        ''', (
            browser_id, command_type, json.dumps(command_data),
            scheduled_time.isoformat() if scheduled_time else None
        ))
        
        conn.commit()
        conn.close()
    
    def get_pending_commands(self, browser_id: Optional[str] = None) -> List[Dict]:
        """Get pending commands for execution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if browser_id:
            cursor.execute('''
                SELECT * FROM commands 
                WHERE browser_id = ? AND status = 'pending'
                ORDER BY scheduled_time ASC
            ''', (browser_id,))
        else:
            cursor.execute('''
                SELECT * FROM commands 
                WHERE status = 'pending' AND 
                (scheduled_time IS NULL OR scheduled_time <= datetime('now'))
                ORDER BY scheduled_time ASC
            ''')
        
        commands = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": cmd[0],
                "browser_id": cmd[1],
                "command_type": cmd[2],
                "command_data": json.loads(cmd[3]),
                "status": cmd[4],
                "scheduled_time": cmd[5],
                "created_at": cmd[7]
            }
            for cmd in commands
        ]
    
    def get_browser_list(self) -> List[Dict]:
        """Get list of all browsers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM browsers ORDER BY created_at DESC')
        browsers = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": browser[0],
                "browser_id": browser[1],
                "name": browser[2],
                "proxy_id": browser[3],
                "email_account_id": browser[4],
                "status": browser[6],
                "to_interact": bool(browser[7]),
                "last_interaction": browser[8],
                "created_at": browser[9],
                "user_agent": browser[10]
            }
            for browser in browsers
        ]

# Example usage and CLI interface
if __name__ == "__main__":
    import argparse
    
    manager = BrowserManager()
    
    parser = argparse.ArgumentParser(description='Browser Manager CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create browser command
    create_parser = subparsers.add_parser('create', help='Create a new browser')
    create_parser.add_argument('--name', required=True, help='Browser name')
    create_parser.add_argument('--proxy-id', type=int, help='Proxy ID')
    create_parser.add_argument('--email-id', type=int, help='Email account ID')
    create_parser.add_argument('--interact', action='store_true', help='Enable daily interactions')
    
    # Generate launch command
    launch_parser = subparsers.add_parser('launch', help='Generate launch command')
    launch_parser.add_argument('--browser-id', required=True, help='Browser ID')
    launch_parser.add_argument('--headless', action='store_true', help='Run headless')
    
    # Schedule batch command
    batch_parser = subparsers.add_parser('batch', help='Schedule browser batch')
    batch_parser.add_argument('--size', type=int, default=350, help='Batch size')
    batch_parser.add_argument('--interval', type=int, default=5, help='Interval in minutes')


    # List browsers command
    list_parser = subparsers.add_parser('list', help='List all browsers')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        browser_id = manager.create_browser(
            name=args.name,
            proxy_id=args.proxy_id,
            email_account_id=args.email_id,
            to_interact=args.interact
        )
        print(f"Created browser: {browser_id}")
        
    elif args.command == 'launch':
        command = manager.generate_launch_command(args.browser_id, args.headless)
        print(json.dumps(command, indent=2))
        
    elif args.command == 'batch':
        batch_command = manager.schedule_browser_batch(args.size, args.interval)
        print(json.dumps(batch_command, indent=2))
        
    elif args.command == 'list':
        browsers = manager.get_browser_list()
        for browser in browsers:
            print(f"ID: {browser['browser_id'][:8]}... | Name: {browser['name']} | Status: {browser['status']}")