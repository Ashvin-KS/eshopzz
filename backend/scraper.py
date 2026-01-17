"""
ShopSync Scraper - Amazon and Flipkart Price Aggregator
=========================================================
Uses Selenium with anti-detection settings to scrape product data
from both e-commerce sites. Based on analyzed selectors.
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, TimeoutError


def get_chrome_driver():
    """Configure Chrome with anti-detection settings."""
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
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
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


def scrape_amazon(query, max_results=50):
    """
    Scrape Amazon India search results.
    
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
        url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
        driver.get(url)
        
        # Wait for search results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-type='s-search-result']"))
        )
        time.sleep(2)  # Extra wait for dynamic content
        
        # Scroll to load more products
        for _ in range(2):  # Reduced to 2 scrolls
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)  # Reduced wait
        driver.execute_script("window.scrollTo(0, 0);")  # Scroll back to top
        time.sleep(0.5)
        
        # Find all product containers
        containers = driver.find_elements(By.CSS_SELECTOR, "[data-component-type='s-search-result']")
        
        for container in containers[:max_results]:
            try:
                # Skip sponsored/ad results
                if container.get_attribute("data-component-type") != "s-search-result":
                    continue
                
                # Extract title
                title_el = container.find_elements(By.CSS_SELECTOR, "h2 a span, h2 span, span.a-size-medium, span.a-text-normal")
                title = title_el[0].text if title_el else "Unknown Product"
                
                # Extract price
                price_el = container.find_elements(By.CSS_SELECTOR, ".a-price-whole")
                price = parse_price(price_el[0].text) if price_el else None
                
                # Extract image
                img_el = container.find_elements(By.CSS_SELECTOR, "img.s-image")
                image = img_el[0].get_attribute("src") if img_el else None
                
                # Extract link
                link_el = container.find_elements(By.CSS_SELECTOR, "h2 a, a.a-link-normal.s-underline-text, a.a-link-normal.s-no-outline")
                link = None
                if link_el:
                    href = link_el[0].get_attribute("href")
                    if href:
                        if href.startswith("/"):
                            link = "https://www.amazon.in" + href
                        else:
                            link = href
                            
                if link and "https://www.amazon.inhttps" in link:
                     link = link.replace("https://www.amazon.inhttps", "https")
                
                # Extract rating
                rating_el = container.find_elements(By.CSS_SELECTOR, ".a-icon-star-small span, .a-icon-alt")
                rating_text = rating_el[0].get_attribute("textContent") if rating_el else None
                rating = None
                if rating_text:
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        rating = float(match.group(1))
                
                # Check for Prime
                prime_el = container.find_elements(By.CSS_SELECTOR, ".a-icon-prime, [aria-label*='Prime']")
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
                    
            except Exception as e:
                print(f"[AMAZON] Error parsing product: {e}")
                continue
                
    except Exception as e:
        print(f"[AMAZON] Scraping error: {e}")
        
    finally:
        if driver:
            driver.quit()
    
    return products


