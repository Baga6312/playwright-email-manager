import csv
import json
import sqlite3
from typing import List, Dict, Optional
from browser_manager import BrowserManager

class CSVImportUtility:
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.init_proxy_accounts_tables()
    
    def init_proxy_accounts_tables(self):
        """Initialize proxy and email accounts tables"""
        conn = sqlite3.connect(self.browser_manager.db_path)
        cursor = conn.cursor()
        
        # Proxies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                username TEXT,
                password TEXT,
                protocol TEXT DEFAULT 'http',
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Email accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                provider TEXT NOT NULL,
                recovery_email TEXT,
                phone TEXT,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def import_proxies_from_csv(self, csv_file_path: str) -> List[int]:
        """
        Import proxies from CSV file
        Expected CSV format: name,host,port,username,password,protocol
        """
        proxy_ids = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                conn = sqlite3.connect(self.browser_manager.db_path)
                cursor = conn.cursor()
                
                for row in csv_reader:
                    try:
                        cursor.execute('''
                            INSERT INTO proxies (name, host, port, username, password, protocol)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            row.get('name', ''),
                            row['host'],
                            int(row['port']),
                            row.get('username', ''),
                            row.get('password', ''),
                            row.get('protocol', 'http')
                        ))
                        
                        proxy_ids.append(cursor.lastrowid)
                        
                    except Exception as e:
                        print(f"Error importing proxy {row}: {str(e)}")
                        continue
                
                conn.commit()
                conn.close()
                
                print(f"Successfully imported {len(proxy_ids)} proxies")
                
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
        
        return proxy_ids
    
    def import_email_accounts_from_csv(self, csv_file_path: str) -> List[int]:
        """
        Import email accounts from CSV file
        Expected CSV format: email,password,provider,recovery_email,phone
        """
        account_ids = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                conn = sqlite3.connect(self.browser_manager.db_path)
                cursor = conn.cursor()
                
                for row in csv_reader:
                    try:
                        cursor.execute('''
                            INSERT INTO email_accounts (email, password, provider, recovery_email, phone)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            row['email'],
                            row['password'],
                            row.get('provider', 'gmail'),
                            row.get('recovery_email', ''),
                            row.get('phone', '')
                        ))
                        
                        account_ids.append(cursor.lastrowid)
                        
                    except Exception as e:
                        print(f"Error importing email account {row}: {str(e)}")
                        continue
                
                conn.commit()
                conn.close()
                
                print(f"Successfully imported {len(account_ids)} email accounts")
                
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
        
        return account_ids
    
    def import_browsers_from_csv(self, csv_file_path: str) -> List[str]:
  
        browser_ids = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    try:
                        # Create or find proxy
                        proxy_id = None
                        if row.get('proxy_host'):
                            proxy_id = self.create_or_find_proxy(
                                host=row['proxy_host'],
                                port=int(row['proxy_port']),
                                username=row.get('proxy_username', ''),
                                password=row.get('proxy_password', '')
                            )
                        
                        # Create or find email account
                        email_account_id = None
                        if row.get('email'):
                            email_account_id = self.create_or_find_email_account(
                                email=row['email'],
                                password=row['email_password'],
                                provider=row.get('provider', 'gmail')
                            )
                        
                        # Create browser
                        browser_id = self.browser_manager.create_browser(
                            name=row.get('name', f"Browser_{len(browser_ids) + 1}"),
                            proxy_id=proxy_id,
                            email_account_id=email_account_id,
                            to_interact=row.get('to_interact', '').lower() == 'true'
                        )
                        
                        browser_ids.append(browser_id)
                        
                    except Exception as e:
                        print(f"Error importing browser {row}: {str(e)}")
                        continue
                
                print(f"Successfully imported {len(browser_ids)} browsers")
                
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
        
        return browser_ids
    
    def create_or_find_proxy(self, host: str, port: int, username: str = '', password: str = '') -> int:
        """Create new proxy or find existing one"""
        conn = sqlite3.connect(self.browser_manager.db_path)
        cursor = conn.cursor()
        
        # Check if proxy already exists
        cursor.execute('''
            SELECT id FROM proxies 
            WHERE host = ? AND port = ? AND username = ?
        ''', (host, port, username))
        
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return existing[0]
        
        # Create new proxy
        cursor.execute('''
            INSERT INTO proxies (host, port, username, password)
            VALUES (?, ?, ?, ?)
        ''', (host, port, username, password))
        
        proxy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return proxy_id
    
    def create_or_find_email_account(self, email: str, password: str, provider: str = 'gmail') -> int:
        """Create new email account or find existing one"""
        conn = sqlite3.connect(self.browser_manager.db_path)
        cursor = conn.cursor()
        
        # Check if account already exists
        cursor.execute('SELECT id FROM email_accounts WHERE email = ?', (email,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return existing[0]
        
        # Create new account
        cursor.execute('''
            INSERT INTO email_accounts (email, password, provider)
            VALUES (?, ?, ?)
        ''', (email, password, provider))
        
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return account_id
    
    def export_browsers_to_csv(self, csv_file_path: str, include_fingerprints: bool = False):
        """Export browsers to CSV file"""
        browsers = self.browser_manager.get_browser_list()
        
        fieldnames = [
            'browser_id', 'name', 'status', 'to_interact', 'created_at',
            'proxy_host', 'proxy_port', 'proxy_username',
            'email', 'email_provider', 'user_agent'
        ]
        
        if include_fingerprints:
            fieldnames.extend(['viewport_width', 'viewport_height', 'timezone', 'locale', 'platform'])
        
        try:
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                conn = sqlite3.connect(self.browser_manager.db_path)
                cursor = conn.cursor()
                
                for browser in browsers:
                    row = {
                        'browser_id': browser['browser_id'],
                        'name': browser['name'],
                        'status': browser['status'],
                        'to_interact': browser['to_interact'],
                        'created_at': browser['created_at'],
                        'user_agent': browser['user_agent']
                    }
                    
                    # Get proxy info
                    if browser['proxy_id']:
                        cursor.execute('SELECT host, port, username FROM proxies WHERE id = ?', 
                                     (browser['proxy_id'],))
                        proxy = cursor.fetchone()
                        if proxy:
                            row.update({
                                'proxy_host': proxy[0],
                                'proxy_port': proxy[1],
                                'proxy_username': proxy[2]
                            })
                    
                    # Get email info
                    if browser['email_account_id']:
                        cursor.execute('SELECT email, provider FROM email_accounts WHERE id = ?', 
                                     (browser['email_account_id'],))
                        email_account = cursor.fetchone()
                        if email_account:
                            row.update({
                                'email': email_account[0],
                                'email_provider': email_account[1]
                            })
                    
                    # Add fingerprint data if requested
                    if include_fingerprints:
                        cursor.execute('''
                            SELECT viewport_width, viewport_height, timezone, locale, platform 
                            FROM browsers WHERE browser_id = ?
                        ''', (browser['browser_id'],))
                        fingerprint = cursor.fetchone()
                        if fingerprint:
                            row.update({
                                'viewport_width': fingerprint[0],
                                'viewport_height': fingerprint[1],
                                'timezone': fingerprint[2],
                                'locale': fingerprint[3],
                                'platform': fingerprint[4]
                            })
                    
                    writer.writerow(row)
                
                conn.close()
                print(f"Successfully exported {len(browsers)} browsers to {csv_file_path}")
                
        except Exception as e:
            print(f"Error exporting to CSV: {str(e)}")
    
    def get_proxy_list(self) -> List[Dict]:
        """Get all proxies"""
        conn = sqlite3.connect(self.browser_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM proxies ORDER BY created_at DESC')
        proxies = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': proxy[0],
                'name': proxy[1],
                'host': proxy[2],
                'port': proxy[3],
                'username': proxy[4],
                'protocol': proxy[6],
                'status': proxy[7],
                'created_at': proxy[8]
            }
            for proxy in proxies
        ]
    
    def get_email_accounts_list(self) -> List[Dict]:
        """Get all email accounts"""
        conn = sqlite3.connect(self.browser_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM email_accounts ORDER BY created_at DESC')
        accounts = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': account[0],
                'email': account[1],
                'provider': account[3],
                'recovery_email': account[4],
                'phone': account[5],
                'status': account[6],
                'created_at': account[7]
            }
            for account in accounts
        ]
    
    def generate_sample_csv_files(self):
        """Generate sample CSV files for import"""
        
        # Sample proxies CSV
        proxies_sample = [
            {'name': 'Proxy1', 'host': '192.168.1.100', 'port': '8080', 'username': 'user1', 'password': 'pass1', 'protocol': 'http'},
            {'name': 'Proxy2', 'host': '192.168.1.101', 'port': '8080', 'username': 'user2', 'password': 'pass2', 'protocol': 'http'},
        ]
        
        with open('sample_proxies.csv', 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['name', 'host', 'port', 'username', 'password', 'protocol'])
            writer.writeheader()
            writer.writerows(proxies_sample)
        
        # Sample email accounts CSV
        emails_sample = [
            {'email': 'test1@gmail.com', 'password': 'password1', 'provider': 'gmail', 'recovery_email': 'recovery1@gmail.com', 'phone': '1234567890'},
            {'email': 'test2@outlook.com', 'password': 'password2', 'provider': 'outlook', 'recovery_email': 'recovery2@outlook.com', 'phone': '0987654321'},
        ]
        
        with open('sample_emails.csv', 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['email', 'password', 'provider', 'recovery_email', 'phone'])
            writer.writeheader()
            writer.writerows(emails_sample)
        
        # Sample browsers CSV
        browsers_sample = [
            {
                'name': 'Browser1',
                'proxy_host': '192.168.1.100',
                'proxy_port': '8080',
                'proxy_username': 'user1',
                'proxy_password': 'pass1',
                'email': 'test1@gmail.com',
                'email_password': 'password1',
                'provider': 'gmail',
                'to_interact': 'true'
            },
            {
                'name': 'Browser2',
                'proxy_host': '192.168.1.101',
                'proxy_port': '8080',
                'proxy_username': 'user2',
                'proxy_password': 'pass2',
                'email': 'test2@outlook.com',
                'email_password': 'password2',
                'provider': 'outlook',
                'to_interact': 'false'
            }
        ]
        
        with open('sample_browsers.csv', 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'name', 'proxy_host', 'proxy_port', 'proxy_username', 'proxy_password',
                'email', 'email_password', 'provider', 'to_interact'
            ])
            writer.writeheader()
            writer.writerows(browsers_sample)
        
        print("Generated sample CSV files:")
        print("- sample_proxies.csv")
        print("- sample_emails.csv")
        print("- sample_browsers.csv")

