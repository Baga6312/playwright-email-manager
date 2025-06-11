import asyncio
import json
import random
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import openai
from browser_manager import BrowserManager

class PlaywrightExecutor:
    def __init__(self, browser_manager: BrowserManager, openai_api_key: str):
        self.browser_manager = browser_manager
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.active_browsers: Dict[str, Dict] = {}
        
    async def launch_browser(self, browser_id: str, use_proxy: bool = False) -> Dict[str, Any]:
        """Launch a browser using generated command"""
        command = self.browser_manager.generate_launch_command(browser_id, use_proxy=use_proxy)

        playwright = await async_playwright().start()
        
        # Launch browser with fingerprint
        browser = await playwright.chromium.launch(**command["launch_options"])
        
        # Create context with fingerprint
        context = await browser.new_context(**command["context_options"])
        
        # Apply additional fingerprint overrides
        page = await context.new_page()
        await self.apply_fingerprint_overrides(page, command["fingerprint_overrides"])
        
        browser_info = {
            "playwright": playwright,
            "browser": browser,
            "context": context,
            "page": page,
            "browser_id": browser_id,
            "launched_at": datetime.now()
        }
        
        self.active_browsers[browser_id] = browser_info
        
        # Update browser status in database
        self.update_browser_status(browser_id, "running")
        
        return browser_info
    
    async def apply_fingerprint_overrides(self, page: Page, overrides: Dict[str, Any]):
        """Apply advanced fingerprint overrides"""
        
        # Override WebGL
        await page.add_init_script(f"""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{overrides['webgl_vendor']}';
                if (parameter === 37446) return '{overrides['webgl_renderer']}';
                return getParameter.apply(this, arguments);
            }};
        """)
        
        # Override canvas fingerprint
        await page.add_init_script(f"""
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type) {{
                const context = originalGetContext.apply(this, arguments);
                if (type === '2d') {{
                    const originalFillText = context.fillText;
                    context.fillText = function() {{
                        const result = originalFillText.apply(this, arguments);
                        // Add noise to canvas
                        const imageData = this.getImageData(0, 0, 1, 1);
                        imageData.data[0] += Math.floor(Math.random() * 10);
                        this.putImageData(imageData, 0, 0);
                        return result;
                    }};
                }}
                return context;
            }};
        """)
        
        # Override fonts
        await page.add_init_script(f"""
            Object.defineProperty(navigator, 'fonts', {{
                get: () => {{
                    return {{
                        check: () => true,
                        ready: Promise.resolve(),
                        values: () => {json.dumps(overrides['fonts'])}
                    }};
                }}
            }});
        """)
        
        # Remove automation indicators
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            delete window.chrome.runtime.onConnect;
            delete window.chrome.runtime.onMessage;
        """)
    
    async def execute_command(self, browser_id: str, command: Dict[str, Any]):
        """Execute a single command"""
        if browser_id not in self.active_browsers:
            await self.launch_browser(browser_id)
        
        page = self.active_browsers[browser_id]["page"]
        
        try:
            if command["type"] == "navigate":
                await page.goto(command["url"])
                if "wait_for" in command:
                    await page.wait_for_selector(command["wait_for"])
                    
            elif command["type"] == "click":
                if "index" in command:
                    elements = await page.query_selector_all(command["selector"])
                    if elements and len(elements) > command["index"]:
                        await elements[command["index"]].click()
                else:
                    await page.click(command["selector"])
                    
            elif command["type"] == "fill":
                await page.fill(command["selector"], command["value"])
                
            elif command["type"] == "scroll":
                if command["direction"] == "down":
                    await page.evaluate(f"window.scrollBy(0, {command['amount']})")
                elif command["direction"] == "up":
                    await page.evaluate(f"window.scrollBy(0, -{command['amount']})")
                    
            elif command["type"] == "wait":
                await asyncio.sleep(command["duration"] / 1000)
                
            elif command["type"] == "wait_for_navigation":
                await page.wait_for_load_state("networkidle")
                
            elif command["type"] == "custom_action":
                await self.execute_custom_action(browser_id, command["action"])
                
        except Exception as e:
            print(f"Error executing command {command['type']}: {str(e)}")
    
    async def execute_custom_action(self, browser_id: str, action: str):
        """Execute custom actions like email processing"""
        page = self.active_browsers[browser_id]["page"]
        
        if action == "process_emails":
            await self.process_emails(browser_id)
    
    async def process_emails(self, browser_id: str):
        """Process emails: check spam, move to inbox, reply with AI"""
        page = self.active_browsers[browser_id]["page"]
        
        try:
            # Check spam folder
            spam_selector = "[data-tooltip='Spam']"
            if await page.query_selector(spam_selector):
                await page.click(spam_selector)
                await asyncio.sleep(2)
                
                # Get spam emails
                spam_emails = await page.query_selector_all(".zA")
                
                for i, email in enumerate(spam_emails[:5]):  # Process first 5
                    await email.click()
                    await asyncio.sleep(1)
                    
                    # Move to inbox
                    move_button = await page.query_selector("[data-tooltip='Not spam']")
                    if move_button:
                        await move_button.click()
                        await asyncio.sleep(1)
                    
                    # Mark as important
                    important_button = await page.query_selector("[data-tooltip='Mark as important']")
                    if important_button:
                        await important_button.click()
                        await asyncio.sleep(1)
                    
                    await page.go_back()
                    await asyncio.sleep(1)
            
            # Go to inbox
            inbox_selector = "[data-tooltip='Inbox']"
            await page.click(inbox_selector)
            await asyncio.sleep(2)
            
            # Process recent emails for replies
            recent_emails = await page.query_selector_all(".zA")
            
            for i, email in enumerate(recent_emails[:3]):  # Process first 3
                await email.click()
                await asyncio.sleep(2)
                
                # Check if email needs reply
                reply_button = await page.query_selector("[data-tooltip='Reply']")
                if reply_button:
                    # Get email content for AI reply
                    email_content = await page.inner_text(".ii.gt")
                    
                    if email_content and len(email_content) > 50:
                        # Generate AI reply
                        ai_reply = await self.generate_ai_reply(email_content)
                        
                        if ai_reply:
                            await reply_button.click()
                            await asyncio.sleep(2)
                            
                            # Fill reply
                            reply_box = await page.query_selector("[contenteditable='true']")
                            if reply_box:
                                await reply_box.fill(ai_reply)
                                await asyncio.sleep(1)
                                
                                # Send reply
                                send_button = await page.query_selector("[data-tooltip='Send']")
                                if send_button:
                                    await send_button.click()
                                    await asyncio.sleep(2)
                
                await page.go_back()
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error processing emails: {str(e)}")
    
    async def generate_ai_reply(self, email_content: str) -> Optional[str]:
        """Generate AI reply using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Generate a brief, professional email reply. Keep it under 100 words and natural sounding."
                    },
                    {
                        "role": "user",
                        "content": f"Generate a reply to this email: {email_content[:500]}"
                    }
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating AI reply: {str(e)}")
            return None
    
    async def run_browser_batch(self, batch_size: int = 350):
        """Run a batch of browsers with interactions"""
        batch_command = self.browser_manager.schedule_browser_batch(batch_size)
        browser_ids = batch_command["browser_ids"]
        
        print(f"Starting batch of {len(browser_ids)} browsers")
        
        # Process browsers in smaller concurrent groups
        group_size = 10  # Run 10 browsers concurrently
        
        for i in range(0, len(browser_ids), group_size):
            group = browser_ids[i:i + group_size]
            tasks = []
            
            for browser_id in group:
                task = asyncio.create_task(self.run_single_browser_session(browser_id))
                tasks.append(task)
            
            # Wait for group to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Small delay between groups
            await asyncio.sleep(5)
        
        print(f"Completed batch of {len(browser_ids)} browsers")
    
    async def run_single_browser_session(self, browser_id: str):
        """Run a complete session for a single browser"""
        try:
            # Launch browser
            await self.launch_browser(browser_id)
            
            # Generate and execute interaction commands
            commands = self.browser_manager.generate_interaction_commands(browser_id)
            
            for command in commands:
                await self.execute_command(browser_id, command)
                # Random delay between actions
                await asyncio.sleep(random.uniform(1, 3))
            
            # Update last interaction time
            self.update_browser_last_interaction(browser_id)
            
        except Exception as e:
            print(f"Error in browser session {browser_id}: {str(e)}")
        
        finally:
            # Clean up browser
            await self.close_browser(browser_id)
    
    async def close_browser(self, browser_id: str):
        """Close a browser and clean up resources"""
        if browser_id in self.active_browsers:
            browser_info = self.active_browsers[browser_id]
            
            try:
                await browser_info["context"].close()
                await browser_info["browser"].close()
                await browser_info["playwright"].stop()
            except Exception as e:
                print(f"Error closing browser {browser_id}: {str(e)}")
            
            del self.active_browsers[browser_id]
            self.update_browser_status(browser_id, "inactive")
    
    def update_browser_status(self, browser_id: str, status: str):
        """Update browser status in database"""
        conn = sqlite3.connect(self.browser_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE browsers SET status = ? WHERE browser_id = ?',
            (status, browser_id)
        )
        
        conn.commit()
        conn.close()
    
    def update_browser_last_interaction(self, browser_id: str):
        """Update last interaction time"""
        conn = sqlite3.connect(self.browser_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE browsers SET last_interaction = ? WHERE browser_id = ?',
            (datetime.now().isoformat(), browser_id)
        )
        
        conn.commit()
        conn.close()

