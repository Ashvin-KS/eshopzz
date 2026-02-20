"""
ShopSync Scraper - Amazon and Flipkart Price Aggregator
=========================================================
Uses Selenium with anti-detection settings to scrape product data
from both e-commerce sites. Based on analyzed selectors.
"""

import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from bs4 import BeautifulSoup
import torch
from sentence_transformers import SentenceTransformer, util

_SERVICE = None
_MODEL = None
_MODEL_LOADED = False

def preload_model():
    """Preload the Transformer model at startup for instant matching."""
    global _MODEL, _MODEL_LOADED
    if not _MODEL_LOADED:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[AI] Preloading transformer model on {device}...")
        _MODEL = SentenceTransformer('all-mpnet-base-v2', device=device)
        # Warm up the model with a dummy encode
        _MODEL.encode(["warmup"], convert_to_tensor=True)
        _MODEL_LOADED = True
        print(f"[AI] Model ready on {device.upper()}!")
    return _MODEL

def get_model():
    """Get the preloaded model (or load if not ready)."""
    global _MODEL
    if _MODEL is None:
        return preload_model()
    return _MODEL

def get_chrome_driver():
    """Configure Chrome with anti-detection settings."""
    global _SERVICE
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Disable automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Performance optimization: Block images and CSS
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.cookies": 2,
        "profile.managed_default_content_settings.javascript": 1,  # JS needed!
        "profile.managed_default_content_settings.plugins": 1,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.media_stream": 2,
    }
    options.add_experimental_option("prefs", prefs)
    options.page_load_strategy = 'eager'  # Don't wait for full page load
    
    driver = webdriver.Edge(options=options)
    
    # Execute CDP commands to hide webdriver
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """
    })
    
    return driver


def parse_price(price_text):
    """Extract numeric price from text."""
    if not price_text:
        return None
    # Remove currency symbols and commas
    cleaned = re.sub(r'[₹$,\s]', '', price_text)
    try:
        return float(cleaned.split('.')[0])  # Get whole number
    except:
        return None


def scrape_amazon(query, max_results=100):
    """
    Scrape Amazon India search results (multi-page for 100 results).
    
    Selectors (from analysis):
    - Container: [data-component-type='s-search-result']
    - Title: h2 a span
    - Price: .a-price-whole
    - Image: img.s-image
    - Link: h2 a
    - Rating: .a-icon-star-small span
    """
    driver = None
    products = []
    
    try:
        driver = get_chrome_driver()
        
        # Scrape multiple pages to get 100 results (Amazon shows ~20-24 per page)
        pages_needed = min(3, (max_results // 24) + 1)  # Max 3 pages
        
        for page in range(1, pages_needed + 1):
            if len(products) >= max_results:
                break
                
            url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&page={page}"
            driver.get(url)
            
            # Wait for search results (reduced timeout for speed)
            try:
                WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-type='s-search-result']"))
                )
            except:
                if page == 1:
                    raise
                break  # No more pages
            
            # Quick scroll to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.2)  # Scroll back to top
        
            # Parse with BeautifulSoup (MUCH faster than Selenium selectors)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            containers = soup.select("[data-component-type='s-search-result']")
            
            for container in containers:
                try:
                    # Extract title - robust across layouts and categories
                    candidates = []

                    # Common span selectors
                    title_selectors = [
                        "span.a-size-base-plus.a-color-base.a-text-normal",
                        "span.a-size-medium.a-color-base.a-text-normal",
                        "h2 a span",
                        "h2 span",
                        "[data-cy='title-recipe'] h2 span"
                    ]
                    for sel in title_selectors:
                        for el in container.select(sel):
                            text = el.get_text(strip=True)
                            if text:
                                candidates.append(text)

                    # Try link attributes (often contains full title)
                    link_el = container.select_one("h2 a")
                    if link_el:
                        for attr in ("aria-label", "title"):
                            val = link_el.get(attr)
                            if val:
                                candidates.append(val.strip())

                    # Try image alt (fallback)
                    img_el = container.select_one("img.s-image")
                    if img_el:
                        alt = img_el.get("alt")
                        if alt:
                            candidates.append(alt.strip())

                    # Choose the longest meaningful candidate (avoid single-word brand only)
                    title = None
                    if candidates:
                        candidates = [c for c in candidates if len(c) >= 8]
                        candidates.sort(key=len, reverse=True)
                        for c in candidates:
                            # Skip titles that are just brand (single word, all caps, very short)
                            if len(c.split()) == 1 and c.isupper() and len(c) <= 12:
                                continue
                            title = c
                            break

                    if not title:
                        title = "Unknown Product"
                
                    # Extract price
                    price_el = container.select(".a-price-whole")
                    price = parse_price(price_el[0].text) if price_el else None
                    
                    # Extract image
                    img_el = container.select("img.s-image")
                    image = img_el[0].get('src') if img_el else None
                    
                    # Extract link
                    link_el = container.select("h2 a, a.a-link-normal.s-underline-text, a.a-link-normal.s-no-outline")
                    link = None
                    if link_el:
                        href = link_el[0].get('href')
                        if href:
                            if href.startswith("/"):
                                link = "https://www.amazon.in" + href
                            else:
                                link = href
                                
                    if link and "https://www.amazon.inhttps" in link:
                        link = link.replace("https://www.amazon.inhttps", "https")
                    
                    # Extract rating
                    rating_el = container.select(".a-icon-star-small span, .a-icon-alt")
                    rating_text = rating_el[0].get_text() if rating_el else None
                    rating = None
                    if rating_text:
                        match = re.search(r'(\d+\.?\d*)', rating_text)
                        if match:
                            rating = float(match.group(1))
                    
                    # Check for Prime
                    prime_el = container.select(".a-icon-prime, [aria-label*='Prime']")
                    is_prime = len(prime_el) > 0
                    
                    if title and price:  # Only add if we have title and price
                        products.append({
                            "title": title,
                            "price": price,
                            "image": image,
                            "link": link,
                            "rating": rating,
                            "is_prime": is_prime,
                            "source": "amazon"
                        })
                        if len(products) >= max_results:
                            break
                        
                except Exception as e:
                    print(f"[AMAZON] Error parsing product: {e}")
                    continue
                    
    except Exception as e:
        print(f"[AMAZON] Scraping error: {e}")
        
    finally:
        if driver:
            driver.quit()
    
    return products


def scrape_flipkart(query, max_results=100):
    """
    Scrape Flipkart search results (multi-page for 100 results).
    
    Selectors (from analysis):
    - Container: div[data-id]
    - Title: div._4rR01T, a.s1Q9rs
    - Price: div._30jeq3
    - Image: img._396cs4, img._2r_T1I
    - Link: a._1fQZEK, a._2rpwqI
    - Rating: div._3LWZlK
    """
    driver = None
    products = []
    
    try:
        driver = get_chrome_driver()
        
        # Scrape multiple pages (Flipkart shows ~24 per page)
        pages_needed = min(3, (max_results // 24) + 1)
        
        for page in range(1, pages_needed + 1):
            if len(products) >= max_results:
                break
                
            url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}&page={page}"
            driver.get(url)
            
            # Flipkart content loads asynchronously — give it time
            time.sleep(2)
            
            # Wait for either layout (increased timeout for reliability)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-id], img, a[href*='/p/']"))
                )
            except:
                if page == 1:
                    pass  # Continue anyway for first page
                else:
                    break  # No more pages
                
            # Close login popup if it appears (only on first page)
            if page == 1:
                try:
                    close_btn = driver.find_element(By.CSS_SELECTOR, "button._2KpZ6l._2doB4z, span._30XB9F")
                    close_btn.click()
                    time.sleep(0.5)
                except:
                    pass
            
            # Scroll to trigger lazy loading (increased delays)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1.0)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.0)
        
            # Parse with BeautifulSoup (MUCH faster)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # --- Robust Heuristic Approach ---
            # Flipkart heavily obfuscates class names like `cPHDOP` or `tUxRFH`.
            # We look for all links that contain `/p/` (which indicates a product page)
            product_links = soup.find_all('a', href=re.compile(r'/p/'))
            
            seen_links = set()
            
            for a in product_links:
                href = a.get('href')
                if not href or href in seen_links: continue
                # Basic filter to avoid junk links
                if 'Search results' in a.get_text(): continue
                
                # 1. Title Extraction
                title = None
                text = a.get_text(strip=True)
                
                if len(text) > 15:
                    title = text
                elif a.get('title') and len(a.get('title')) > 15:
                    title = a.get('title')
                else:
                    # Check child divs
                    for d in a.find_all(['div', 'span']):
                        t = d.get_text(strip=True)
                        if len(t) > 15 and not t.startswith('₹') and not 'OFF' in t.upper():
                            title = t
                            break
                            
                # Fallback: check parents' other children (for grid layouts)
                if not title:
                    parent = a.parent
                    if parent:
                        for sibling in parent.find_all(['div', 'a']):
                            t = sibling.get_text(strip=True)
                            if len(t) > 15 and not t.startswith('₹') and not 'OFF' in t.upper():
                                title = t
                                break
                                
                if not title: continue
                
                # 2. Price Extraction
                price = None
                # Traverse up the DOM to find the nearest price block
                curr = a
                for _ in range(6): # Go up 6 levels max
                    if not curr or curr.name == 'body': break
                    
                    # Look for characteristic Rupee symbol
                    price_texts = curr.find_all(string=re.compile(r'₹[0-9,]+'))
                    if price_texts:
                        for pt in price_texts:
                            pt_str = str(pt).strip()
                            # Check if it's the discounted/original price (often has line-through)
                            parent_classes = ' '.join(pt.parent.get('class', [])).lower()
                            if 'strikethrough' in parent_classes or 'discount' in parent_classes:
                                continue
                                
                            parsed_p = parse_price(pt_str)
                            if parsed_p:
                                price = parsed_p
                                break
                    
                    if price: break
                    curr = curr.parent

                # 3. Image Extraction
                image = None
                curr = a
                for _ in range(4):
                    if not curr or curr.name == 'body': break
                    img_els = curr.find_all('img')
                    for img in img_els:
                        src = img.get('src') or img.get('data-src')
                        if src and ('rukminim' in src or 'http' in src) and not src.endswith('.svg'):
                            image = src
                            break
                    if image: break
                    curr = curr.parent
                    
                # 4. Rating Extraction
                rating = None
                curr = a
                for _ in range(4):
                    if not curr or curr.name == 'body': break
                    # Look for characteristic rating formats like "4.5"
                    rating_blocks = curr.find_all('div')
                    for rb in rating_blocks:
                        t = rb.get_text(strip=True)
                        if re.match(r'^[1-5]\.[0-9]$', t) or re.match(r'^[1-5]$', t):
                            rating = float(t)
                            break
                    if rating: break
                    curr = curr.parent
                            
                # Link cleanup
                link = href
                if link and not link.startswith("http"):
                    link = "https://www.flipkart.com" + link
                    
                if title and price:
                    products.append({
                        "title": title,
                        "price": price,
                        "image": image,
                        "link": link,
                        "rating": rating,
                        "is_prime": False,  # Flipkart lacks Prime concept precisely as modeled
                        "source": "flipkart"
                    })
                    seen_links.add(href)
                    
                if len(products) >= max_results:
                    break
                    
    except Exception as e:
        print(f"[FLIPKART] Scraping error: {e}")
        
    finally:
        if driver:
            driver.quit()
    
    return products


# Global Constants
SUPPORTED_BRANDS = [
        # Phones
        'apple', 'iphone', 'samsung', 'oneplus', 'xiaomi', 'redmi', 'realme', 
        'oppo', 'vivo', 'poco', 'motorola', 'google', 'pixel', 'nothing',
        # TVs
        'mi', 'lg', 'sony', 'toshiba', 'tcl', 'panasonic', 'philips', 'haier',
        'hisense', 'vu', 'acer', 'acerpure', 'kenstar', 'onida', 'iffalcon',
        # Laptops
        'hp', 'dell', 'lenovo', 'asus', 'msi', 'macbook', 'thinkpad',
        # Audio
        'boat', 'jbl', 'bose', 'sennheiser', 'noise', 'zebronics', 'skullcandy',
        # Kitchen Appliances
        'prestige', 'bajaj', 'philips', 'butterfly', 'preethi', 'pigeon', 
        'havells', 'morphy richards', 'usha', 'crompton', 'kent', 'maharaja',
        'sujata', 'bosch', 'wonderchef', 'kenwood', 'inalsa', 'hamilton',
        # Stationary / Pens
        'parker', 'montblanc', 'cross', 'sheaffer', 'lamy', 'pilot', 'uniball', 'staedtler', 'faber castell',
        # Clocks / Watches
        'titan', 'casio', 'fossil', 'timex', 'fastrack', 'ajanta', 'oreva', 'seiko', 'citizen'
]

def normalize_title(title):
    """Normalize title for better matching."""
    if not title:
        return ""
    title = title.lower()
    
    # Remove symbols that confuse embeddings
    title = re.sub(r'[()\[\]|\-,]', ' ', title)
    
    # Standardize units (GB vs G.B vs GB.)
    title = re.sub(r'(\d+)\s*(?:gb|g\.b|gb\.)', r'\1gb', title)
    title = re.sub(r'(\d+)\s*(?:tb|t\.b|tb\.)', r'\1tb', title)
    
    # Remove common noise words/marketing fluff
    noise_words = {
        'with', 'and', 'the', 'for', 'new', 'latest', 'mobile', 'phone', 
        'smartphone', 'works', 'camera', 'control', 'chip', 'boost', 
        'battery', 'life', 'display', '5g', '4g', 'lte', 'india', 'buy', 
        'online', 'best', 'price', 'low', 'guarantee', 'warranty', 'available',
        'fast', 'delivery', 'shipping', 'original', 'genuine'
    }
    
    words = title.split()
    filtered = [w for w in words if w not in noise_words and len(w) > 1]
    return ' '.join(filtered)


def extract_key_identifiers(title):
    """Extract key product identifiers like brand, model, size, storage."""
    if not title:
        return set()
    
    title_lower = title.lower()
    identifiers = set()
    
    # Extract brand names
    for brand in SUPPORTED_BRANDS:
        if re.search(r'\b' + re.escape(brand) + r'\b', title_lower):
            identifiers.add(brand)
            
    # Brand Families (for grouping)
    if any(b in identifiers for b in ['iphone', 'macbook', 'ipad', 'apple']):
        identifiers.add('brandfamily_apple')
    if any(b in identifiers for b in ['xiaomi', 'redmi', 'mi']):
        identifiers.add('brandfamily_xiaomi')
    if 'samsung' in identifiers:
        identifiers.add('brandfamily_samsung')

    # Condition / Type Flags
    if any(x in title_lower for x in ['renewed', 'refurbished', 'unboxed', 'used', 'pre-owned']):
        identifiers.add('flag_refurbished')
    else:
        identifiers.add('flag_new')

    if any(x in title_lower for x in ['compatible', 'for ', 'case for', 'cover for', 'adapter for']):
        identifiers.add('flag_accessory')
    else:
        identifiers.add('flag_main_product')
    
    # Extract screen sizes for TVs/Monitors (e.g., 32 inch, 43 inch, 55", 80cm)
    # Using word boundaries and specific patterns to avoid catching other numbers
    size_match = re.search(r'(\d{2,3})\s*(?:inch|cm|\"|\')', title_lower)
    if size_match:
        val = int(size_match.group(1))
        unit = size_match.group(0).lower()
        if 'cm' in unit:
            # Standardize common cm to inch mappings to avoid rounding errors
            cm_to_inch = {80: 32, 108: 43, 109: 43, 126: 50, 138: 55, 139: 55, 164: 65, 189: 75}
            inch = cm_to_inch.get(val, round(val / 2.54))
            identifiers.add(f"{inch}inch")
        else:
            identifiers.add(f"{val}inch")
    
    # Extract storage/RAM sizes (e.g., 8GB RAM, 128GB Storage, 1TB)
    storage_candidates = []
    for match in re.finditer(r'(\d+)\s*(gb|tb)', title_lower):
        val = int(match.group(1))
        unit = match.group(2)
        token = f"{val}{unit}"
        identifiers.add(token)

        start, end = match.span()
        window = title_lower[max(0, start - 12):min(len(title_lower), end + 12)]

        if 'ram' in window:
            identifiers.add(f"ram_{token}")
        elif 'rom' in window or 'storage' in window:
            identifiers.add(f"storage_{token}")
            storage_candidates.append((val, unit, token))
        else:
            storage_candidates.append((val, unit, token))

    # If no explicit storage identified, assume the largest size is storage
    if storage_candidates and not any(i.startswith('storage_') for i in identifiers):
        def size_value(v, u):
            return v * 1024 if u == 'tb' else v
        best = max(storage_candidates, key=lambda t: size_value(t[0], t[1]))
        identifiers.add(f"storage_{best[2]}")
    
    # Extract resolution types - more robust matching
    res_map = {
        '4k': '4k', 'uhd': '4k', 'ultra hd': '4k', '2160p': '4k',
        'full hd': 'fhd', 'fhd': 'fhd', '1080p': 'fhd',
        'hd ready': 'hd', '720p': 'hd'
    }
    for res_str, res_id in res_map.items():
        if res_str in title_lower:
            identifiers.add(res_id)
    
    # Special check for generic "HD" which is often used for 720p/HD Ready
    if 'hd' not in identifiers and re.search(r'\bhd\b', title_lower):
        if 'fhd' not in identifiers and '4k' not in identifiers:
            identifiers.add('hd')
    
    # Panel types
    panels = ['qled', 'oled', 'led', 'lcd']
    for panel in panels:
        if panel in title_lower:
            identifiers.add(panel)
    
    # --- Wattage for Appliances (Mixers, Grinders, etc.) ---
    watt_match = re.search(r'(\d+)\s*(?:watt|w)\b', title_lower)
    if watt_match:
        identifiers.add('watt_' + watt_match.group(1))
    
    # --- Appliance Model Names (Critical for kitchen appliances) ---
    appliance_models = [
        # Prestige models
        'apex', 'iris', 'popular', 'deluxe', 'teon', 'nakshatra', 'omega', 'manttra',
        # Philips models
        'viva', 'daily', 'avance',
        # Bajaj models
        'gx', 'twister', 'classic', 'bravo', 'platini',
        # Butterfly models
        'jet', 'hero', 'matchless', 'desire', 'splendid',
        # Preethi models
        'zodiac', 'blue leaf', 'eco', 'peppy',
        # Generic appliance terms
        'juicer', 'blender', 'chopper', 'grinder', 'mixer'
    ]
    for model in appliance_models:
        if re.search(r'\b' + model + r'\b', title_lower):
            identifiers.add('appmodel_' + model)
    
    # --- Jar Count for Mixers ---
    jar_match = re.search(r'(\d+)\s*(?:jar|jars)\b', title_lower)
    if jar_match:
        identifiers.add('jars_' + jar_match.group(1))
            
    # --- New General Identifiers ---
    
    # Colors (important for clothing and gadgets)
    colors = ['black', 'white', 'silver', 'gold', 'blue', 'red', 'green', 'yellow', 'pink', 'purple', 'orange', 'grey', 'gray', 'brown', 'multicolor']
    for color in colors:
        if re.search(r'\b' + color + r'\b', title_lower):
            identifiers.add('color_' + color)
            
    # Quantity / Pack Size (e.g., "Pack of 2", "Set of 3", "2kg", "500ml")
    qty_patterns = [
        r'\bpack\s*of\s*(\d+)\b',
        r'\bset\s*of\s*(\d+)\b',
        r'(\d+)\s*(?:kg|gram|gm|ml|ltr|litre|pounds|lbs)\b',
        r'(\d+)\s*piece(?:s)?\b',
    ]
    for pattern in qty_patterns:
        match = re.search(pattern, title_lower)
        if match:
            # Add a 'unit_' prefix to differentiate from screen sizes or storage
            identifiers.add('unit_' + match.group(0).replace(' ', ''))
            
    # Alphanumeric Model Numbers (e.g., SM-G991B, WH-1000XM4, B07XJ8C8F5)
    # Improved to be hyphen-tolerant and catch mixed clusters
    tokens = re.split(r'[\s/]+', title_lower)
    for token in tokens:
        clean_token = token.strip('(),.[]"\'')
        if len(clean_token) >= 4 and any(c.isdigit() for c in clean_token) and any(c.isalpha() for c in clean_token):
             # Normalize: remove non-alphanumeric chars for matching
             norm = re.sub(r'[^a-z0-9]', '', clean_token)
             if len(norm) >= 4 and norm not in ['pack', 'inch', 'with', 'from', 'best', 'india', '500ml', 'gen1', 'gen2', 'gen3']:
                 identifiers.add('model_' + norm)
            
    # Variants (moved down and expanded)
    variants = ['pro', 'max', 'plus', 'ultra', 'mini', 'air', 'lite', 'fe', 'promax', 'v2', 'gen', 'generation']
    for variant in variants:
        if re.search(r'\b' + variant + r'\b', title_lower):
            identifiers.add(variant)
            if variant == 'promax':
                identifiers.add('pro')
                identifiers.add('max')
    
    # Extract Series (TVs, Laptops, etc.) - Crucial for avoiding Series mismatches
    series_patterns = [
        r'\bfx\b', r'\bx\s*series\b', r'\ba\s*series\b', r'\bf\s*series\b', 
        r'\bg\s*series\b', r'\bfire\s*tv\b', r'\bgoogle\s*tv\b', 
        r'\bandroid\s*tv\b', r'\bwebos\b', r'\btizen\b',
        r'\bmacbook\s*air\b', r'\bmacbook\s*pro\b', r'\bthinkpad\b', 
        r'\bzenbook\b', r'\bvivobook\b', r'\brog\b', r'\btuf\b', r'\baliware\b',
        r'\binspiron\b', r'\bvostro\b', r'\blatitude\b', r'\bxps\b',
        r'\bideapad\b', r'\blegion\b', r'\byoga\b', r'\bpavilion\b', r'\benvy\b', r'\bspectre\b', r'\bomen\b'
    ]
    for pattern in series_patterns:
        match = re.search(pattern, title_lower)
        if match:
            identifiers.add('series_' + match.group(0).replace(' ', ''))
            
    # Extract phone model patterns
    model_patterns = [
        r'iphone\s*(\d+)(?:\s*(pro|plus|max))?',
        r's(\d+)(?:\s*(ultra|plus|\+))?',
        r'galaxy\s*(\w+)',
        r'(\d+)\s*pro',
        r'nord\s*(\w+)',
    ]
    for pattern in model_patterns:
        match = re.search(pattern, title_lower)
        if match:
            identifiers.add(match.group(0).replace(' ', ''))
    
    return identifiers


def match_products(amazon_products, flipkart_products):
    """
    Match similar products from Amazon and Flipkart.
    Uses AI Embeddings (RTX 4050 accelerated) + Regex Heuristics.
    """
    if not amazon_products and not flipkart_products:
        return []

    unified_products = []
    used_flipkart = set()
    
    # Handle single source results
    if not amazon_products:
        for p in flipkart_products:
            unified_products.append({
                "id": len(unified_products) + 1,
                "title": p['title'],
                "image": p['image'],
                "rating": p['rating'],
                "is_prime": False,
                "amazon_price": None,
                "amazon_link": None,
                "flipkart_price": p['price'],
                "flipkart_link": p['link'],
                "has_comparison": False,
                "match_confidence": 0
            })
        return unified_products

    if not flipkart_products:
        for p in amazon_products:
            unified_products.append({
                "id": len(unified_products) + 1,
                "title": p['title'],
                "image": p['image'],
                "rating": p['rating'],
                "is_prime": p['is_prime'],
                "amazon_price": p['price'],
                "amazon_link": p['link'],
                "flipkart_price": None,
                "flipkart_link": None,
                "has_comparison": False,
                "match_confidence": 0
            })
        return unified_products

    # Initialize AI Model
    model = get_model()
    
    # 1. Pre-calculate Amazon Identifiers and Embeddings
    amz_titles = [p['title'] for p in amazon_products]
    print(f"[AI] Encoding {len(amz_titles)} Amazon products...")
    amz_embeddings = model.encode(amz_titles, convert_to_tensor=True, show_progress_bar=False)
    
    amz_data = []
    for idx, amz_p in enumerate(amazon_products):
        amz_data.append({
            'p': amz_p,
            'embedding': amz_embeddings[idx],
            'identifiers': extract_key_identifiers(amz_p['title']),
            'words': set(normalize_title(amz_p['title']).split())
        })

    # 2. Pre-calculate Flipkart Identifiers and Embeddings
    fk_titles = [p['title'] for p in flipkart_products]
    print(f"[AI] Encoding {len(fk_titles)} Flipkart products...")
    fk_embeddings = model.encode(fk_titles, convert_to_tensor=True, show_progress_bar=False)
    
    fk_data = []
    for idx, fk_p in enumerate(flipkart_products):
        fk_data.append({
            'idx': idx,
            'p': fk_p,
            'embedding': fk_embeddings[idx],
            'identifiers': extract_key_identifiers(fk_p['title']),
            'words': set(normalize_title(fk_p['title']).split())
        })

    # 3. Batch compute all cosine similarities (GPU accelerated)
    # Resulting matrix shape: [len(amz), len(fk)]
    cosine_scores = util.cos_sim(amz_embeddings, fk_embeddings)

    # 4. Perform matching with conflict detection
    for i, amz in enumerate(amz_data):
        amz_product = amz['p']
        amz_ids = amz['identifiers']
        
        # Determine Category
        amz_cat = 'general'
        if any(x.endswith('inch') for x in amz_ids) or any(x in amz_ids for x in ['4k', 'fhd', 'hd']):
            amz_cat = 'tv'
        elif any(x.startswith('storage_') for x in amz_ids) and any(x in amz_ids for x in ['apple', 'samsung', 'oneplus', 'xiaomi', 'redmi', 'realme', 'oppo', 'vivo', 'poco', 'motorola']):
            amz_cat = 'mobile'
        elif any(x.startswith('watt_') for x in amz_ids) or any(x.startswith('jars_') for x in amz_ids):
            amz_cat = 'appliance'

        best_match = None
        best_score = 0
        best_idx = -1
        
        for j, fk in enumerate(fk_data):
            if fk['idx'] in used_flipkart:
                continue
            
            fk_ids = fk['identifiers']
            semantic_score = float(cosine_scores[i][j])
            
            # --- VETO LOGIC (100% Fatal Conflicts) ---
            
            # 1. Accessory vs Main Product Conflict
            if amz_ids.intersection({'flag_accessory', 'flag_main_product'}) != fk_ids.intersection({'flag_accessory', 'flag_main_product'}):
                continue

            # 2. Refurbished vs New Conflict
            if amz_ids.intersection({'flag_refurbished', 'flag_new'}) != fk_ids.intersection({'flag_refurbished', 'flag_new'}):
                continue
            
            # 3. Brand Conflict
            amz_brands = {x for x in amz_ids if not x.startswith(('brandfamily_', 'flag_', 'unit_', 'watt_', 'jars_', 'appmodel_', 'storage_', 'ram_', 'series_', 'model_', 'color_')) and x in SUPPORTED_BRANDS}
            fk_brands = {x for x in fk_ids if not x.startswith(('brandfamily_', 'flag_', 'unit_', 'watt_', 'jars_', 'appmodel_', 'storage_', 'ram_', 'series_', 'model_', 'color_')) and x in SUPPORTED_BRANDS}
            
            brand_conflict = False
            if amz_brands and fk_brands:
                # Check for explicit brand overlap
                if not amz_brands.intersection(fk_brands):
                    # Check for brand family overlap (e.g. Mi belongs to Xiaomi)
                    amz_families = {x for x in amz_ids if x.startswith('brandfamily_')}
                    fk_families = {x for x in fk_ids if x.startswith('brandfamily_')}
                    if not amz_families.intersection(fk_families):
                        continue # Hard brand mismatch

            # 4. Storage Conflict (Strict for Mobiles)
            amz_storage = {x for x in amz_ids if x.startswith('storage_')}
            fk_storage = {x for x in fk_ids if x.startswith('storage_')}
            if amz_storage and fk_storage and amz_storage != fk_storage:
                continue

            # 5. Quantity/Unit Conflict
            amz_units = {x for x in amz_ids if x.startswith('unit_')}
            fk_units = {x for x in fk_ids if x.startswith('unit_')}
            if amz_units and fk_units and amz_units != fk_units:
                continue

            # 6. Category Specific Vetoes
            if amz_cat == 'tv':
                # Screen size match
                amz_sizes = {x for x in amz_ids if x.endswith('inch')}
                fk_sizes = {x for x in fk_ids if x.endswith('inch')}
                if amz_sizes and fk_sizes and amz_sizes != fk_sizes:
                    continue
                # Resolution match
                amz_res = amz_ids.intersection({'4k', 'fhd', 'hd'})
                fk_res = fk_ids.intersection({'4k', 'fhd', 'hd'})
                if amz_res and fk_res and amz_res != fk_res:
                    continue
            
            if amz_cat == 'appliance':
                # Wattage match
                amz_watt = {x for x in amz_ids if x.startswith('watt_')}
                fk_watt = {x for x in fk_ids if x.startswith('watt_')}
                if amz_watt and fk_watt and amz_watt != fk_watt:
                    continue
                # Jar count match
                amz_jars = {x for x in amz_ids if x.startswith('jars_')}
                fk_jars = {x for x in fk_ids if x.startswith('jars_')}
                if amz_jars and fk_jars and amz_jars != fk_jars:
                    continue

            # 7. Series/Variant Conflict
            amz_series = {x for x in amz_ids if x.startswith('series_')}
            fk_series = {x for x in fk_ids if x.startswith('series_')}
            if amz_series and fk_series and amz_series != fk_series:
                continue

            # --- DYNAMIC SCORING ---
            score = semantic_score
            
            # Boost for shared identifiers
            overlap_count = len(amz_ids & fk_ids)
            score += (overlap_count * 0.05)
            
            # Boost for brand match
            brand_match = bool(amz_brands.intersection(fk_brands))
            if brand_match:
                score += 0.15
            
            # Boost for model match
            amz_models = {x for x in amz_ids if x.startswith('model_')}
            fk_models = {x for x in fk_ids if x.startswith('model_')}
            if amz_models and fk_models and amz_models.intersection(fk_models):
                score += 0.4 # Significant boost
                
            # Penalty for color mismatch (not a veto)
            amz_colors = {x for x in amz_ids if x.startswith('color_')}
            fk_colors = {x for x in fk_ids if x.startswith('color_')}
            if amz_colors and fk_colors and amz_colors != fk_colors:
                score -= 0.2

            # Final Decision based on confidence levels
            is_valid = False
            
            # Level 1: Extremely high confidence (Model match OR Brand+Storage+Series)
            if amz_models and fk_models and amz_models.intersection(fk_models) and semantic_score > 0.4:
                is_valid = True
            # Level 2: High overlap + decent semantic
            elif brand_match and overlap_count >= 4 and semantic_score > 0.55:
                is_valid = True
            # Level 3: Pure semantic (needs to be very high for electronics)
            elif semantic_score > 0.82:
                is_valid = True
            
            if is_valid and score > best_score:
                best_score = score
                best_match = fk['p']
                best_idx = fk['idx']
        
        unified = {
            "id": len(unified_products) + 1,
            "title": amz_product['title'],
            "image": amz_product['image'],
            "rating": amz_product['rating'],
            "is_prime": amz_product['is_prime'],
            "amazon_price": amz_product['price'],
            "amazon_link": amz_product['link'],
            "flipkart_price": best_match['price'] if best_match else None,
            "flipkart_link": best_match['link'] if best_match else None,
            "match_confidence": round(best_score, 2) if best_match else 0
        }
        
        if best_match:
            used_flipkart.add(best_idx)
        
        unified_products.append(unified)
    
    # Add unmatched Flipkart products
    for idx, fk_product in enumerate(flipkart_products):
        if idx not in used_flipkart:
            unified_products.append({
                "id": len(unified_products) + 1,
                "title": fk_product['title'],
                "image": fk_product['image'],
                "rating": fk_product['rating'],
                "is_prime": False,
                "amazon_price": None,
                "amazon_link": None,
                "flipkart_price": fk_product['price'],
                "flipkart_link": fk_product['link'],
                "match_confidence": 0
            })
    
    # Sort: matched products (with both prices) first, then unmatched
    matched = [p for p in unified_products if p['amazon_price'] and p['flipkart_price']]
    unmatched = [p for p in unified_products if not (p['amazon_price'] and p['flipkart_price'])]
    
    # Re-assign IDs after sorting
    sorted_products = matched + unmatched
    for i, product in enumerate(sorted_products):
        product['id'] = i + 1
        product['has_comparison'] = bool(product['amazon_price'] and product['flipkart_price'])
    
    return sorted_products


def scrape_product_details(url):
    """
    Scrape detailed product specifications from an individual Amazon or Flipkart product page.
    Uses Selenium to handle JavaScript-rendered content.
    Returns a dict of specification key-value pairs.
    """
    if not url:
        return {}
    
    driver = None
    specs = {}
    
    try:
        driver = get_chrome_driver()
        driver.set_page_load_timeout(15)
        print(f"[DETAIL SCRAPE] Loading: {url[:80]}...")
        driver.get(url)
        time.sleep(2)  # Let page render
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        if "amazon" in url.lower():
            # ── Amazon Product Details ──
            
            # Method 1: Technical Details table (#productDetails_techSpec_section_1)
            tech_table = soup.find('table', {'id': 'productDetails_techSpec_section_1'})
            if tech_table:
                for row in tech_table.find_all('tr'):
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        key = th.get_text(strip=True)
                        val = td.get_text(strip=True)
                        if key and val:
                            specs[key] = val
            
            # Method 2: Additional Info table (#productDetails_detailBullets_sections1)
            detail_table = soup.find('table', {'id': 'productDetails_detailBullets_sections1'})
            if detail_table:
                for row in detail_table.find_all('tr'):
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        key = th.get_text(strip=True)
                        val = td.get_text(strip=True)
                        if key and val and key not in specs:
                            specs[key] = val
            
            # Method 3: Detail Bullets (#detailBullets_feature_div)
            bullets_div = soup.find('div', {'id': 'detailBullets_feature_div'})
            if bullets_div:
                for li in bullets_div.find_all('li'):
                    spans = li.find_all('span', class_='a-list-item')
                    for span in spans:
                        text = span.get_text(strip=True)
                        if ':' in text or '\u200f' in text:
                            parts = re.split(r'[:\u200f‏]', text, 1)
                            if len(parts) == 2:
                                key = parts[0].strip().strip('\u200e')
                                val = parts[1].strip().strip('\u200e')
                                if key and val and key not in specs:
                                    specs[key] = val
            
            # Method 4: Feature bullets (#feature-bullets)
            feature_div = soup.find('div', {'id': 'feature-bullets'})
            if feature_div:
                features = []
                for li in feature_div.find_all('li'):
                    text = li.get_text(strip=True)
                    if text and len(text) > 5:
                        features.append(text)
                if features:
                    specs['Key Features'] = ' | '.join(features[:6])
            
            # Product description
            desc = soup.find('div', {'id': 'productDescription'})
            if desc:
                desc_text = desc.get_text(strip=True)[:300]
                if desc_text:
                    specs['Description'] = desc_text
                    
        elif "flipkart" in url.lower():
            # ── Flipkart Product Details ──
            
            # Method 1: Specification tables (_14cfVK or _3Fm-hO pattern)
            spec_divs = soup.find_all('div', class_=re.compile(r'_14cfVK|GNDEQ-|_3k-BhJ'))
            if not spec_divs:
                # Try alternative class patterns
                spec_divs = soup.find_all('div', class_=re.compile(r'X3BRps|_3dtsli'))
            
            for div in spec_divs:
                rows = div.find_all('tr', class_=re.compile(r'_1s_Smc|WJdYP6|row'))
                if not rows:
                    rows = div.find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 2:
                        key = tds[0].get_text(strip=True)
                        val_el = tds[1].find('li') or tds[1]
                        val = val_el.get_text(strip=True)
                        if key and val:
                            specs[key] = val
            
            # Method 2: Key Specs section (often _2RngUh or _2418kt)
            key_specs = soup.find_all('li', class_=re.compile(r'_2RngUh|_21lJbe'))
            if key_specs:
                features = [li.get_text(strip=True) for li in key_specs if li.get_text(strip=True)]
                if features:
                    specs['Highlights'] = ' | '.join(features[:6])

            # Method 3: Read more description
            desc_div = soup.find('div', class_=re.compile(r'_1mXcCf|_2o0sEQ'))
            if desc_div:
                desc_text = desc_div.get_text(strip=True)[:300]
                if desc_text:
                    specs['Description'] = desc_text
        
        print(f"[DETAIL SCRAPE] Found {len(specs)} specs from {url[:50]}...")
        
    except Exception as e:
        print(f"[DETAIL SCRAPE] Error scraping {url[:60]}: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return specs


def search_products(query, timeout=15, use_nvidia=False):
    """
    Search both Amazon and Flipkart concurrently.
    Returns unified product list.
    use_nvidia: If True, uses NVIDIA Kimi-K2 for product matching instead of sentence-transformers.
    """
    amazon_products = []
    flipkart_products = []
    
    # Increase timeout for slower machines/connections
    timeout = 45 
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        print("[SCRAPER] Starting threads...")
        amazon_future = executor.submit(scrape_amazon, query)
        flipkart_future = executor.submit(scrape_flipkart, query)
        
        try:
            print(f"[SCRAPER] Waiting for Amazon (timeout={timeout}s)...")
            amazon_products = amazon_future.result(timeout=timeout)
            print(f"[AMAZON] Found {len(amazon_products)} products")
        except TimeoutError:
            print("[AMAZON] Timeout - operation took too long")
        except Exception as e:
            print(f"[AMAZON] Error: {e}")
            
        try:
            print(f"[SCRAPER] Waiting for Flipkart (timeout={timeout}s)...")
            flipkart_products = flipkart_future.result(timeout=timeout)
            print(f"[FLIPKART] Found {len(flipkart_products)} products")
        except TimeoutError:
            print("[FLIPKART] Timeout - operation took too long")
        except Exception as e:
            print(f"[FLIPKART] Error: {e}")
    
    if use_nvidia:
        print("[SCRAPER] Using NVIDIA AI for product matching...")
        unified = match_products_nvidia(amazon_products, flipkart_products)
    else:
        print("[SCRAPER] Using local model for product matching...")
        unified = match_products(amazon_products, flipkart_products)
    return unified


def match_products_nvidia(amazon_products, flipkart_products):
    """
    Match products using NVIDIA Kimi-K2 AI model via API.
    Sends product titles to AI and asks it to find matching pairs.
    Falls back to local matching if API fails.
    """
    if not amazon_products and not flipkart_products:
        return []
    
    # Single source — no matching needed
    if not amazon_products:
        return [{
            "id": i + 1,
            "title": p['title'], "image": p['image'], "rating": p['rating'],
            "is_prime": False,
            "amazon_price": None, "amazon_link": None,
            "flipkart_price": p['price'], "flipkart_link": p['link'],
            "has_comparison": False, "match_confidence": 0
        } for i, p in enumerate(flipkart_products)]

    if not flipkart_products:
        return [{
            "id": i + 1,
            "title": p['title'], "image": p['image'], "rating": p['rating'],
            "is_prime": p['is_prime'],
            "amazon_price": p['price'], "amazon_link": p['link'],
            "flipkart_price": None, "flipkart_link": None,
            "has_comparison": False, "match_confidence": 0
        } for i, p in enumerate(amazon_products)]

    try:
        from openai import OpenAI
        import json as json_mod
        
        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key="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"
        )
        
        # Limit to manageable batch sizes for AI
        amz_batch = amazon_products[:30]
        fk_batch = flipkart_products[:30]
        
        # Build product lists for AI
        amz_list = "\n".join([f"A{i}: {p['title'][:100]}" for i, p in enumerate(amz_batch)])
        fk_list = "\n".join([f"F{i}: {p['title'][:100]}" for i, p in enumerate(fk_batch)])
        
        prompt = f"""You are a product matching AI. Match identical or very similar products between Amazon (A) and Flipkart (F) lists.

