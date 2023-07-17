import time
import pandas as pd
import re
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--start-maximized")  # Start browser maximized
chrome_options.add_argument("--incognito")  # Browse in incognito mode

# Set path to chromedriver as per your configuration
webdriver_service = Service('C:/Windows/chromedriver.exe')

def get_product_info_and_units(driver, url):
    driver.get(url)
    time.sleep(5)

    # Scrape the product name
    product_name = driver.find_element(By.CSS_SELECTOR, '.product-title h1').text

    # Scrape the review count and average rating
    review_info = driver.find_element(By.CSS_SELECTOR, '.rating-and-reviews').text.split()
    avg_rating = review_info[0]
    review_count = review_info[1]

    # Try to scrape the seller, if not available set to 'No seller information'
    try:
        seller = driver.find_element(By.CSS_SELECTOR, '.seller-information span a').text
    except NoSuchElementException:
        seller = 'No seller information'


    # Attempt to close the cookie banner
    try:
        accept_cookies_button = driver.find_element(By.XPATH, '//button[text()="Got it"]')
        accept_cookies_button.click()
        time.sleep(5)
    except NoSuchElementException:
        pass

    # Attempt to close a pop-up by clicking the close button
    try:
        close_button = driver.find_element(By.CSS_SELECTOR, 'button.modal-module_close-button_asjao')
        close_button.click()
        time.sleep(5)
    except NoSuchElementException:
        pass

    # Add the product to the cart
    wait = WebDriverWait(driver, 10)
    add_to_cart_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-ref="add-to-cart-button"]')))
    add_to_cart_button.click()
    time.sleep(5)

    # Go to the cart
    go_to_cart_button = wait.until(EC.presence_of_element_located((By.XPATH, '//button[contains(text(), "Go to Cart")]')))
    

    # Try to click the button until it succeeds
    while True:
        try:
            driver.execute_script("arguments[0].click();", go_to_cart_button)
            break  # If the click succeeded, break the loop
        except Exception as e:
            print(f"Failed to click 'Go to Cart' button: {str(e)}")
            time.sleep(1)  # Wait a second before trying again

    time.sleep(5)
    
    
    # Scrape the price from the cart
    price = driver.find_element(By.CSS_SELECTOR, '.cart-item-module_price-container_1IAjB .currency.plus').text

    # Change the quantity to 10+
    quantity_select = Select(driver.find_element(By.ID, 'cart-item_undefined'))
    quantity_select.select_by_visible_text('10+')
    time.sleep(5)

    # Type in quantity of 9999
    quantity_input = driver.find_element(By.ID, 'cart-item_undefined')
    quantity_input.clear()
    quantity_input.send_keys('9999')
    time.sleep(5)

    # Click update
    update_cart_button = driver.find_element(By.XPATH, '//button[@data-ref="quantity-update-button"]')
    update_cart_button.click()
    time.sleep(5)

    # Record the available units
    availability_text = driver.find_element(By.XPATH, '//div[contains(text(), "You asked for")]').text
    available_units = int(re.findall(r'\d+', availability_text)[1])  # Extract the second number

    # Remove the product from the cart
    remove_item_button = driver.find_element(By.XPATH, '//button[@data-ref="remove-item-button"]')
    remove_item_button.click()
    time.sleep(5)

    return product_name, review_count, avg_rating, seller, price, available_units

# Read the product URLs from the CSV file
df_urls = pd.read_csv('product_urls.csv')
product_urls = df_urls['URL'].tolist()

# Go through each product URL and scrape the product data
for url in product_urls:
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

    try:
        product_name, review_count, avg_rating, seller, price, units = get_product_info_and_units(driver, url)
    except (NoSuchElementException, NoSuchWindowException) as e:
        print(f"Failed to process URL {url}: {str(e)}")
        continue
    finally:
        driver.quit()

    # Load the existing data from the Excel file
    sanitized_url = hashlib.md5(url.encode()).hexdigest()
    filename = sanitized_url + '.xlsx'

    try:
        df = pd.read_excel(filename)
        last_units = df['Available Units'].iloc[-1] if not df.empty else None
    except FileNotFoundError:
        df = pd.DataFrame(columns=['Date', 'Time', 'URL', 'Product Name', 'Review Count', 'Average Rating', 'Seller', 'Price', 'Available Units', 'Units Sold'])
        last_units = None

    # Calculate the units sold in the last 5 minutes
    units_sold = last_units - units if last_units is not None else None

    # Create a DataFrame with the new data
    new_data = pd.DataFrame({
        'Date': [pd.to_datetime('today').strftime('%Y-%m-%d')],
        'Time': [pd.to_datetime('today').strftime('%H:%M:%S')],
        'URL': [url],
        'Product Name': [product_name],
        'Review Count': [review_count],
        'Average Rating': [avg_rating],
        'Seller': [seller],
        'Price': [price],
        'Available Units': [units],
        'Units Sold': [units_sold]
    })

    # Append the new data to the existing data
    df = pd.concat([df, new_data])

    # Write the DataFrame to an Excel file
    df.to_excel(filename, index=False)
