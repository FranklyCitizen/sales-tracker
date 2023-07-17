import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--start-maximized")  # Start browser maximized
chrome_options.add_argument("--incognito")  # Browse in incognito mode

# Set path to chromedriver as per your configuration
webdriver_service = Service('C:/Windows/chromedriver.exe')

# Get the initial list of product URLs
driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

driver.get('http://www.takealot.com')

search_box = driver.find_element(By.NAME, 'search')
search_box.send_keys('weight loss')
search_box.send_keys(Keys.RETURN)

time.sleep(5)

# Attempt to close the cookie banner
try:
    accept_cookies_button = driver.find_element(By.XPATH, '//button[text()="Got it"]')
    accept_cookies_button.click()
    time.sleep(5)
except NoSuchElementException:
    pass

# Try to load the existing URLs from the CSV file
try:
    df = pd.read_csv('product_urls.csv')
    product_urls = df['URL'].tolist()
except FileNotFoundError:
    # If the file does not exist, start with an empty list
    product_urls = []

# Loop through each page of search results
while len(product_urls) < 20:
    # Get all the product links on the current page
    product_elements = driver.find_elements(By.CSS_SELECTOR, 'a.product-anchor')

    # Record the URL for each product
    for product in product_elements:
        url = product.get_attribute('href')
        
        if url not in product_urls:
            product_urls.append(url)

        if len(product_urls) >= 50:
            break

    # Try to find the 'Load More' button and click it
    try:
        load_more_button = driver.find_element(By.XPATH, '//button[text()="Load More"]')
        load_more_button.click()
        time.sleep(5)
    except NoSuchElementException:
        break

# Save the product URLs to a CSV file
df = pd.DataFrame(product_urls, columns=['URL'])
df.to_csv('product_urls.csv', index=False)

driver.quit()
