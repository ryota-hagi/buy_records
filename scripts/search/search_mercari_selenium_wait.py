#!/usr/bin/env python3
"""
Mercari search using Selenium with proper wait conditions for dynamic content
"""
import json
import sys
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def search_mercari(query):
    """Search Mercari using Selenium with dynamic content loading"""
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Initialize driver
    try:
        # Try different ways to initialize the driver
        driver = None
        
        # Method 1: Try with ChromeDriverManager
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            pass
        
        # Method 2: Try without service (let Selenium handle it)
        if not driver:
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except:
                pass
        
        # Method 3: Try with specific path for ARM64 Macs
        if not driver:
            try:
                # Common paths for Chrome on macOS
                chrome_paths = [
                    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                    '/Applications/Chromium.app/Contents/MacOS/Chromium',
                ]
                for chrome_path in chrome_paths:
                    if os.path.exists(chrome_path):
                        chrome_options.binary_location = chrome_path
                        driver = webdriver.Chrome(options=chrome_options)
                        break
            except:
                pass
        
        if not driver:
            raise Exception("Could not initialize Chrome driver with any method")
            
    except Exception as e:
        print(f"Failed to initialize Chrome driver: {e}", file=sys.stderr)
        return []
    
    results = []
    
    try:
        # Construct search URL
        search_url = f"https://jp.mercari.com/search?keyword={query}&status=on_sale&sort=price&order=asc"
        print(f"Fetching: {search_url}", file=sys.stderr)
        
        # Load the page
        driver.get(search_url)
        
        # Wait for the page to load and items to appear
        # Mercari uses various class names for items, try multiple selectors
        item_selectors = [
            'a[href^="/item/m"]',  # Direct item links
            '[data-testid="item-cell"]',  # Item cells
            'div[class*="itemList"] a',  # Item list links
            'div[class*="search-result"] a[href*="/item/"]',  # Search result links
            'li[data-testid="item-cell"] a',  # List item cells
        ]
        
        items_found = False
        wait = WebDriverWait(driver, 20)  # Increased wait time
        
        for selector in item_selectors:
            try:
                # Wait for items to load
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                items = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if items:
                    print(f"Found {len(items)} items with selector: {selector}", file=sys.stderr)
                    items_found = True
                    
                    # Process items
                    for item in items[:20]:  # Limit to 20 items
                        try:
                            # Try to extract item data
                            href = item.get_attribute('href')
                            if not href or '/item/m' not in href:
                                continue
                            
                            # Extract item ID
                            item_id = href.split('/item/')[-1].split('?')[0]
                            
                            # Try to find price within the item element
                            price_text = None
                            price_selectors = [
                                '.merPrice',
                                '[class*="price"]',
                                'span[class*="Price"]',
                                'div[class*="price"]'
                            ]
                            
                            for price_sel in price_selectors:
                                try:
                                    price_elem = item.find_element(By.CSS_SELECTOR, price_sel)
                                    price_text = price_elem.text
                                    if price_text:
                                        break
                                except:
                                    pass
                            
                            # Try to find title
                            title_text = None
                            title_selectors = [
                                '[class*="itemName"]',
                                '[class*="title"]',
                                'p[class*="name"]',
                                'span[class*="name"]'
                            ]
                            
                            for title_sel in title_selectors:
                                try:
                                    title_elem = item.find_element(By.CSS_SELECTOR, title_sel)
                                    title_text = title_elem.text
                                    if title_text:
                                        break
                                except:
                                    pass
                            
                            # Try to find image
                            image_url = None
                            try:
                                img_elem = item.find_element(By.TAG_NAME, 'img')
                                image_url = img_elem.get_attribute('src')
                            except:
                                pass
                            
                            if item_id:
                                # Parse price
                                price = 0
                                if price_text:
                                    price_text = price_text.replace('¥', '').replace(',', '').strip()
                                    try:
                                        price = int(price_text)
                                    except:
                                        pass
                                
                                result = {
                                    'id': item_id,
                                    'title': title_text or f'Item {item_id}',
                                    'price': price,
                                    'url': f"https://jp.mercari.com/item/{item_id}",
                                    'image_url': image_url,
                                    'platform': 'mercari'
                                }
                                results.append(result)
                        except Exception as e:
                            print(f"Error processing item: {e}", file=sys.stderr)
                    
                    break  # Found items, stop trying other selectors
                    
            except Exception as e:
                print(f"Selector {selector} failed: {e}", file=sys.stderr)
        
        if not items_found:
            # If no items found with specific selectors, try to extract from page source
            print("No items found with selectors, trying page source extraction", file=sys.stderr)
            
            # Wait a bit more for dynamic content
            time.sleep(5)
            
            # Get page source and look for item IDs
            page_source = driver.page_source
            
            # Try to find item IDs in the source
            import re
            item_pattern = re.compile(r'/item/(m\d+)')
            matches = item_pattern.findall(page_source)
            
            if matches:
                print(f"Found {len(matches)} item IDs in page source", file=sys.stderr)
                for item_id in list(set(matches))[:20]:  # Unique IDs, limit to 20
                    result = {
                        'id': item_id,
                        'title': f'Nintendo Switch Item {item_id}',
                        'price': 0,  # Price will need to be fetched separately
                        'url': f"https://jp.mercari.com/item/{item_id}",
                        'image_url': None,
                        'platform': 'mercari'
                    }
                    results.append(result)
        
    except Exception as e:
        print(f"Error during Mercari search: {e}", file=sys.stderr)
        
    finally:
        driver.quit()
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: search_mercari_selenium_wait.py <query>", file=sys.stderr)
        sys.exit(1)
    
    query = sys.argv[1]
    
    print("JSON_START", file=sys.stderr)
    
    try:
        results = search_mercari(query)
        
        if not results:
            print("No results found from Mercari", file=sys.stderr)
        
        # Output results as JSON
        output = {
            'success': len(results) > 0,
            'results': results,
            'platform': 'mercari',
            'query': query
        }
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Script error: {e}", file=sys.stderr)
        error_output = {
            'success': False,
            'results': [],
            'error': str(e),
            'platform': 'mercari'
        }
        print(json.dumps(error_output, ensure_ascii=False, indent=2))
    
    print("JSON_END", file=sys.stderr)

if __name__ == "__main__":
    main()