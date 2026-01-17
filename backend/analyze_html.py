"""
HTML Structure Analyzer for Amazon and Flipkart
================================================
This script fetches search result pages from both e-commerce sites
and saves the HTML for analysis. Run this to understand the DOM structure
before building the actual scraper.

Usage: python analyze_html.py <search_query>
Example: python analyze_html.py "iphone 15"
"""

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json


def get_chrome_driver():
    """Configure Chrome with anti-detection settings."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Disable automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Execute CDP commands to hide webdriver
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """
    })
    
    return driver


def fetch_amazon_html(driver, query):
    """Fetch Amazon search results page."""
    print(f"\n[AMAZON] Searching for: {query}")
    
    # Use Amazon India
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    print(f"[AMAZON] URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)  # Wait for dynamic content
        
        # Wait for search results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-type='s-search-result']"))
        )
        
        html = driver.page_source
        print(f"[AMAZON] Page loaded successfully ({len(html)} bytes)")
        return html
        
    except Exception as e:
        print(f"[AMAZON] Error: {e}")
        return driver.page_source if driver.page_source else None


def fetch_flipkart_html(driver, query):
    """Fetch Flipkart search results page."""
    print(f"\n[FLIPKART] Searching for: {query}")
    
    url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
    print(f"[FLIPKART] URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)  # Wait for dynamic content
        
        # Close login popup if it appears
        try:
            close_btn = driver.find_element(By.CSS_SELECTOR, "button._2KpZ6l._2doB4z")
            close_btn.click()
            time.sleep(1)
        except:
            pass
        
        html = driver.page_source
        print(f"[FLIPKART] Page loaded successfully ({len(html)} bytes)")
        return html
        
    except Exception as e:
        print(f"[FLIPKART] Error: {e}")
        return driver.page_source if driver.page_source else None


def analyze_amazon_structure(html):
    """Analyze Amazon HTML to find product selectors."""
    print("\n" + "="*60)
    print("AMAZON HTML STRUCTURE ANALYSIS")
    print("="*60)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find product containers
    products = soup.select("[data-component-type='s-search-result']")
    print(f"\nFound {len(products)} product containers")
    print("Selector: [data-component-type='s-search-result']")
    
    if products:
        product = products[0]
        print("\n--- First Product Analysis ---")
        
        # Try to find title
        title_el = product.select_one("h2 a span")
        if title_el:
            print(f"\nTITLE Selector: 'h2 a span'")
            print(f"Sample: {title_el.get_text()[:80]}...")
        
        # Try to find price
        price_el = product.select_one(".a-price-whole")
        if price_el:
            print(f"\nPRICE Selector: '.a-price-whole'")
            print(f"Sample: ₹{price_el.get_text()}")
        
        # Try to find image
        img_el = product.select_one("img.s-image")
        if img_el:
            print(f"\nIMAGE Selector: 'img.s-image'")
            print(f"Sample: {img_el.get('src', 'N/A')[:80]}...")
        
        # Try to find link
        link_el = product.select_one("h2 a")
        if link_el:
            print(f"\nLINK Selector: 'h2 a'")
            href = link_el.get('href', 'N/A')
            print(f"Sample: {href[:80]}...")
        
        # Try to find rating
        rating_el = product.select_one(".a-icon-star-small span")
        if rating_el:
            print(f"\nRATING Selector: '.a-icon-star-small span'")
            print(f"Sample: {rating_el.get_text()}")
    
    return {
        "container": "[data-component-type='s-search-result']",
        "title": "h2 a span",
        "price": ".a-price-whole",
        "image": "img.s-image",
        "link": "h2 a",
        "rating": ".a-icon-star-small span"
    }


def analyze_flipkart_structure(html):
    """Analyze Flipkart HTML to find product selectors."""
    print("\n" + "="*60)
    print("FLIPKART HTML STRUCTURE ANALYSIS")
    print("="*60)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Flipkart uses different structures for different product types
    # Try multiple selectors
    
    # Method 1: Grid layout products
    products = soup.select("div[data-id]")
    container_selector = "div[data-id]"
    
    if not products:
        # Method 2: List layout
        products = soup.select("div._1AtVbE")
        container_selector = "div._1AtVbE"
    
    print(f"\nFound {len(products)} potential product containers")
    print(f"Selector tried: {container_selector}")
    
    # Find all possible title patterns
    all_titles = soup.select("a[title]")
    print(f"\nFound {len(all_titles)} elements with title attribute")
    
    # Find price patterns (Flipkart uses ₹ symbol)
    all_prices = soup.find_all(string=lambda t: t and '₹' in t)
    print(f"Found {len(all_prices)} elements with ₹ symbol")
    
    # Analyze common classes
    print("\n--- Common Class Patterns ---")
    
    # Title patterns
    title_candidates = [
        "div._4rR01T",  # Grid view title
        "a.s1Q9rs",    # List view title
        "a._2rpwqI",   # Another variant
    ]
    
    for selector in title_candidates:
        els = soup.select(selector)
        if els:
            print(f"\nTITLE Selector: '{selector}' - Found {len(els)} matches")
            print(f"Sample: {els[0].get_text()[:80]}...")
    
    # Price patterns
    price_candidates = [
        "div._30jeq3",   # Common price class
        "div._1_WHN1",   # Discounted price
    ]
    
    for selector in price_candidates:
        els = soup.select(selector)
        if els:
            print(f"\nPRICE Selector: '{selector}' - Found {len(els)} matches")
            print(f"Sample: {els[0].get_text()}")
    
    # Image patterns
    img_els = soup.select("img._396cs4, img._2r_T1I")
    if img_els:
        print(f"\nIMAGE Selector: 'img._396cs4, img._2r_T1I' - Found {len(img_els)} matches")
    
    return {
        "container": "div[data-id]",
        "title": "div._4rR01T, a.s1Q9rs",
        "price": "div._30jeq3",
        "image": "img._396cs4, img._2r_T1I",
        "link": "a._1fQZEK, a._2rpwqI",
        "rating": "div._3LWZlK"
    }


def save_analysis_results(amazon_selectors, flipkart_selectors):
    """Save the discovered selectors to a JSON file."""
    results = {
        "amazon": amazon_selectors,
        "flipkart": flipkart_selectors,
        "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open("selectors.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print("SELECTORS SAVED TO: selectors.json")
    print("="*60)
    print(json.dumps(results, indent=2))


def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "iphone 15"
    
    print("="*60)
    print("E-COMMERCE HTML ANALYZER")
    print("="*60)
    print(f"Search Query: {query}")
    
    # Create output directory
    os.makedirs("html_samples", exist_ok=True)
    
    driver = get_chrome_driver()
    
    try:
        # Fetch Amazon
        amazon_html = fetch_amazon_html(driver, query)
        if amazon_html:
            with open("html_samples/amazon_search.html", "w", encoding="utf-8") as f:
                f.write(amazon_html)
            print("[AMAZON] HTML saved to: html_samples/amazon_search.html")
            amazon_selectors = analyze_amazon_structure(amazon_html)
        else:
            amazon_selectors = {}
        
        # Fetch Flipkart
        flipkart_html = fetch_flipkart_html(driver, query)
        if flipkart_html:
            with open("html_samples/flipkart_search.html", "w", encoding="utf-8") as f:
                f.write(flipkart_html)
            print("[FLIPKART] HTML saved to: html_samples/flipkart_search.html")
            flipkart_selectors = analyze_flipkart_structure(flipkart_html)
        else:
            flipkart_selectors = {}
        
        # Save results
        save_analysis_results(amazon_selectors, flipkart_selectors)
        
    finally:
        driver.quit()
        print("\n[DONE] Browser closed. Analysis complete!")


if __name__ == "__main__":
    main()