def scrape_flipkart(query, max_results=50):
    """
    Scrape Flipkart search results.
    
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
        url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
        driver.get(url)
        
        time.sleep(3)
        
        # Close login popup if it appears
        try:
            close_btn = driver.find_element(By.CSS_SELECTOR, "button._2KpZ6l._2doB4z, span._30XB9F")
            close_btn.click()
            time.sleep(1)
        except:
            pass
        
        # Scroll to load more products
        for _ in range(2):  # Reduced to 2 scrolls
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)  # Reduced wait
        driver.execute_script("window.scrollTo(0, 0);")  # Scroll back to top
        time.sleep(0.5)
        
        # Try multiple container selectors (Flipkart uses different layouts)
        containers = driver.find_elements(By.CSS_SELECTOR, "div[data-id]")
        
        if not containers:
            # Try alternative layout
            containers = driver.find_elements(By.CSS_SELECTOR, "div._1AtVbE div._13oc-S")
        
        for container in containers[:max_results]:
            try:
                # Extract title
                title_el = container.find_elements(By.CSS_SELECTOR, "div.RG5Slk, div._4rR01T, a.s1Q9rs, a.IRpwTa")
                title = title_el[0].text if title_el else None
                
                # Extract price
                price_el = container.find_elements(By.CSS_SELECTOR, "div.hZ3P6w, div._30jeq3, div._1_WHN1")
                price = parse_price(price_el[0].text) if price_el else None
                
                # Extract image
                img_el = container.find_elements(By.CSS_SELECTOR, "img.UCc1lI, img._396cs4, img._2r_T1I")
                image = img_el[0].get_attribute("src") if img_el else None
                
                # Extract link
                link_el = container.find_elements(By.CSS_SELECTOR, "a.k7wcnx, a._1fQZEK, a._2rpwqI, a.CGtC98")
                if not link_el:
                    link_el = container.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
                link = None
                if link_el:
                    href = link_el[0].get_attribute("href")
                    if href and not href.startswith("http"):
                        link = "https://www.flipkart.com" + href
                    else:
                        link = href
                
                # Extract rating
                rating_el = container.find_elements(By.CSS_SELECTOR, "div.MKiFS6, div._3LWZlK")
                rating = None
                if rating_el:
                    try:
                        # "4.6" + star image
                        rating = float(rating_el[0].text.split()[0])
                    except:
                        pass
                
                if title and price:
                    products.append({
                        "title": title,
                        "price": price,
                        "image": image,
                        "link": link,
                        "rating": rating,
                        "is_prime": False,  # Flipkart doesn't have Prime
                        "source": "flipkart"
                    })
                    
            except Exception as e:
                print(f"[FLIPKART] Error parsing product: {e}")
                continue
                
    except Exception as e:
        print(f"[FLIPKART] Scraping error: {e}")
        
    finally:
        if driver:
            driver.quit()
    
    return products


def normalize_title(title):
    """Normalize title for better matching."""
    if not title:
        return ""
    title = title.lower()
    # Remove common noise words
    noise_words = ['with', 'and', 'the', 'for', 'new', 'latest', 'mobile', 'phone', 
                   'smartphone', 'works', 'camera', 'control', 'chip', 'boost', 
                   'battery', 'life', 'display', '5g', '4g', 'lte', 'india']
    words = title.split()
    filtered = [w for w in words if w not in noise_words]
    return ' '.join(filtered)


def extract_key_identifiers(title):
    """Extract key product identifiers like brand, model, size, storage."""
    if not title:
        return set()
    
    title_lower = title.lower()
    identifiers = set()
    
    # Extract brand names (expanded list)
    brands = [
        # Phones
        'apple', 'iphone', 'samsung', 'oneplus', 'xiaomi', 'redmi', 'realme', 
        'oppo', 'vivo', 'poco', 'motorola', 'google', 'pixel', 'nothing',
        # TVs
        'mi', 'lg', 'sony', 'toshiba', 'tcl', 'panasonic', 'philips', 'haier',
        'hisense', 'vu', 'acer', 'acerpure', 'kenstar', 'onida', 'iffalcon',
        # Laptops
        'hp', 'dell', 'lenovo', 'asus', 'msi', 'macbook', 'thinkpad',
        # General
        'boat', 'jbl', 'bose', 'sennheiser', 'sony', 'noise'
    ]
    for brand in brands:
        if brand in title_lower:
            identifiers.add(brand)
    
    # Extract screen sizes for TVs (e.g., 32 inch, 43 inch, 55 inch)
    screen_match = re.search(r'(\d+)\s*(?:inch|cm|\"|\')', title_lower)
    if screen_match:
        identifiers.add(screen_match.group(1) + 'inch')
    
    # Also extract cm measurements and convert to approximate inch category
    cm_match = re.search(r'(\d+)\s*cm', title_lower)
    if cm_match:
        cm = int(cm_match.group(1))
        # Round to nearest common TV size
        inch_approx = round(cm / 2.54)
        identifiers.add(str(inch_approx) + 'inch')
    
    # Extract storage sizes (e.g., 128gb, 256 gb)
    storage_match = re.search(r'(\d+)\s*gb', title_lower)
    if storage_match:
        identifiers.add(storage_match.group(1) + 'gb')
    
    # Extract resolution types
    resolutions = ['4k', 'ultra hd', 'uhd', 'full hd', 'fhd', 'hd ready', 'qled', 'oled', 'led']
    for res in resolutions:
        if res in title_lower:
            identifiers.add(res.replace(' ', ''))
    
    # Extract TV series/model names
    tv_series = ['fire tv', 'google tv', 'android tv', 'webos', 'tizen', 
                 'a series', 'x series', 'f series', 'g series']
    for series in tv_series:
        if series in title_lower:
            identifiers.add(series.replace(' ', ''))
            
    # Extract variants/editions (crucial for distinguishing Pro vs Non-Pro)
    variants = ['pro', 'max', 'plus', 'ultra', 'mini', 'air', 'lite', 'fe', 'promax']
    for variant in variants:
        if re.search(r'\b' + variant + r'\b', title_lower):
            identifiers.add(variant)
            # Handle promax special case
            if variant == 'promax':
                identifiers.add('pro')
                identifiers.add('max')
    
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
    Uses keyword extraction and normalized title matching.
    Returns unified product objects with both prices.
    """
    unified_products = []
    used_flipkart = set()
    
    for amz_product in amazon_products:
        amz_title = amz_product['title']
        amz_normalized = normalize_title(amz_title)
        amz_identifiers = extract_key_identifiers(amz_title)
        amz_words = set(amz_normalized.split())
        
        best_match = None
        best_score = 0
        best_idx = -1
        
        for idx, fk_product in enumerate(flipkart_products):
            if idx in used_flipkart:
                continue
            
            fk_title = fk_product['title']
            fk_normalized = normalize_title(fk_title)
            fk_identifiers = extract_key_identifiers(fk_title)
            fk_words = set(fk_normalized.split())
            
            # Check key identifier overlap (brand + model + storage + size)
            identifier_overlap = len(amz_identifiers & fk_identifiers)
            
            # Resolution conflict check
            resolutions = {'4k', 'uhd', 'qled', 'oled', 'fullhd', 'fhd', 'hdready'}
            amz_res = amz_identifiers.intersection(resolutions)
            fk_res = fk_identifiers.intersection(resolutions)
            
            # If both have resolution info but they don't share ANY, it's a mismatch (e.g. 4k vs hdready)
            # Exception: '4k' matched with 'uhd' is fine (synonyms logic needed if not normalized)
            resolution_conflict = False
            if amz_res and fk_res and not amz_res.intersection(fk_res):
                # Check for synonyms
                synonyms = [{'4k', 'uhd', 'ultrahd'}, {'fullhd', 'fhd'}, {'hdready', 'hd'}]
                is_synonym = False
                for group in synonyms:
                    if amz_res.intersection(group) and fk_res.intersection(group):
                        is_synonym = True
                        break
                if not is_synonym:
                    resolution_conflict = True

            # Price difference check (sanity check)
            price_conflict = False
            if amz_product['price'] and fk_product['price']:
                p1 = amz_product['price']
                p2 = fk_product['price']
                # If price differs by more than 60%, likely different products (e.g. different storage/size)
                if abs(p1 - p2) / min(p1, p2) > 0.6:
                    price_conflict = True

            # Model Variant Conflict (e.g. Pro vs Pro Max, Plus vs Standard)
            variant_conflict = False
            variants = {'pro', 'max', 'plus', 'ultra', 'mini', 'air', 'lite', 'fe'}
            
            # Get variants present in each
            amz_vars = amz_identifiers.intersection(variants)
            fk_vars = fk_identifiers.intersection(variants)
            
            # If variants don't match exactly, it's a conflict
            # (e.g. {'pro'} vs {'pro', 'max'} is a conflict)
            if amz_vars != fk_vars:
                variant_conflict = True

            # Calculate word similarity
            intersection = len(amz_words & fk_words)
            union = len(amz_words | fk_words)
            word_score = intersection / union if union > 0 else 0
            
            # Combined score: prioritize identifier matches
            score = (identifier_overlap * 0.6) + (word_score * 0.4)
            
            # Debug logging for first few products
            if len(unified_products) < 3 and idx < 5:
                print(f"[MATCH DEBUG] AMZ: {amz_title[:50]} | FK: {fk_title[:50]}")
                print(f"  AMZ IDs: {amz_identifiers} | FK IDs: {fk_identifiers}")
                print(f"  Res Conf: {resolution_conflict} | Price Conf: {price_conflict} | Var Conf: {variant_conflict} | Score: {score:.2f}")
            
            # Skip valid matches if there's a conflict
            if resolution_conflict or price_conflict or variant_conflict:
                continue

            # Match if: 2+ identifiers OR (1 identifier + some word overlap)
            if identifier_overlap >= 2 and score > best_score:
                best_score = score
                best_match = fk_product
                best_idx = idx
            elif identifier_overlap >= 1 and word_score > 0.15 and score > best_score:
                # Fallback: 1 identifier + some word overlap (lowered threshold)
                best_score = score
                best_match = fk_product
                best_idx = idx
        
        unified = {
            "id": len(unified_products) + 1,
            "title": amz_product['title'],
            "image": amz_product['image'],
            "rating": amz_product['rating'],
            "is_prime": amz_product['is_prime'],
            "amazon_price": amz_product['price'],
            "amazon_link": amz_product['link'],
            "flipkart_price": best_match['price'] if best_match else None,
            "flipkart_link": best_match['link'] if best_match else None
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
                "flipkart_link": fk_product['link']
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


def search_products(query, timeout=15):
    """
    Search both Amazon and Flipkart concurrently.
    Returns unified product list.
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
    
    print("[SCRAPER] Matching products...")
    # Match and unify products
    unified = match_products(amazon_products, flipkart_products)
    return unified


if __name__ == "__main__":
    # Test the scraper
    import json
    results = search_products("iphone 15")
    print(json.dumps(results, indent=2))