# Scheduler for continuous browser automation
class BrowserScheduler:
    def __init__(self, executor: PlaywrightExecutor, browser_manager: BrowserManager):
        self.executor = executor
        self.browser_manager = browser_manager
        self.running = False
        
    async def start_continuous_automation(self, batch_size: int = 350, interval_minutes: int = 5):
        """Start continuous browser automation with batching"""
        self.running = True
        print(f"Starting continuous automation: {batch_size} browsers every {interval_minutes} minutes")
        
        while self.running:
            try:
                # Run browser batch
                await self.executor.run_browser_batch(batch_size)
                
                # Wait for next batch
                print(f"Waiting {interval_minutes} minutes for next batch...")
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                print(f"Error in continuous automation: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def stop_automation(self):
        """Stop continuous automation"""
        self.running = False
        print("Stopping continuous automation...")

# CLI and main execution
async def main():
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Playwright Browser Executor')
    parser.add_argument('--openai-key', required=True, help='OpenAI API key')
    parser.add_argument('--db-path', default='browsers.db', help='Database path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
   # Test browser launch
    test_parser = subparsers.add_parser('test-launch', help='Test browser launch')
    test_parser.add_argument('--browser-id', required=True, help='Browser ID')
    test_parser.add_argument('--headless', action='store_true', help='Run headless')
    test_parser.add_argument('--no-proxy', action='store_true', help='Ignore proxies')

    # Single browser execution
    single_parser = subparsers.add_parser('run-single', help='Run single browser')
    single_parser.add_argument('--browser-id', required=True, help='Browser ID')
    single_parser.add_argument('--no-proxy', action='store_true', help='Ignore proxies')

    # Batch execution
    batch_parser = subparsers.add_parser('run-batch', help='Run browser batch')
    batch_parser.add_argument('--size', type=int, default=350, help='Batch size')
    batch_parser.add_argument('--no-proxy', action='store_true', help='Ignore proxies')

    # Continuous automation
    continuous_parser = subparsers.add_parser('start-automation', help='Start continuous automation')
    continuous_parser.add_argument('--batch-size', type=int, default=350, help='Batch size')
    continuous_parser.add_argument('--interval', type=int, default=5, help='Interval in minutes')
    continuous_parser.add_argument('--no-proxy', action='store_true', help='Ignore proxies')
    
    args = parser.parse_args()
    
    # Initialize components
    browser_manager = BrowserManager(args.db_path)
    executor = PlaywrightExecutor(browser_manager, args.openai_key)
    
    if args.command == 'run-single':
        await executor.run_single_browser_session(args.browser_id, use_proxy=not args.no_proxy)      

    elif args.command == 'run-batch':
        await executor.run_browser_batch(args.size)
        
    elif args.command == 'start-automation':
        scheduler = BrowserScheduler(executor, browser_manager)
        try:
            await scheduler.start_continuous_automation(args.batch_size, args.interval)
        except KeyboardInterrupt:
            scheduler.stop_automation()
            
    elif args.command == 'test-launch':
        browser_info = await executor.launch_browser(args.browser_id, use_proxy=not args.no_proxy)

        print(f"Browser launched successfully: {browser_info['browser_id']}")
        
        # Navigate to test page
        page = browser_info["page"]
        await page.goto("https://httpbin.org/headers")
        await asyncio.sleep(5)
        
        # Close browser
        await executor.close_browser(args.browser_id)
        print("Test completed successfully")

if __name__ == "__main__":
    asyncio.run(main())