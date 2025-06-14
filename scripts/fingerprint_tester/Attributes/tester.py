import asyncio
import random
import csv
import json
from pathlib import Path
from playwright.async_api import async_playwright
import itertools
from datetime import datetime
import time
import re

class AdvancedFingerprintTester:
    def __init__(self):
        self.data_files = {
            'user_agents': 'user_agents.txt',
            'screen_resolutions': 'screen_resolutions.txt',
            'timezones': 'timezones.txt',
            'flash_plugins': 'flash_plugins.json',
            'languages': 'languages.txt',
            'platforms': 'platforms.txt',
            'flash_languages': 'flash_languages.txt',
            'flash_platforms': 'flash_platform.txt',
            'fonts': 'fonts.txt',
            'webgl_vendor_renderer': 'webgl_vendor_renderer.txt'
        }
        self.combinations = []
    
    
    def get_random_flash_plugins(self, flash_plugins, min_plugins=0, max_plugins=3):
        """Generate a realistic subset of browser plugins"""
        if not flash_plugins or not isinstance(flash_plugins, list):
            return []

        if len(flash_plugins) == 0:
            return []

        num_plugins = random.randint(min_plugins, min(max_plugins, len(flash_plugins)))
        if num_plugins == 0:
            return []

        # Use random.choices instead of random.sample to handle edge cases
        if num_plugins >= len(flash_plugins):
            return flash_plugins.copy()
        else:
            selected_plugins = random.sample(flash_plugins, num_plugins)
            return selected_plugins 
        
    def load_data_files(self):
        """Load all data from .txt files"""
        data = {}
        for key, filename in self.data_files.items():
            try:
                if filename.endswith('.json'):
                    with open(filename, 'r', encoding='utf-8') as file:
                        json_data = json.load(file)
                        if key == 'flash_plugins' and 'flash_plugins' in json_data:
                            data[key] = json_data['flash_plugins']  # Extract the array
                        else:
                            data[key] = json_data
                    print(f"✅ Loaded {len(data[key])} {key} from {filename}")
                else:
                    with open(filename, 'r', encoding='utf-8') as file:
                        data[key] = [line.strip() for line in file.readlines() if line.strip()]
                    print(f"✅ Loaded {len(data[key])} {key} from {filename}")
            except FileNotFoundError:
                print(f"❌ File {filename} not found! Creating sample file...")
                self.create_sample_file(filename, key)
                data[key] = self.get_sample_data(key)
        return data
    
    def get_weighted_resolution(self, resolutions):
        """Favor uncommon screen resolutions for uniqueness"""
        common_resolutions = ['1920x1080', '1366x768', '1280x720', '1536x864']
        uncommon_resolutions = [r for r in resolutions if r not in common_resolutions]
        
        # 20% chance of common, 80% chance of uncommon for maximum uniqueness
        if random.random() < 0.2 and common_resolutions:
            return random.choice([r for r in common_resolutions if r in resolutions])
        else:
            return random.choice(uncommon_resolutions if uncommon_resolutions else resolutions)
    
    def get_weighted_timezone(self, timezones):
        """Favor uncommon timezones"""
        common_timezones = ['America/New_York', 'Europe/London', 'America/Los_Angeles', 'UTC']
        uncommon_timezones = [t for t in timezones if t not in common_timezones]
        
        # 15% chance of common, 85% chance of uncommon
        if random.random() < 0.15 and common_timezones:
            return random.choice([t for t in common_timezones if t in timezones])
        else:
            return random.choice(uncommon_timezones if uncommon_timezones else timezones)
    
    def get_weighted_language(self, languages):
        """Favor uncommon language combinations"""
        common_languages = ['en-US,en;q=0.9', 'en-GB,en;q=0.9', 'en,en-US;q=0.9']
        uncommon_languages = [l for l in languages if l not in common_languages]
        
        # 10% chance of common, 90% chance of uncommon
        if random.random() < 0.1 and common_languages:
            return random.choice([l for l in common_languages if l in languages])
        else:
            return random.choice(uncommon_languages if uncommon_languages else languages)
    
    def get_random_font_subset(self, fonts, min_fonts=20, max_fonts=50):
        """Generate a realistic subset of installed fonts"""
        # Always include some common fonts
        common_fonts = ['Arial', 'Times New Roman', 'Helvetica', 'Georgia', 'Verdana']
        available_common = [f for f in fonts if any(common in f for common in common_fonts)]
        
        # Select random subset
        num_fonts = random.randint(min_fonts, min(max_fonts, len(fonts)))
        selected_fonts = random.sample(fonts, min(num_fonts, len(fonts)))
        
        # Ensure some common fonts are included
        if available_common:
            selected_fonts.extend(random.sample(available_common, min(3, len(available_common))))
        
        return list(set(selected_fonts))  # Remove duplicates
    
    def parse_webgl_data(self, webgl_data):
        """Parse WebGL vendor/renderer data"""
        vendors = []
        renderers = []
        
        for line in webgl_data:
            if '|' in line:
                vendor, renderer = line.split('|', 1)
                vendors.append(vendor.strip())
                renderers.append(renderer.strip())
            else:
                # Fallback if format is different
                vendors.append(line.strip())
                renderers.append(line.strip())
        
        return vendors, renderers
    
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
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
            ],
            'screen_resolutions': [
                '1920x1080', '2560x1440', '1366x768', '1440x900', '1280x720', '3840x2160', '1600x900'
            ],
            'timezones': [
                'Africa/Abidjan', 'Asia/Kolkata', 'Europe/Berlin', 'America/Argentina/Buenos_Aires', 'Pacific/Auckland'
            ],
            'languages': [
                'en-US,en;q=0.9', 'fr-FR,fr;q=0.9,en;q=0.8', 'de-DE,de;q=0.9', 'ja-JP,ja;q=0.9', 'zh-CN,zh;q=0.9'
            ],
            'platforms': [
                'Linux x86_64', 'Win32', 'MacIntel', 'Linux armv7l'
            ],
            'flash_languages': [
                'akk', 'en', 'fr', 'de', 'ja'
            ],
            'flash_platforms': [
                'Windows CE 5.0', 'Linux', 'Mac OS', 'Windows 10'
            ],
            'fonts': [
                'Arial', 'Helvetica', 'Times New Roman', 'Georgia', 'Verdana', 'Comic Sans MS', 'Impact'
            ],
            'webgl_vendor_renderer': [
                'NVIDIA Corporation|GeForce GTX 1060',
                'AMD|Radeon RX 580',
                'Intel Inc.|Intel Iris Pro',
                'Apple Inc.|Apple M1'
            ],
            'flash_plugins': [
                    {
                        "name": "Shockwave Flash",
                        "description": "Shockwave Flash 32.0 r0",
                        "filename": "pepflashplayer.dll",
                        "version": "32.0.0.387",
                        "mimeTypes": ["application/x-shockwave-flash"]
                    },
                    {
                        "name": "Java Platform SE 8",
                        "description": "Java Platform SE 8 U371",
                        "filename": "npjp2.dll", 
                        "version": "11.371.2",
                        "mimeTypes": ["application/x-java-applet"]
                    },
                    {
                        "name": "Adobe Acrobat",
                        "description": "Adobe Acrobat Plug-In Version 23.003.20201",
                        "filename": "nppdf32.dll",
                        "version": "23.003.20201",
                        "mimeTypes": ["application/pdf"]
                    }
                ]
        }
        return samples.get(data_type, ['sample_data'])
    
    def generate_advanced_combinations(self, data, max_combinations=100):
        """Generate advanced combinations targeting maximum uniqueness"""
        combinations = []
        
        # Parse WebGL data
        vendors, renderers = self.parse_webgl_data(data['webgl_vendor_renderer'])
        
        for _ in range(max_combinations):
            # Generate unique font subset for each combination
            font_subset = self.get_random_font_subset(data['fonts'])
            
            combo = {
                'user_agent': random.choice(data['user_agents']),
                'screen_resolution': self.get_weighted_resolution(data['screen_resolutions']),
                'timezone': self.get_weighted_timezone(data['timezones']),
                'language': self.get_weighted_language(data['languages']),
                'platform': random.choice(data['platforms']),
                'flash_language': random.choice(data['flash_languages']),
                'flash_platform': random.choice(data['flash_platforms']),
                'fonts': font_subset,
                'webgl_vendor': random.choice(vendors),
                'webgl_renderer': random.choice(renderers),
                'hardware_concurrency': random.randint(2, 32),
                'device_memory': random.choice([0.25, 0.5, 1, 2, 4, 8, 16, 32]),
                'color_depth': random.choice([16, 24, 30, 32, 48]),
                'pixel_ratio': random.choice([1, 1.25, 1.5, 2, 2.5, 3]),
                'max_touch_points': random.choice([0, 1, 2, 5, 10]),
                'canvas_noise': random.randint(1, 10),  # Level of canvas noise to add
                'webgl_noise': random.randint(1, 5),    # Level of WebGL noise
                'flash_plugins': self.get_random_flash_plugins(data['flash_plugins'])
            }
            
            # Avoid exact duplicates
            if combo not in combinations:
                combinations.append(combo)
        
        return combinations
    
    async def test_advanced_combination(self, browser, combination, test_sites):
        """Test an advanced combination with comprehensive fingerprint spoofing"""
        try:
            # Parse screen resolution
            width, height = map(int, combination['screen_resolution'].split('x'))
            
            # Create context with enhanced fingerprint settings
            context = await browser.new_context(
                user_agent=combination['user_agent'],
                viewport={'width': width, 'height': height},
                locale=combination['language'].split(',')[0],
                timezone_id=combination['timezone'],
                device_scale_factor=combination['pixel_ratio'],
                java_script_enabled=True,
                extra_http_headers={
                    'Accept-Language': combination['language']
                }
            )
            
            page = await context.new_page()
            
            # Comprehensive fingerprint spoofing script
            await page.add_init_script(f"""
                // Platform override
                Object.defineProperty(navigator, 'platform', {{
                    get: () => '{combination['platform']}'
                }});
                
                // Hardware specs
                Object.defineProperty(navigator, 'hardwareConcurrency', {{
                    get: () => {combination['hardware_concurrency']}
                }});
                
                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => {combination['device_memory']}
                }});
                
                Object.defineProperty(navigator, 'maxTouchPoints', {{
                    get: () => {combination['max_touch_points']}
                }});
                
                // Screen properties
                Object.defineProperty(screen, 'colorDepth', {{
                    get: () => {combination['color_depth']}
                }});
                
                Object.defineProperty(screen, 'pixelDepth', {{
                    get: () => {combination['color_depth']}
                }});
                
                // Flash plugin simulation
                # Dynamic Flash plugins simulation
                const flashPluginsData = {json.dumps(combination['flash_plugins'])};

                if (flashPluginsData && flashPluginsData.length > 0) {{
                    Object.defineProperty(navigator, 'plugins', {{
                        get: () => {{
                            const plugins = flashPluginsData.map(plugin => ({{
                                name: plugin.name,
                                description: plugin.description,
                                filename: plugin.filename,
                                version: plugin.version,
                                length: plugin.mimeTypes ? plugin.mimeTypes.length : 1
                            }}));
                            return plugins;
                        }}
                    }});
                }} else {{
                    Object.defineProperty(navigator, 'plugins', {{
                        get: () => []
                    }});
                }}

                // Flash language and platform
                window.flashLanguage = '{combination['flash_language']}';
                window.flashPlatform = '{combination['flash_platform']}';

                // Font detection spoofing
                const availableFonts = {json.dumps(combination['fonts'])};
                const originalMeasureText = CanvasRenderingContext2D.prototype.measureText;
                CanvasRenderingContext2D.prototype.measureText = function(text) {{
                    // Simulate different font metrics based on available fonts
                    const result = originalMeasureText.call(this, text);
                    if (this.font && !availableFonts.some(font => this.font.includes(font))) {{
                        // Slightly modify metrics for unavailable fonts
                        result.width *= 0.95 + Math.random() * 0.1;
                    }}
                    return result;
                }};
                
                // WebGL fingerprinting with custom vendor/renderer
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                        return '{combination['webgl_vendor']}';
                    }}
                    if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL  
                        return '{combination['webgl_renderer']}';
                    }}
                    return getParameter.call(this, parameter);
                }};
                
                // Canvas fingerprinting with controlled noise
                const getContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type) {{
                    const context = getContext.call(this, type);
                    if (type === '2d') {{
                        const getImageData = context.getImageData;
                        context.getImageData = function(...args) {{
                            const imageData = getImageData.apply(this, args);
                            // Add controlled noise based on canvas_noise level
                            const noiseLevel = {combination['canvas_noise']};
                            for (let i = 0; i < imageData.data.length; i += 4) {{
                                imageData.data[i] += Math.floor(Math.random() * noiseLevel) - (noiseLevel/2);
                                imageData.data[i+1] += Math.floor(Math.random() * noiseLevel) - (noiseLevel/2);
                                imageData.data[i+2] += Math.floor(Math.random() * noiseLevel) - (noiseLevel/2);
                            }}
                            return imageData;
                        }};
                    }}
                    return context;
                }};
                
                // Audio context fingerprinting noise
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (AudioContext) {{
                    const originalCreateOscillator = AudioContext.prototype.createOscillator;
                    AudioContext.prototype.createOscillator = function() {{
                        const oscillator = originalCreateOscillator.call(this);
                        const originalFrequency = oscillator.frequency;
                        // Add slight frequency variation
                        Object.defineProperty(oscillator, 'frequency', {{
                            get: () => {{
                                const variation = 1 + (Math.random() - 0.5) * 0.0001;
                                return originalFrequency.value * variation;
                            }}
                        }});
                        return oscillator;
                    }};
                }}
                
                // Override Date timezone for consistency
                const originalDate = Date;
                Date = function(...args) {{
                    if (args.length === 0) {{
                        return new originalDate();
                    }}
                    return new originalDate(...args);
                }};
                Date.prototype = originalDate.prototype;
                
                // Battery API spoofing (if available)
                if (navigator.getBattery) {{
                    navigator.getBattery = async () => ({{
                        charging: {random.choice(['true', 'false'])},
                        chargingTime: {random.randint(3600, 14400)},
                        dischargingTime: {random.randint(7200, 28800)},
                        level: {random.uniform(0.1, 1.0):.2f}
                    }});
                }}
            """)
            
            results = {}
            
            for site_name, site_config in test_sites.items():
                try:
                    print(f"  🔍 Testing {site_name}...")
                    await page.goto(site_config['url'], wait_until='networkidle', timeout=30000)
                    
                    # Wait for the site to load and analyze
                    await page.wait_for_timeout(site_config.get('wait_time', 8000))
                    
                    # Extract uniqueness data based on site
                    if site_name == 'amiunique':
                        uniqueness_data = await self.extract_amiunique_data(page)
                    elif site_name == 'coveryourtracks':
                        uniqueness_data = await self.extract_eff_data(page)
                    elif site_name == 'deviceinfo':
                        uniqueness_data = await self.extract_deviceinfo_data(page)
                    elif site_name == 'browserleaks':
                        uniqueness_data = await self.extract_browserleaks_data(page)
                    else:
                        uniqueness_data = await self.extract_generic_data(page)
                    
                    await page.wait_for_timeout(5000)  # Wait 10 seconds to view results
                    results[site_name] = uniqueness_data
                    
                    # Small delay between tests
                    await page.wait_for_timeout(3000)
                    
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
            await page.wait_for_timeout(5000)
            
            # Try multiple selectors for uniqueness
            uniqueness_data = await page.evaluate('''
                () => {
                    const data = {};
                    
                    // Look for uniqueness percentage
                    const uniquenessSelectors = [
                        '.uniqueness',
                        '[data-uniqueness]',
                        '.percentage',
                        '.result-percentage'
                    ];
                    
                    for (const selector of uniquenessSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            data.uniqueness = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // Look for "bits of information" or entropy
                    const entropyElement = document.querySelector('.entropy, .bits, [data-entropy]');
                    if (entropyElement) {
                        data.entropy = entropyElement.textContent.trim();
                    }
                    
                    // Get page content for analysis
                    data.pageText = document.body.textContent.toLowerCase();
                    
                    return data;
                }
            ''')
            
            # Parse uniqueness percentage
            uniqueness_percent = 0
            if uniqueness_data.get('uniqueness'):
                percent_match = re.search(r'(\d+(?:\.\d+)?)%', uniqueness_data['uniqueness'])
                if percent_match:
                    uniqueness_percent = float(percent_match.group(1))
            
            # Check for uniqueness indicators in page text
            page_text = uniqueness_data.get('pageText', '')
            is_unique = (
                uniqueness_percent > 95 or
                'unique' in page_text or
                'one in' in page_text or
                'identifiable' in page_text
            )
            
            return {
                'site': 'AmIUnique',
                'uniqueness_percentage': uniqueness_percent,
                'is_unique': is_unique,
                'entropy': uniqueness_data.get('entropy', ''),
                'raw_data': uniqueness_data.get('uniqueness', 'No data found')
            }
        except Exception as e:
            return {'site': 'AmIUnique', 'error': f'Extraction failed: {str(e)}'}
    
    async def extract_eff_data(self, page):
        """Extract uniqueness data from EFF Cover Your Tracks"""
        try:
            await page.wait_for_timeout(8000)
            
            tracking_data = await page.evaluate('''
                () => {
                    const data = {};
                    
                    // Look for fingerprint results
                    const resultElements = document.querySelectorAll('.result, .test-result, .fingerprint-result');
                    resultElements.forEach((element, index) => {
                        data[`result_${index}`] = element.textContent.trim();
                    });
                    
                    // Look for uniqueness indicators
                    data.pageText = document.body.textContent.toLowerCase();
                    
                    return data;
                }
            ''')
            
            page_text = tracking_data.get('pageText', '')
            is_unique = (
                'unique' in page_text or
                'fingerprint' in page_text or
                'identifiable' in page_text or
                'one in' in page_text
            )
            
            return {
                'site': 'EFF Cover Your Tracks',
                'is_unique': is_unique,
                'tracking_protection': tracking_data,
                'raw_data': tracking_data
            }
        except Exception as e:
            return {'site': 'EFF Cover Your Tracks', 'error': f'Extraction failed: {str(e)}'}
    
    async def extract_deviceinfo_data(self, page):
        """Extract data from Device Info site"""
        try:
            await page.wait_for_timeout(5000)
            
            device_data = await page.evaluate('''
                () => {
                    const data = {};
                    data.pageText = document.body.textContent.toLowerCase();
                    
                    // Look for fingerprint or uniqueness indicators
                    const infoElements = document.querySelectorAll('.info, .device-info, .fingerprint');
                    infoElements.forEach((element, index) => {
                        data[`info_${index}`] = element.textContent.trim();
                    });
                    
                    return data;
                }
            ''')
            
            page_text = device_data.get('pageText', '')
            is_unique = 'unique' in page_text or 'fingerprint' in page_text
            
            return {
                'site': 'Device Info',
                'is_unique': is_unique,
                'device_data': device_data,
                'raw_data': device_data
            }
        except Exception as e:
            return {'site': 'Device Info', 'error': f'Extraction failed: {str(e)}'}
    
    async def extract_browserleaks_data(self, page):
        """Extract data from BrowserLeaks"""
        try:
            await page.wait_for_timeout(6000)
            
            browser_data = await page.evaluate('''
                () => {
                    const data = {};
                    data.pageText = document.body.textContent.toLowerCase();
                    
                    // Look for leak indicators
                    const leakElements = document.querySelectorAll('.leak, .fingerprint, .result');
                    leakElements.forEach((element, index) => {
                        data[`leak_${index}`] = element.textContent.trim();
                    });
                    
                    return data;
                }
            ''')
            
            page_text = browser_data.get('pageText', '')
            is_unique = 'unique' in page_text or 'identifiable' in page_text
            
            return {
                'site': 'BrowserLeaks',
                'is_unique': is_unique,
                'browser_data': browser_data,
                'raw_data': browser_data
            }
        except Exception as e:
            return {'site': 'BrowserLeaks', 'error': f'Extraction failed: {str(e)}'}
    
    async def extract_generic_data(self, page):
        """Generic extraction for other fingerprinting sites"""
        try:
            content = await page.content()
            page_text = content.lower()
            
            # Look for uniqueness indicators
            uniqueness_keywords = ['unique', 'identifiable', 'fingerprint', 'one in', 'bits of information']
            uniqueness_score = sum(page_text.count(keyword) for keyword in uniqueness_keywords)
            is_unique = uniqueness_score > 2
            
            return {
                'site': 'Generic',
                'content_length': len(content),
                'uniqueness_score': uniqueness_score,
                'is_unique': is_unique,
                'raw_data': f'Uniqueness score: {uniqueness_score}'
            }
        except Exception as e:
            return {'site': 'Generic', 'error': f'Extraction failed: {str(e)}'}
    
    async def run_advanced_tests(self, max_combinations=50, max_concurrent=3):
        """Main function to run advanced fingerprint tests"""
        print("🚀 Starting Advanced Browser Fingerprint Uniqueness Tester")
        print("🎯 Goal: Find the most unique browser fingerprint possible")
        print("=" * 70)
        
        # Load all data files
        data = self.load_data_files()
        
        # Generate advanced combinations
        combinations = self.generate_advanced_combinations(data, max_combinations)
        
        # Define comprehensive test sites
        test_sites = {
            'amiunique': {
                'url': 'https://amiunique.org/fingerprint',
                'wait_time': 10000
            },
            'coveryourtracks': {
                'url': 'https://coveryourtracks.eff.org/',
                'wait_time': 12000
            },
            'deviceinfo': {
                'url': 'https://www.deviceinfo.me/',
                'wait_time': 8000
            },
            'browserleaks': {
                'url': 'https://browserleaks.com/canvas',
                'wait_time': 10000
            }
        }
        
        print(f"\n🧪 Testing {len(combinations)} advanced combinations on {len(test_sites)} sites")
        print(f"🔄 Running {max_concurrent} tests concurrently")
        print("📊 Tracking uniqueness percentages and entropy scores")
        print("=" * 70)
        
        async with async_playwright() as playwright:
            # Launch browser with anti-detection features
            browser = await playwright.chromium.launch(
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            
            # Process combinations and track best results
            unique_combinations = []
            best_combinations = []
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def test_single_combination(combo_index, combination):
                async with semaphore:
                    print(f"\n🔄 Testing combination {combo_index + 1}/{len(combinations)}")
                    print(f"   UA: {combination['user_agent'][:60]}...")
                    print(f"   Resolution: {combination['screen_resolution']}")
                    print(f"   Timezone: {combination['timezone']}")
                    print(f"   WebGL: {combination['webgl_vendor']} - {combination['webgl_renderer']}")
                    print(f"   Fonts: {len(combination['fonts'])} fonts loaded")
                    
                    results = await self.test_advanced_combination(browser, combination, test_sites)
                    
                    # Analyze results for uniqueness
                    uniqueness_scores = []
                    is_unique = False
                    best_score = 0
                    
                    for site, result in results.items():
                        if 'error' not in result:
                            if result.get('is_unique', False):
                                is_unique = True
                            
                            # Extract numeric scores
                            if 'uniqueness_percentage' in result:
                                score = result['uniqueness_percentage']
                                uniqueness_scores.append(score)
                                best_score = max(best_score, score)
                    
                    # Calculate average uniqueness
                    avg_uniqueness = sum(uniqueness_scores) / len(uniqueness_scores) if uniqueness_scores else 0
                    
                    combination_result = {
                        'combination_id': combo_index + 1,
                        'timestamp': datetime.now().isoformat(),
                        'is_unique': is_unique,
                        'best_uniqueness_score': best_score,
                        'average_uniqueness': avg_uniqueness,
                        'test_results': results,
                        'fingerprint_config': combination
                    }
                    
                    # Track best performing combinations
                    if avg_uniqueness > 90 or is_unique:
                        unique_combinations.append(combination_result)
                        print(f"   ✅ HIGH UNIQUENESS! Avg: {avg_uniqueness:.1f}% Best: {best_score:.1f}%")
                    else:
                        print(f"   📊 Uniqueness: Avg: {avg_uniqueness:.1f}% Best: {best_score:.1f}%")
                    
                    # Keep track of top 10 combinations
                    best_combinations.append(combination_result)
                    best_combinations.sort(key=lambda x: x['average_uniqueness'], reverse=True)
                    best_combinations = best_combinations[:10]
                    
                    # Respectful delay
                    await asyncio.sleep(2)
            
            # Run all tests
            tasks = [
                test_single_combination(i, combo) 
                for i, combo in enumerate(combinations)
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await browser.close()
        
        # Save comprehensive results
        await self.save_advanced_results(unique_combinations, best_combinations)
        
        # Print summary
        print(f"\n🎉 Advanced Testing Completed!")
        print(f"📊 Total combinations tested: {len(combinations)}")
        print(f"✅ High uniqueness combinations found: {len(unique_combinations)}")
        print(f"🏆 Best average uniqueness: {best_combinations[0]['average_uniqueness']:.1f}%" if best_combinations else "No results")
        print(f"📁 Results saved to CSV files")
        
        # Print top 3 combinations
        if best_combinations:
            print(f"\n🏆 TOP 3 MOST UNIQUE COMBINATIONS:")
            print("=" * 50)
            for i, combo in enumerate(best_combinations[:3], 1):
                print(f"\n#{i} - Average Uniqueness: {combo['average_uniqueness']:.1f}%")
                config = combo['fingerprint_config']
                print(f"   🌐 User Agent: {config['user_agent'][:80]}...")
                print(f"   📺 Resolution: {config['screen_resolution']}")
                print(f"   🌍 Timezone: {config['timezone']}")
                print(f"   🔧 Platform: {config['platform']}")
                print(f"   🎨 WebGL: {config['webgl_vendor']} - {config['webgl_renderer']}")
                print(f"   📝 Languages: {config['language']}")
                print(f"   🎯 Hardware Concurrency: {config['hardware_concurrency']}")
                print(f"   💾 Device Memory: {config['device_memory']}GB")
                print(f"   🎪 Flash Enabled: {config['flash_enabled']}")
                print(f"   📚 Fonts Available: {len(config['fonts'])}")
    
    async def save_advanced_results(self, unique_combinations, best_combinations):
        """Save comprehensive results to CSV files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save unique combinations
        if unique_combinations:
            unique_csv = f"unique_fingerprints_{timestamp}.csv"
            with open(unique_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'combination_id', 'timestamp', 'is_unique', 'best_uniqueness_score',
                    'average_uniqueness', 'user_agent', 'screen_resolution', 'timezone',
                    'language', 'platform', 'flash_language', 'flash_platform', 'fonts_count',
                    'webgl_vendor', 'webgl_renderer', 'hardware_concurrency', 'device_memory',
                    'color_depth', 'pixel_ratio', 'max_touch_points', 'flash_plugins_count',
                    'test_results_json'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for combo in unique_combinations:
                    config = combo['fingerprint_config']
                    row = {
                        'combination_id': combo['combination_id'],
                        'timestamp': combo['timestamp'],
                        'is_unique': combo['is_unique'],
                        'best_uniqueness_score': combo['best_uniqueness_score'],
                        'average_uniqueness': combo['average_uniqueness'],
                        'user_agent': config['user_agent'],
                        'screen_resolution': config['screen_resolution'],
                        'timezone': config['timezone'],
                        'language': config['language'],
                        'platform': config['platform'],
                        'flash_language': config['flash_language'],
                        'flash_platform': config['flash_platform'],
                        'fonts_count': len(config['fonts']),
                        'webgl_vendor': config['webgl_vendor'],
                        'webgl_renderer': config['webgl_renderer'],
                        'hardware_concurrency': config['hardware_concurrency'],
                        'device_memory': config['device_memory'],
                        'color_depth': config['color_depth'],
                        'pixel_ratio': config['pixel_ratio'],
                        'max_touch_points': config['max_touch_points'],
                        'flash_plugins_count': len(config['flash_plugins']),
                        'test_results_json': json.dumps(combo['test_results'])
                    }
                    writer.writerow(row)
            
            print(f"💾 Saved {len(unique_combinations)} unique combinations to {unique_csv}")
        
        # Save top combinations
        if best_combinations:
            best_csv = f"best_fingerprints_{timestamp}.csv"
            with open(best_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'rank', 'combination_id', 'average_uniqueness', 'best_uniqueness_score',
                    'user_agent', 'screen_resolution', 'timezone', 'language', 'platform',
                    'webgl_vendor', 'webgl_renderer', 'hardware_concurrency', 'device_memory',
                    'fonts_list', 'full_config_json'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for rank, combo in enumerate(best_combinations, 1):
                    config = combo['fingerprint_config']
                    row = {
                        'rank': rank,
                        'combination_id': combo['combination_id'],
                        'average_uniqueness': combo['average_uniqueness'],
                        'best_uniqueness_score': combo['best_uniqueness_score'],
                        'user_agent': config['user_agent'],
                        'screen_resolution': config['screen_resolution'],
                        'timezone': config['timezone'],
                        'language': config['language'],
                        'platform': config['platform'],
                        'webgl_vendor': config['webgl_vendor'],
                        'webgl_renderer': config['webgl_renderer'],
                        'hardware_concurrency': config['hardware_concurrency'],
                        'device_memory': config['device_memory'],
                        'fonts_list': '|'.join(config['fonts'][:20]),  # First 20 fonts
                        'full_config_json': json.dumps(config)
                    }
                    writer.writerow(row)
            
            print(f"💾 Saved top {len(best_combinations)} combinations to {best_csv}")
    
    def print_usage_instructions(self):
        """Print instructions for using the most unique fingerprint"""
        print(f"\n📋 HOW TO USE YOUR MOST UNIQUE FINGERPRINT:")
        print("=" * 60)
        print("1. Check the generated CSV files for the best combinations")
        print("2. Use the #1 ranked combination for maximum uniqueness")
        print("3. Apply these settings in your browser automation:")
        print("   - User Agent: Copy from 'user_agent' column")
        print("   - Screen Resolution: Set viewport to 'screen_resolution'")
        print("   - Timezone: Set to 'timezone' value")
        print("   - Language: Set Accept-Language header")
        print("   - WebGL: Spoof vendor/renderer values")
        print("   - Canvas: Add controlled noise")
        print("4. Monitor your uniqueness periodically as web tracking evolves")
        print("\n⚠️  IMPORTANT: Use responsibly and respect website terms of service")

# Enhanced main execution
if __name__ == "__main__":
    tester = AdvancedFingerprintTester()
    
    # Print welcome message
    print("🎯 Advanced Browser Fingerprint Uniqueness Tester")
    print("🔍 Testing combinations to maximize browser uniqueness")
    print("📊 Using comprehensive fingerprinting data")
    print("=" * 60)
    
    # Configuration - Adjust 1  these values
    MAX_COMBINATIONS = 75    # Number of combinations to test
    MAX_CONCURRENT = 1  
    
    print(f"⚙️  Configuration:")
    print(f"   📊 Testing {MAX_COMBINATIONS} combinations")
    print(f"   🔄 {MAX_CONCURRENT} concurrent tests")
    print(f"   🎯 Goal: Find maximum uniqueness percentages")
    print("=" * 60)
    
    # Run the advanced tests
    try:
        asyncio.run(tester.run_advanced_tests(MAX_COMBINATIONS, MAX_CONCURRENT))
        tester.print_usage_instructions()
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        print("💡 Make sure all required .txt files are present in the directory")