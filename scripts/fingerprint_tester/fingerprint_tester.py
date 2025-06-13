import asyncio
import random
import csv
import json
from pathlib import Path
from playwright.async_api import async_playwright
import itertools
from datetime import datetime
import time

class FingerprintTester:
    def __init__(self):
        self.data_files = {
            'user_agents': 'user_agents.txt',
            'screen_resolutions': 'screen_resolutions.txt',
            'timezones': 'timezones.txt',
            'languages': 'languages.txt',
            'platforms': 'platforms.txt'
        }
        self.combinations = []
        self.unique_combinations = []
        
    def load_data_files(self):
        """Load all data from .txt files"""
        data = {}
        for key, filename in self.data_files.items():
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    # Remove empty lines and strip whitespace
                    data[key] = [line.strip() for line in file.readlines() if line.strip()]
                print(f"✅ Loaded {len(data[key])} {key} from {filename}")
            except FileNotFoundError:
                print(f"❌ File {filename} not found! Creating sample file...")
                self.create_sample_file(filename, key)
                data[key] = self.get_sample_data(key)
        return data 
   
    
    def get_weighted_resolution(self, resolutions):
        """Favor less common screen resolutions"""
        common_resolutions = ['1920x1080', '1366x768', '1280x720']
        uncommon_resolutions = [r for r in resolutions if r not in common_resolutions]
        
        # 30% chance of common, 70% chance of uncommon
        if random.random() < 0.3 and common_resolutions:
            return random.choice([r for r in common_resolutions if r in resolutions])
        else:
            return random.choice(uncommon_resolutions if uncommon_resolutions else resolutions)
    
    def get_weighted_timezone(self, timezones):
        """Favor less common timezones"""
        common_timezones = ['America/New_York', 'Europe/London', 'America/Los_Angeles']
        uncommon_timezones = [t for t in timezones if t not in common_timezones]
        
        # 25% chance of common, 75% chance of uncommon
        if random.random() < 0.25 and common_timezones:
            return random.choice([t for t in common_timezones if t in timezones])
        else:
            return random.choice(uncommon_timezones if uncommon_timezones else timezones)
    
    def get_weighted_language(self, languages):
        """Favor less common language combinations"""
        common_languages = ['en-US,en;q=0.9', 'en-GB,en;q=0.9']
        uncommon_languages = [l for l in languages if l not in common_languages]
        
        # 20% chance of common, 80% chance of uncommon
        if random.random() < 0.2 and common_languages:
            return random.choice([l for l in common_languages if l in languages])
        else:
            return random.choice(uncommon_languages if uncommon_languages else languages)
    
    
    def create_sample_file(self, filename, data_type):
        """Create sample files if they don't exist"""
        samples = self.get_sample_data(data_type)
        with open(filename, 'w', encoding='utf-8') as file:
            file.write('\n'.join(samples))
        print(f"📝 Created sample {filename} with {len(samples)} entries")
    
    def get_sample_data(self, data_type):
        """Return sample data for each type"""
        samples = {
            'user_agents': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
            ],
            'screen_resolutions': [
                '1920x1080', '1366x768', '1440x900', '1536x864', '1280x720', '1600x900', '2560x1440'
            ],
            'timezones': [
                'America/New_York', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney', 'America/Los_Angeles'
            ],
            'languages': [
                'en-US,en;q=0.9', 'en-GB,en;q=0.9', 'fr-FR,fr;q=0.9', 'de-DE,de;q=0.9', 'es-ES,es;q=0.9'
            ],
            'platforms': [
                'Win32', 'MacIntel', 'Linux x86_64'
            ]
        }
        return samples.get(data_type, ['sample_data'])
    
    def generate_combinations(self, data, max_combinations=1000):
        """Generate strategic combinations more likely to be unique"""
        combinations = []

        # Generate combinations with bias toward uniqueness
        for _ in range(max_combinations):
            # Use weighted selection for rarer combinations
            combo = {
                'user_agents': random.choice(data['user_agents']),
                'screen_resolutions': self.get_weighted_resolution(data['screen_resolutions']),
                'timezones': self.get_weighted_timezone(data['timezones']),
                'languages': self.get_weighted_language(data['languages']),
                'platforms': random.choice(data['platforms'])
            }

            # Avoid exact duplicates
            if combo not in combinations:
                combinations.append(combo)

        return combinations
    
    async def test_combination(self, browser, combination, test_sites):
        """Test a single combination against fingerprinting sites"""
        try:
            # Parse screen resolution
            width, height = map(int, combination['screen_resolutions'].split('x'))
            
            # Create context with fingerprint settings
            context = await browser.new_context(
                user_agent=combination['user_agents'],
                viewport={'width': width, 'height': height},
                locale=combination['languages'].split(',')[0],
                timezone_id=combination['timezones'],
                extra_http_headers={
                    'Accept-Language': combination['languages']
                }
            )
            
            page = await context.new_page()
            
            # Override platform if needed
            await page.add_init_script(f"""
                Object.defineProperty(navigator, 'platform', {{
                    get: () => '{combination['platforms']}'
                }});
            """)
            
            # Add this after the platform override
            await page.add_init_script(f"""
                // Override more fingerprinting vectors
                Object.defineProperty(navigator, 'hardwareConcurrency', {{
                    get: () => {random.randint(2, 16)}
                }});
                
                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => {random.choice([2, 4, 8, 16])}
                }});
                
                Object.defineProperty(screen, 'colorDepth', {{
                    get: () => {random.choice([24, 30, 32])}
                }});
                
                // WebGL fingerprinting
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                        return '{random.choice(["NVIDIA Corporation", "AMD", "Intel Inc.", "Apple Inc."])}';
                    }}
                    if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL  
                        return '{random.choice(["GeForce GTX 1060", "Radeon RX 580", "Intel Iris Pro", "Apple M1"])}';
                    }}
                    return getParameter.call(this, parameter);
                }};
                
                // Canvas fingerprinting protection
                const getContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type) {{
                    const context = getContext.call(this, type);
                    if (type === '2d') {{
                        const getImageData = context.getImageData;
                        context.getImageData = function(...args) {{
                            const imageData = getImageData.apply(this, args);
                            // Add slight noise to canvas
                            for (let i = 0; i < imageData.data.length; i += 4) {{
                                imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                            }}
                            return imageData;
                        }};
                    }}
                    return context;
                }};
            """)
            
            results = {}
            
            for site_name, site_config in test_sites.items():
                try:
                    print(f"  🔍 Testing {site_name}...")
                    await page.goto(site_config['url'], wait_until='networkidle')
                    
                    # Wait for the site to load and analyze
                    await page.wait_for_timeout(site_config.get('wait_time', 5000))
                    
                    # Extract uniqueness data based on site
                    if site_name == 'amiunique':
                        uniqueness_data = await self.extract_amiunique_data(page)
                    elif site_name == 'coveryourtracks':
                        uniqueness_data = await self.extract_eff_data(page)
                    else:
                        uniqueness_data = await self.extract_generic_data(page)
                    
                    results[site_name] = uniqueness_data
                    
                    # Small delay between tests
                    await page.wait_for_timeout(2000)
                    
                except Exception as e:
                    print(f"    ❌ Error testing {site_name}: {str(e)}")
                    results[site_name] = {'error': str(e)}
            
            await context.close()
            return results
            
        except Exception as e:
            print(f"  ❌ Error with combination: {str(e)}")
            return {'error': str(e)}
        
    async def extract_amiunique_data(self, page):
        """Extract uniqueness data from AmIUnique"""
        try:
            # Wait for results to load
            await page.wait_for_selector('.uniqueness', timeout=10000)
            
            # Extract uniqueness percentage
            uniqueness_element = await page.query_selector('.uniqueness')
            uniqueness_text = await uniqueness_element.inner_text() if uniqueness_element else "0%"
            
            # Extract other metrics if available
            fingerprint_data = await page.evaluate('''
                () => {
                    const data = {};
                    // Try to extract various metrics from the page
                    const uniquenessEl = document.querySelector('.uniqueness');
                    if (uniquenessEl) {
                        data.uniqueness = uniquenessEl.textContent.trim();
                    }
                    return data;
                }
            ''')
            
            return {
                'uniqueness': uniqueness_text,
                'is_unique': 'unique' in uniqueness_text.lower() or float(uniqueness_text.replace('%', '')) > 95,
                'raw_data': fingerprint_data
            }
        except Exception as e:
            return {'error': f'AmIUnique extraction failed: {str(e)}'}
    
    async def extract_eff_data(self, page):
        """Extract uniqueness data from EFF Cover Your Tracks"""
        try:
            # Wait for results
            await page.wait_for_timeout(8000)
            
            # Extract tracking protection results
            tracking_data = await page.evaluate('''
                () => {
                    const data = {};
                    // Look for tracking protection indicators
                    const results = document.querySelectorAll('.result, .test-result');
                    results.forEach((result, index) => {
                        data[`result_${index}`] = result.textContent.trim();
                    });
                    return data;
                }
            ''')
            
            # Determine if fingerprint is unique based on EFF's results
            is_unique = any('unique' in str(value).lower() for value in tracking_data.values())
            
            return {
                'tracking_protection': tracking_data,
                'is_unique': is_unique,
                'raw_data': tracking_data
            }
        except Exception as e:
            return {'error': f'EFF extraction failed: {str(e)}'}
    
    async def extract_generic_data(self, page):
        """Generic extraction for other fingerprinting sites"""
        try:
            # Generic approach - look for common indicators
            content = await page.content()
            
            # Look for uniqueness indicators in the page content
            uniqueness_keywords = ['unique', 'identifiable', 'fingerprint', 'tracking']
            is_unique = any(keyword in content.lower() for keyword in uniqueness_keywords)
            
            return {
                'content_length': len(content),
                'is_unique': is_unique,
                'raw_data': 'Generic extraction completed'
            }
        except Exception as e:
            return {'error': f'Generic extraction failed: {str(e)}'}
    
    async def run_tests(self, max_combinations=100, max_concurrent=5):
        """Main function to run all tests"""
        print("🚀 Starting Browser Fingerprint Combination Tester")
        print("=" * 60)
        
        # Load data files
        data = self.load_data_files()
        
        # Generate combinations
        combinations = self.generate_combinations(data, max_combinations)
        
        # Define test sites
        test_sites = {
            'amiunique': {
                'url': 'https://amiunique.org/fp',
                'wait_time': 8000
            },
            'coveryourtracks': {
                'url': 'https://coveryourtracks.eff.org/',
                'wait_time': 10000
            }
        }
        
        print(f"\n🧪 Testing {len(combinations)} combinations on {len(test_sites)} sites")
        print(f"🔄 Running {max_concurrent} tests concurrently")
        print("=" * 60)
        
        async with async_playwright() as playwright:
            # Launch browser
            browser = await playwright.chromium.launch(
                headless=True,  # Set to False if you want to see the browser
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
            )
            
            # Process combinations in batches
            unique_combinations = []
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def test_single_combination(combo_index, combination):
                async with semaphore:
                    print(f"\n🔄 Testing combination {combo_index + 1}/{len(combinations)}")
                    print(f"   UA: {combination['user_agents'][:50]}...")
                    print(f"   Resolution: {combination['screen_resolutions']}")
                    print(f"   Timezone: {combination['timezones']}")
                    
                    results = await self.test_combination(browser, combination, test_sites)
                    
                    # Determine if combination is unique
                    is_unique = False
                    uniqueness_scores = []
                    
                    for site, result in results.items():
                        if 'error' not in result:
                            if result.get('is_unique', False):
                                is_unique = True
                            if 'uniqueness' in result:
                                uniqueness_scores.append(result['uniqueness'])
                    
                    if is_unique:
                        combination_result = {
                            'combination_id': combo_index + 1,
                            'timestamp': datetime.now().isoformat(),
                            'is_unique': True,
                            'test_results': results,
                            **combination
                        }
                        unique_combinations.append(combination_result)
                        print(f"   ✅ UNIQUE combination found! (Total unique: {len(unique_combinations)})")
                    else:
                        print(f"   ❌ Not unique")
                    
                    # Small delay between tests to be respectful
                    await asyncio.sleep(1)
            
            # Run all tests
            tasks = [
                test_single_combination(i, combo) 
                for i, combo in enumerate(combinations)
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            await browser.close()
        
        # Save results
        await self.save_results(unique_combinations)
        
        print(f"\n🎉 Testing completed!")
        print(f"📊 Total combinations tested: {len(combinations)}")
        print(f"✅ Unique combinations found: {len(unique_combinations)}")
        print(f"📁 Results saved to unique_fingerprints.csv")
    
    async def save_results(self, unique_combinations):
        """Save unique combinations to CSV"""
        if not unique_combinations:
            print("❌ No unique combinations found to save")
            return
        
        # Prepare CSV data
        csv_filename = f"unique_fingerprints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'combination_id', 'timestamp', 'is_unique',
                'user_agents', 'screen_resolutions', 'timezones', 
                'languages', 'platforms', 'test_results_json'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for combo in unique_combinations:
                row = {
                    'combination_id': combo['combination_id'],
                    'timestamp': combo['timestamp'],
                    'is_unique': combo['is_unique'],
                    'user_agents': combo['user_agents'],
                    'screen_resolutions': combo['screen_resolutions'],
                    'timezones': combo['timezones'],
                    'languages': combo['languages'],
                    'platforms': combo['platforms'],
                    'test_results_json': json.dumps(combo['test_results'])
                }
                writer.writerow(row)
        
        print(f"💾 Saved {len(unique_combinations)} unique combinations to {csv_filename}")

# Main execution
if __name__ == "__main__":
    tester = FingerprintTester()
    
    # Configuration
    MAX_COMBINATIONS = 50  # Adjust this number
    MAX_CONCURRENT = 3     # How many browsers to run at once
    
    # Run the tests
    asyncio.run(tester.run_tests(MAX_COMBINATIONS, MAX_CONCURRENT))
