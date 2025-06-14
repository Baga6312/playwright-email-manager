from playwright.sync_api import sync_playwright
import time
import json

def test_user_agent_amiunique(user_agent, custom_product=None, custom_product_sub=None, custom_app_name=None):
    """
    Test a custom user agent and navigator properties on AmIUnique website using Playwright
    """
    with sync_playwright() as p:
        # Launch browser with custom user agent
        browser = p.chromium.launch(headless=False)  # Set to True for headless mode
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        
        # Override navigator properties before any page loads
        navigator_override = f"""
        Object.defineProperty(navigator, 'product', {{
            get: () => '{custom_product or "Gecko"}',
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'productSub', {{
            get: () => '{custom_product_sub or "20100101"}',
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'appName', {{
            get: () => '{custom_app_name or "Netscape"}',
            configurable: true
        }});
        
        console.log('Navigator properties overridden:');
        console.log('Product:', navigator.product);
        console.log('ProductSub:', navigator.productSub);
        console.log('AppName:', navigator.appName);
        """
        
        # Add script to override navigator properties
        page.add_init_script(navigator_override)
        
        try:
            print(f"Testing User-Agent: {user_agent}")
            print(f"Custom Product: {custom_product or 'Gecko'}")
            print(f"Custom ProductSub: {custom_product_sub or '20100101'}")
            print(f"Custom AppName: {custom_app_name or 'Netscape'}")
            print("Opening AmIUnique...")
            
            # Go to AmIUnique
            page.goto("https://amiunique.org/fingerprint")
            
            # Wait for the page to load
            time.sleep(3)
            
            # Verify our navigator overrides worked
            actual_product = page.evaluate("navigator.product")
            actual_product_sub = page.evaluate("navigator.productSub")
            actual_app_name = page.evaluate("navigator.appName")
            
            print(f"\n=== ACTUAL NAVIGATOR VALUES ===")
            print(f"navigator.product: {actual_product}")
            print(f"navigator.productSub: {actual_product_sub}")
            print(f"navigator.appName: {actual_app_name}")
            print(f"navigator.userAgent: {page.evaluate('navigator.userAgent')}")
            
            
            # Extract fingerprint data
            print("\n=== FINGERPRINT RESULTS ===")
            
            # Get all fingerprint attribute rows
            rows = page.query_selector_all(".fp-details tr")
            
            for row in rows:
                try:
                    attribute = row.query_selector("td:first-child").inner_text()
                    value = row.query_selector("td:nth-child(2)").inner_text()
                    percentage = row.query_selector("td:nth-child(3)").inner_text()
                    
                    print(f"{attribute}: {value} ({percentage})")
                    
                    # Highlight the Product attribute specifically
                    if "Product" in attribute:
                        print(f"*** PRODUCT DETECTED: {value} ***")
                        
                except Exception as e:
                    continue
            
            # Take a screenshot for reference
            page.screenshot(path=f"amiunique_test_{int(time.time())}.png")
            print(f"\nScreenshot saved as: amiunique_test_{int(time.time())}.png")
            
            # Wait a bit to see results
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            browser.close()

def main():
    """
    Main function to input user agent and navigator properties
    """
    print("=== AmIUnique Navigator Properties Tester ===\n")
    
    # Predefined configurations for quick testing
    preset_configs = {
        "1": {
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "product": "Gecko",
            "product_sub": "20030107",
            "app_name": "Netscape"
        },
        "2": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "product": "Gecko",
            "product_sub": "20100101",
            "app_name": "Netscape"
        },
        "3": {
            "user_agent": "Lynx/2.8.9rel.1 libwww-FM/2.14 SSL-MM/1.4.1",
            "product": "Lynx",
            "product_sub": "undefined",
            "app_name": "Lynx"
        },
        "4": {
            "user_agent": "w3m/0.5.3+git20210102",
            "product": "w3m",
            "product_sub": "undefined",
            "app_name": "w3m"
        },
        "5": {
            "user_agent": "NetSurf/3.10 (NetSurf; Linux)",
            "product": "NetSurf",
            "product_sub": "undefined",
            "app_name": "NetSurf"
        },
        "6": {
            "user_agent": "Mozilla/5.0 (compatible; Dillo 3.0.5)",
            "product": "Dillo",
            "product_sub": "undefined",
            "app_name": "Dillo"
        }
    }
    
    print("Choose a preset configuration:")
    print("1. Chrome (Standard)")
    print("2. Firefox (Standard)")
    print("3. Lynx (Text Browser)")
    print("4. w3m (Text Browser)")
    print("5. NetSurf (Lightweight)")
    print("6. Dillo (Minimal)")
    print("7. Custom Configuration")
    
    choice = input("\nEnter choice (1-7): ").strip()
    
    if choice in preset_configs:
        config = preset_configs[choice]
        user_agent = config["user_agent"]
        product = config["product"]
        product_sub = config["product_sub"] if config["product_sub"] != "undefined" else None
        app_name = config["app_name"]
        print(f"Using preset configuration for {choice}")
    elif choice == "7":
        print("\n=== Custom Configuration ===")
        user_agent = input("Enter User-Agent string: ").strip()
        product = input("Enter navigator.product (e.g., 'Lynx', 'NetSurf'): ").strip()
        product_sub = input("Enter navigator.productSub (leave empty for undefined): ").strip()
        app_name = input("Enter navigator.appName: ").strip()
        
        product_sub = product_sub if product_sub else None
    else:
        print("Invalid choice. Using default Chrome configuration.")
        config = preset_configs["1"]
        user_agent = config["user_agent"]
        product = config["product"]
        product_sub = config["product_sub"]
        app_name = config["app_name"]
    
    if not user_agent:
        print("No user agent provided. Exiting.")
        return
    
    # Run the test
    test_user_agent_amiunique(user_agent, product, product_sub, app_name)

if __name__ == "__main__":
    # Installation reminder
    print("Make sure you have Playwright installed:")
    print("pip install playwright")
    print("playwright install chromium")
    print("-" * 50)
    
    main()
