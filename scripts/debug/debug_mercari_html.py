#!/usr/bin/env python3
"""
メルカリHTMLデバッグスクリプト
実際のHTMLコンテンツを詳しく調査します。
"""

import requests
import re
import json
from urllib.parse import quote

def debug_mercari_html(keyword):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    url = f'https://jp.mercari.com/search?keyword={quote(keyword)}&status=on_sale&sort=price&order=asc'
    print(f"URL: {url}")
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Content-Length: {len(response.text)}")
    
    # __NEXT_DATA__を探す
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text, re.DOTALL)
    
    if match:
        print("\n__NEXT_DATA__ found!")
        try:
            data = json.loads(match.group(1))
            
            # データ構造を調査
            print("\n=== Top-level keys ===")
            for key in data.keys():
                print(f"- {key}: {type(data[key]).__name__}")
            
            # propsを詳しく見る
            if 'props' in data:
                props = data['props']
                print("\n=== props keys ===")
                for key in props.keys():
                    print(f"- {key}: {type(props[key]).__name__}")
                
                # pagePropsを詳しく見る
                if 'pageProps' in props:
                    page_props = props['pageProps']
                    print("\n=== pageProps keys ===")
                    for key in page_props.keys():
                        value_type = type(page_props[key]).__name__
                        if isinstance(page_props[key], list):
                            print(f"- {key}: List[{len(page_props[key])}]")
                        elif isinstance(page_props[key], dict):
                            print(f"- {key}: Dict[{len(page_props[key])} keys]")
                        else:
                            print(f"- {key}: {value_type}")
                    
                    # 各キーの中身を探る
                    for key, value in page_props.items():
                        if isinstance(value, dict) and len(value) > 0:
                            print(f"\n=== pageProps.{key} keys ===")
                            for k in list(value.keys())[:10]:
                                print(f"  - {k}")
                        elif isinstance(value, list) and len(value) > 0:
                            print(f"\n=== pageProps.{key}[0] ===")
                            if isinstance(value[0], dict):
                                for k in list(value[0].keys())[:10]:
                                    print(f"  - {k}")
            
            # 商品データを探す
            def find_items(obj, path="", depth=0):
                if depth > 5:
                    return
                
                if isinstance(obj, dict):
                    # 商品っぽいデータを探す
                    if 'items' in obj or 'itemList' in obj or 'searchResult' in obj:
                        print(f"\n=== Potential items at {path} ===")
                        for k in obj.keys():
                            print(f"  - {k}")
                    
                    for k, v in obj.items():
                        find_items(v, f"{path}.{k}", depth + 1)
                elif isinstance(obj, list) and len(obj) > 0:
                    if isinstance(obj[0], dict) and ('id' in obj[0] or 'itemId' in obj[0]):
                        print(f"\n=== Item list found at {path} ({len(obj)} items) ===")
                        print(f"First item keys: {list(obj[0].keys())[:10]}")
                        # サンプルデータを表示
                        item = obj[0]
                        print(f"Sample item:")
                        for k in ['id', 'name', 'price', 'itemId', 'itemName', 'itemPrice']:
                            if k in item:
                                print(f"  {k}: {item[k]}")
            
            find_items(data)
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
    else:
        print("\n__NEXT_DATA__ not found in the expected format")
    
    # その他のパターンを探す
    print("\n=== Other patterns ===")
    
    # 商品IDパターン
    item_patterns = [
        r'/item/(m\d+)',
        r'"itemId":"(m\d+)"',
        r'"id":"(m\d+)"',
        r'data-item-id="(m\d+)"',
    ]
    
    for pattern in item_patterns:
        matches = re.findall(pattern, response.text)
        if matches:
            print(f"Pattern '{pattern}' found {len(set(matches))} unique matches")
            print(f"  Samples: {list(set(matches))[:3]}")
    
    # HTMLの一部を保存（デバッグ用）
    with open('mercari_debug.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("\nFull HTML saved to mercari_debug.html")

if __name__ == "__main__":
    debug_mercari_html("Nintendo Switch")