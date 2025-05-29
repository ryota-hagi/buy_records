#!/usr/bin/env python3
"""
ラクマスクレイパーの修正スクリプト
"""
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_rakuma_selectors():
    """ラクマのセレクターをテストして正しいものを特定"""
    print("=== Rakuma Selector Fix ===\n")
    
    # Seleniumドライバーの設定
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        # リモートWebDriverを試す
        print("📍 Connecting to Selenium server...")
        driver = webdriver.Remote(
            command_executor='http://localhost:5001/wd/hub',
            options=options
        )
        print("✅ Connected to remote Selenium server")
    except:
        print("⚠️  Remote connection failed, trying local driver...")
        try:
            driver = webdriver.Chrome(options=options)
            print("✅ Using local Chrome driver")
        except Exception as e:
            print(f"❌ Failed to create driver: {e}")
            return False
    
    try:
        # テスト検索
        keyword = "Nintendo Switch"
        url = f"https://rakuma.rakuten.co.jp/search/{keyword}"
        
        print(f"\n📍 Testing URL: {url}")
        driver.get(url)
        
        # ページロード待機
        time.sleep(3)
        
        # 現在のURL確認
        print(f"✅ Current URL: {driver.current_url}")
        
        # 可能なセレクターをテスト
        selectors_to_test = {
            "container": [
                "div[class*='item']",
                "div[class*='search-result']",
                "div[class*='product']",
                "div[class*='list']",
                "div.item",
                "article",
                "section[class*='item']"
            ],
            "title": [
                "h3",
                "h2",
                "p[class*='title']",
                "span[class*='title']",
                "div[class*='title']",
                "a[class*='name']"
            ],
            "price": [
                "span[class*='price']",
                "div[class*='price']",
                "p[class*='price']",
                "strong[class*='price']"
            ],
            "link": [
                "a[href*='/item/']",
                "a[href*='/product/']"
            ]
        }
        
        print("\n📍 Testing selectors...")
        found_selectors = {}
        
        for selector_type, selectors in selectors_to_test.items():
            print(f"\n  Testing {selector_type}:")
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"    ✅ {selector}: {len(elements)} found")
                        if selector_type not in found_selectors:
                            found_selectors[selector_type] = selector
                            # サンプルデータ取得
                            if len(elements) > 0:
                                sample = elements[0]
                                if selector_type == "title":
                                    print(f"       Sample: {sample.text[:50]}...")
                                elif selector_type == "price":
                                    print(f"       Sample: {sample.text}")
                                elif selector_type == "link":
                                    print(f"       Sample: {sample.get_attribute('href')[:80]}...")
                except Exception as e:
                    print(f"    ❌ {selector}: Error - {str(e)}")
        
        # ページのHTMLを保存（デバッグ用）
        print("\n📍 Saving page HTML for analysis...")
        with open('rakuma_test_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("✅ Saved to rakuma_test_page.html")
        
        # スクリーンショット保存
        print("\n📍 Taking screenshot...")
        driver.save_screenshot('rakuma_test_screenshot.png')
        print("✅ Saved to rakuma_test_screenshot.png")
        
        return found_selectors
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        return None
    finally:
        driver.quit()

def update_rakuma_scraper(selectors):
    """ラクマスクレイパーを正しいセレクターで更新"""
    if not selectors:
        print("\n❌ No valid selectors found")
        return
    
    print("\n📍 Updating Rakuma scraper with correct selectors...")
    
    # ここで実際のセレクター更新ロジックを実装
    print("\nFound selectors:")
    for key, value in selectors.items():
        print(f"  - {key}: {value}")
    
    # 更新推奨事項
    print("\n📝 Recommended updates for rakuma_selenium.py:")
    print(f"""
    # 商品コンテナ
    items = driver.find_elements(By.CSS_SELECTOR, "{selectors.get('container', 'div.item')}")
    
    # 各商品の情報取得
    for item in items:
        try:
            # タイトル
            title_elem = item.find_element(By.CSS_SELECTOR, "{selectors.get('title', 'h3')}")
            title = title_elem.text.strip()
            
            # 価格
            price_elem = item.find_element(By.CSS_SELECTOR, "{selectors.get('price', 'span[class*=price]')}")
            price_text = price_elem.text.strip()
            
            # リンク
            link_elem = item.find_element(By.CSS_SELECTOR, "{selectors.get('link', 'a[href*=/item/]')}")
            url = link_elem.get_attribute('href')
        except Exception as e:
            continue
    """)

if __name__ == "__main__":
    # セレクターテスト
    selectors = test_rakuma_selectors()
    
    if selectors:
        print("\n✅ Selector testing completed!")
        update_rakuma_scraper(selectors)
    else:
        print("\n❌ Selector testing failed")
        print("\nRecommended actions:")
        print("1. Check if Selenium server is running on port 5001")
        print("2. Verify Rakuma website structure hasn't changed")
        print("3. Review rakuma_test_page.html for actual structure")