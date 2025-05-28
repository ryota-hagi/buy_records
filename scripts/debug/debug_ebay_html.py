#!/usr/bin/env python3
"""
eBay HTMLデバッグスクリプト
実際のHTML構造を調査してパーサーを改善
"""

import requests
import sys
from bs4 import BeautifulSoup
from urllib.parse import quote

def debug_ebay_html():
    """eBayのHTML構造をデバッグ"""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    keyword = "Nintendo Switch"
    search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}&_sacat=0&_sop=15&LH_BIN=1"
    
    print(f"検索URL: {search_url}")
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        response = session.get(search_url, timeout=20)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンスサイズ: {len(response.text)} 文字")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 様々なセレクタを試行
            selectors_to_try = [
                'div.s-item__wrapper',
                'div.s-item',
                'div[data-view="mi:1686"]',
                '.srp-results .s-item',
                '.srp-river-results .s-item'
            ]
            
            for selector in selectors_to_try:
                items = soup.select(selector)
                print(f"\nセレクタ '{selector}': {len(items)}件")
                
                if items and len(items) > 0:
                    # 最初のアイテムの詳細を調査
                    first_item = items[0]
                    print(f"最初のアイテムのクラス: {first_item.get('class', [])}")
                    
                    # タイトル要素を探す
                    title_selectors = [
                        'h3.s-item__title',
                        '.s-item__title',
                        'h3[role="heading"]',
                        '.it-ttl',
                        'a.s-item__link'
                    ]
                    
                    for title_sel in title_selectors:
                        title_elem = first_item.select_one(title_sel)
                        if title_elem:
                            title_text = title_elem.get_text(strip=True)
                            print(f"  タイトル ({title_sel}): {title_text[:100]}")
                    
                    # 価格要素を探す
                    price_selectors = [
                        '.s-item__price .notranslate',
                        '.s-item__price',
                        '.u-flL.condText',
                        '.it-price'
                    ]
                    
                    for price_sel in price_selectors:
                        price_elem = first_item.select_one(price_sel)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            print(f"  価格 ({price_sel}): {price_text}")
                    
                    # URL要素を探す
                    link_elem = first_item.select_one('a')
                    if link_elem:
                        href = link_elem.get('href', '')
                        print(f"  URL: {href[:100]}")
                    
                    # 最初のアイテムのHTML構造を出力（最初の500文字）
                    print(f"\n最初のアイテムのHTML構造:")
                    print(str(first_item)[:1000])
                    print("...")
                    
                    break
            
            # 全体のHTML構造の一部を保存
            with open('ebay_debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"\n完全なHTMLを ebay_debug.html に保存しました")
            
        else:
            print(f"HTTPエラー: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"例外発生: {str(e)}")

if __name__ == "__main__":
    debug_ebay_html()