# CLI interface
if __name__ == "__main__":
    import argparse
    
    browser_manager = BrowserManager()
    csv_util = CSVImportUtility(browser_manager)
    
    parser = argparse.ArgumentParser(description='CSV Import/Export Utility')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Import commands
    import_proxies = subparsers.add_parser('import-proxies', help='Import proxies from CSV')
    import_proxies.add_argument('--file', required=True, help='CSV file path')
    
    import_emails = subparsers.add_parser('import-emails', help='Import email accounts from CSV')
    import_emails.add_argument('--file', required=True, help='CSV file path')
    
    import_browsers = subparsers.add_parser('import-browsers', help='Import browsers from CSV')
    import_browsers.add_argument('--file', required=True, help='CSV file path')
    
    # Export commands
    export_browsers = subparsers.add_parser('export-browsers', help='Export browsers to CSV')
    export_browsers.add_argument('--file', required=True, help='Output CSV file path')
    export_browsers.add_argument('--include-fingerprints', action='store_true', help='Include fingerprint data')
    
    # List commands
    list_proxies = subparsers.add_parser('list-proxies', help='List all proxies')
    list_emails = subparsers.add_parser('list-emails', help='List all email accounts')
    
    # Generate samples
    generate_samples = subparsers.add_parser('generate-samples', help='Generate sample CSV files')
    
    args = parser.parse_args()
    
    if args.command == 'import-proxies':
        csv_util.import_proxies_from_csv(args.file)
        
    elif args.command == 'import-emails':
        csv_util.import_email_accounts_from_csv(args.file)
        
    elif args.command == 'import-browsers':
        csv_util.import_browsers_from_csv(args.file)
        
    elif args.command == 'export-browsers':
        csv_util.export_browsers_to_csv(args.file, args.include_fingerprints)
        
    elif args.command == 'list-proxies':
        proxies = csv_util.get_proxy_list()
        print(f"Found {len(proxies)} proxies:")
        for proxy in proxies:
            print(f"ID: {proxy['id']} | {proxy['host']}:{proxy['port']} | {proxy['username']} | {proxy['status']}")
            
    elif args.command == 'list-emails':
        accounts = csv_util.get_email_accounts_list()
        print(f"Found {len(accounts)} email accounts:")
        for account in accounts:
            print(f"ID: {account['id']} | {account['email']} | {account['provider']} | {account['status']}")
            
    elif args.command == 'generate-samples':
        csv_util.generate_sample_csv_files()