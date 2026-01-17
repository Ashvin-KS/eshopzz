from backend.scraper import get_chrome_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def debug_amazon():
    driver = get_chrome_driver()
    try:
        url = "https://www.amazon.in/s?k=monitor"
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-type='s-search-result']"))
        )
        time.sleep(2)
        containers = driver.find_elements(By.CSS_SELECTOR, "[data-component-type='s-search-result']")
        if containers:
            print(f"Found {len(containers)} containers.")
            for i, container in enumerate(containers[:3]):
                print(f"--- CONTAINER {i+1} ---")
                # print(f"Full text snippet: {container.text[:100]}...")
                
                h2s = container.find_elements(By.TAG_NAME, "h2")
                print(f"Found {len(h2s)} h2 elements.")
                for j, h2 in enumerate(h2s):
                    print(f"  h2[{j}] text: '{h2.text}'")
                    print(f"  h2[{j}] innerHTML: {h2.get_attribute('innerHTML')}")
                    
                spans = container.find_elements(By.CSS_SELECTOR, "h2 span")
                print(f"Found {len(spans)} 'h2 span' elements.")
                for k, span in enumerate(spans):
                    print(f"  span[{k}] text: '{span.text}'")
                    
        else:
            print("No containers found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_amazon()
