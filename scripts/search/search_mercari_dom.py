#!/usr/bin/env python3
"""
メルカリDOM解析による確実な商品取得
"""
import sys
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote

def search_mercari_dom(query, limit=20):
    """DOM解析でメルカリ商品を検索"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    results = []
    
    try:
        # 検索URL（価格昇順）
        search_url = f"https://jp.mercari.com/search?keyword={quote(query)}&status=on_sale&sort=price&order=asc"
        print(f"検索URL: {search_url}", file=sys.stderr)
        
        driver.get(search_url)
        time.sleep(3)  # ページ読み込み待機
        
        # 商品要素を待機
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='item-cell']"))
            )
        except:
            print("商品要素が見つかりません", file=sys.stderr)
            
        # 商品を取得
        items = driver.find_elements(By.CSS_SELECTOR, "[data-testid='item-cell']")
        print(f"商品数: {len(items)}件", file=sys.stderr)
        
        for i, item in enumerate(items[:limit]):
            try:
                # 商品情報を取得
                # 価格を取得（span[class*='price']から）
                price_elem = item.find_element(By.CSS_SELECTOR, 'span[class*="price"]')
                price_text = price_elem.text.replace('¥', '').replace(',', '').replace('\n', '')
                price = int(price_text) if price_text.isdigit() else 0
                
                # タイトルを取得（.merItemThumbnailのaria-labelから）
                thumbnail_elem = item.find_element(By.CSS_SELECTOR, '.merItemThumbnail')
                aria_label = thumbnail_elem.get_attribute('aria-label') or ''
                # aria-labelから商品名を抽出（最後の価格部分を除く）
                title_parts = aria_label.split('の画像')
                title = title_parts[0] if title_parts else 'No title'
                
                # URLを取得
                link_elem = item.find_element(By.TAG_NAME, 'a')
                href = link_elem.get_attribute('href')
                if href.startswith('http'):
                    item_url = href
                else:
                    item_url = f"https://jp.mercari.com{href}"
                
                # 画像URLを取得
                img_elem = item.find_element(By.TAG_NAME, 'img')
                image_url = img_elem.get_attribute('src') or ''
                
                # SOLD状態をチェック
                sold = False
                try:
                    item.find_element(By.CSS_SELECTOR, '[aria-label*="sold"]')
                    sold = True
                except:
                    pass
                
                if not sold:  # 売り切れでない商品のみ
                    result = {
                        'id': f'dom_{i}',
                        'title': title,
                        'price': price,
                        'url': item_url,
                        'image_url': image_url,
                        'platform': 'mercari',
                        'method': 'dom_parsing',
                        'sold': sold
                    }
                    results.append(result)
                    
            except Exception as e:
                print(f"商品{i}の取得エラー: {e}", file=sys.stderr)
                continue
                
        print(f"取得成功: {len(results)}件", file=sys.stderr)
        
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        
    finally:
        driver.quit()
    
    return results

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'results': [],
            'error': '検索クエリが指定されていません'
        }, ensure_ascii=False))
        sys.exit(1)
    
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print("JSON_START")
    
    try:
        results = search_mercari_dom(query, limit)
        
        output = {
            'success': True,
            'results': results,
            'platform': 'mercari',
            'query': query,
            'method': 'dom_parsing',
            'metadata': {
                'total_results': len(results)
            }
        }
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'results': [],
            'error': str(e),
            'platform': 'mercari',
            'method': 'dom_parsing'
        }, ensure_ascii=False))
    
    print("JSON_END")

if __name__ == "__main__":
    main()