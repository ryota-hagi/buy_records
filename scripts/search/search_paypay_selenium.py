#!/usr/bin/env python3
"""
PayPayフリマ検索スクリプト
"""
import sys
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import urllib.parse

def search_paypay(query, limit=20):
    """PayPayフリマで商品を検索"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    results = []
    
    try:
        # PayPayフリマの検索URLを構築
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://paypayfleamarket.yahoo.co.jp/search/{encoded_query}"
        
        driver.get(search_url)
        time.sleep(3)  # ページロード待機
        
        # 商品リストを取得
        wait = WebDriverWait(driver, 10)
        
        try:
            # 商品要素を待機
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/item/"]')))
        except TimeoutException:
            print(f"PayPayフリマで商品が見つかりません: {query}", file=sys.stderr)
            print(json.dumps([]))
            return
        
        # 商品情報を取得
        items = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/item/"]')
        
        for item in items[:limit]:
            try:
                # 商品情報を抽出
                item_data = {
                    'platform': 'paypay',
                    'item_url': item.get_attribute('href') or '',
                    'item_title': '',
                    'price': 0,
                    'item_image_url': '',
                    'seller': '',
                    'condition': '',
                    'shipping_cost': 0,
                    'total_price': 0
                }
                
                # タイトルを取得
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, 'p[class*="ItemCard__title"]')
                    item_data['item_title'] = title_elem.text
                except:
                    pass
                
                # 価格を取得
                try:
                    price_elem = item.find_element(By.CSS_SELECTOR, 'span[class*="ItemCard__price"]')
                    price_text = price_elem.text.replace('¥', '').replace(',', '').strip()
                    item_data['price'] = int(price_text)
                    item_data['total_price'] = item_data['price']
                except:
                    pass
                
                # 画像URLを取得
                try:
                    img_elem = item.find_element(By.CSS_SELECTOR, 'img')
                    item_data['item_image_url'] = img_elem.get_attribute('src') or ''
                except:
                    pass
                
                if item_data['item_title'] and item_data['price'] > 0:
                    results.append(item_data)
                    
            except Exception as e:
                print(f"商品情報取得エラー: {e}", file=sys.stderr)
                continue
        
    except Exception as e:
        print(f"PayPayフリマ検索エラー: {e}", file=sys.stderr)
    
    finally:
        driver.quit()
    
    # 結果をJSON形式で出力
    print(json.dumps(results, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python search_paypay_selenium.py <検索クエリ> [limit]", file=sys.stderr)
        sys.exit(1)
    
    search_query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    search_paypay(search_query, limit)