AMAZON PRODUCTS:
{amz_list}

FLIPKART PRODUCTS:
{fk_list}

RULES:
- Only match products that are the SAME product (same brand, model, specs)
- Do NOT match products that are merely in the same category
- Brand must match exactly
- Storage/RAM/size/color variants are different products — do NOT match them
- If unsure, do NOT match

Respond with ONLY a JSON array of matches. Each match: {{"a": amazon_index, "f": flipkart_index, "confidence": 0.0-1.0}}
Example: [{{"a": 0, "f": 3, "confidence": 0.95}}, {{"a": 2, "f": 1, "confidence": 0.88}}]
If no matches found, respond: []"""

        print(f"[NVIDIA] Sending {len(amz_batch)} Amazon + {len(fk_batch)} Flipkart products for matching...")
        
        completion = client.chat.completions.create(
            model="minimaxai/minimax-m2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            top_p=0.9,
            max_tokens=2048,
            stream=False
        )
        
        ai_response = completion.choices[0].message.content.strip()
        print(f"[NVIDIA] Raw response: {ai_response[:300]}")
        
        # Clean up response
        import re as re_mod
        ai_response = re_mod.sub(r'^```(?:json)?\s*', '', ai_response)
        ai_response = re_mod.sub(r'\s*```$', '', ai_response)
        ai_response = ai_response.strip()
        
        matches = json_mod.loads(ai_response)
        print(f"[NVIDIA] Found {len(matches)} matches")
        
        # Build unified products from AI matches
        unified_products = []
        used_flipkart = set()
        matched_amazon = set()
        
        for m in matches:
            a_idx = m.get('a', -1)
            f_idx = m.get('f', -1)
            confidence = m.get('confidence', 0)
            
            if a_idx < 0 or a_idx >= len(amz_batch) or f_idx < 0 or f_idx >= len(fk_batch):
                continue
            if f_idx in used_flipkart or a_idx in matched_amazon:
                continue
            if confidence < 0.7:
                continue
            
            amz_p = amz_batch[a_idx]
            fk_p = fk_batch[f_idx]
            
            unified_products.append({
                "id": len(unified_products) + 1,
                "title": amz_p['title'],
                "image": amz_p['image'],
                "rating": amz_p['rating'],
                "is_prime": amz_p['is_prime'],
                "amazon_price": amz_p['price'],
                "amazon_link": amz_p['link'],
                "flipkart_price": fk_p['price'],
                "flipkart_link": fk_p['link'],
                "has_comparison": True,
                "match_confidence": round(confidence, 2)
            })
            used_flipkart.add(f_idx)
            matched_amazon.add(a_idx)
        
        # Add unmatched Amazon products
        for i, p in enumerate(amz_batch):
            if i not in matched_amazon:
                unified_products.append({
                    "id": len(unified_products) + 1,
                    "title": p['title'], "image": p['image'], "rating": p['rating'],
                    "is_prime": p['is_prime'],
                    "amazon_price": p['price'], "amazon_link": p['link'],
                    "flipkart_price": None, "flipkart_link": None,
                    "has_comparison": False, "match_confidence": 0
                })
        
        # Add unmatched Flipkart products
        for i, p in enumerate(fk_batch):
            if i not in used_flipkart:
                unified_products.append({
                    "id": len(unified_products) + 1,
                    "title": p['title'], "image": p['image'], "rating": p['rating'],
                    "is_prime": False,
                    "amazon_price": None, "amazon_link": None,
                    "flipkart_price": p['price'], "flipkart_link": p['link'],
                    "has_comparison": False, "match_confidence": 0
                })
        
        # Sort: matched first
        matched = [p for p in unified_products if p['has_comparison']]
        unmatched = [p for p in unified_products if not p['has_comparison']]
        sorted_products = matched + unmatched
        for i, product in enumerate(sorted_products):
            product['id'] = i + 1
        
        print(f"[NVIDIA] Returning {len(sorted_products)} unified products ({len(matched)} matched)")
        return sorted_products
        
    except Exception as e:
        print(f"[NVIDIA] Error in AI matching, falling back to local model: {e}")
        return match_products(amazon_products, flipkart_products)


if __name__ == "__main__":
    # Test the scraper
    import json
    results = search_products("iphone 15")
    print(json.dumps(results, indent=2))
