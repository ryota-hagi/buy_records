#!/usr/bin/env python3
"""
ラクマの価格取得をデバッグ
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re

def debug_rakuma_price():
    """ラクマの価格取得をデバッグ"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 検索ページ
        search_url = "https://fril.jp/s?query=Nintendo+Switch"
        print(f"検索ページアクセス: {search_url}")
        driver.get(search_url)
        time.sleep(5)
        
        # 商品リンクを取得
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="item.fril.jp"]')
        print(f"\n商品リンク数: {len(links)}")
        
        # 最初の3つの商品を詳しく見る
        for i, link in enumerate(links[:3]):
            print(f"\n=== 商品 {i+1} ===")
            
            # リンクの親要素を遡る
            parent = link
            for j in range(4):
                try:
                    parent = parent.find_element(By.XPATH, '..')
                    text = parent.text.strip()
                    
                    print(f"\n親要素レベル{j+1}のテキスト:")
                    print(f"---")
                    print(text)
                    print(f"---")
                    
                    # 価格パターンを探す
                    price_patterns = [
                        r'¥\s*([\d,]+)',
                        r'￥\s*([\d,]+)',
                        r'([\d,]+)\s*円',
                        r'¥([\d,]+)',
                        r'￥([\d,]+)'
                    ]
                    
                    for pattern in price_patterns:
                        matches = re.findall(pattern, text)
                        if matches:
                            print(f"価格パターン '{pattern}' で見つかった値: {matches}")
                    
                except Exception as e:
                    print(f"親要素レベル{j+1}でエラー: {str(e)}")
                    break
            
            # 画像のalt属性も確認
            try:
                img = link.find_element(By.TAG_NAME, 'img')
                alt = img.get_attribute('alt')
                print(f"\n画像alt属性: {alt}")
            except:
                pass
        
        driver.save_screenshot("rakuma_price_debug.png")
        print("\nスクリーンショット保存: rakuma_price_debug.png")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_rakuma_price()