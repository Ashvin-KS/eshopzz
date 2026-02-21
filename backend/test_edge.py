from selenium import webdriver
from selenium.webdriver.edge.options import Options

try:
    print("Setting up options...")
    options = Options()
    options.add_argument("--headless=new")
    print("Initializing Edge...")
    driver = webdriver.Edge(options=options)
    print("Success! Getting google.com...")
    driver.get("https://www.google.com")
    print(driver.title)
    driver.quit()
    print("Done.")
except Exception as e:
    import traceback
    traceback.print_exc()
