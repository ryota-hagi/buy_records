#!/usr/bin/env python3
"""
メルカリのページ構造をデバッグ
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=options)

try:
    url = "https://jp.mercari.com/search?keyword=nintendo%20switch&status=on_sale&sort=price&order=asc"
    print(f"アクセス中: {url}")
    
    driver.get(url)
    time.sleep(5)  # ページ完全読み込み待機
    
    # スクリーンショット保存
    driver.save_screenshot("mercari_debug.png")
    print("スクリーンショット保存: mercari_debug.png")
    
    # ページのHTMLを保存
    with open("mercari_debug.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("HTML保存: mercari_debug.html")
    
    # 商品要素を探す
    print("\n商品要素の検索:")
    
    # 様々なセレクタを試す
    selectors = [
        ("mer-item-thumbnail", By.TAG_NAME),
        ("[data-testid='item-cell']", By.CSS_SELECTOR),
        (".merItemThumbnail", By.CSS_SELECTOR),
        ("article", By.TAG_NAME),
        ("[role='article']", By.CSS_SELECTOR),
        ("li[data-testid*='item']", By.CSS_SELECTOR),
        ("div[data-testid*='item']", By.CSS_SELECTOR),
        ("a[href*='/item/']", By.CSS_SELECTOR),
    ]
    
    for selector, by_type in selectors:
        try:
            elements = driver.find_elements(by_type, selector)
            if elements:
                print(f"✓ {selector}: {len(elements)}個見つかりました")
                # 最初の要素の詳細
                if len(elements) > 0:
                    elem = elements[0]
                    print(f"  HTML: {elem.get_attribute('outerHTML')[:200]}...")
        except Exception as e:
            print(f"✗ {selector}: エラー {e}")
    
    # 価格要素を探す
    print("\n価格要素の検索:")
    price_selectors = [
        ("[data-testid='price']", By.CSS_SELECTOR),
        (".price", By.CSS_SELECTOR),
        ("span[class*='price']", By.CSS_SELECTOR),
        ("div[class*='price']", By.CSS_SELECTOR),
    ]
    
    for selector, by_type in price_selectors:
        try:
            elements = driver.find_elements(by_type, selector)
            if elements:
                print(f"✓ {selector}: {len(elements)}個見つかりました")
                print(f"  例: {elements[0].text}")
        except:
            pass
            
    input("ブラウザを確認してください。Enterで終了...")
    
finally:
    driver.quit()