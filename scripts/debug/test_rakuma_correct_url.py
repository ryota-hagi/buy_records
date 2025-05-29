#!/usr/bin/env python3
"""
ラクマの正しいURL構造をテスト
"""
import requests
from bs4 import BeautifulSoup
import urllib.parse

def test_rakuma_urls():
    """様々なラクマのURL形式をテスト"""
    print("=== Testing Rakuma URL Formats ===\n")
    
    keyword = "Nintendo Switch"
    encoded_keyword = urllib.parse.quote(keyword)
    
    # テストするURL形式
    test_urls = [
        f"https://rakuma.rakuten.co.jp/search/{encoded_keyword}",
        f"https://fril.jp/search/{encoded_keyword}",
        f"https://rakuma.rakuten.co.jp/s/{encoded_keyword}",
        f"https://rakuma.rakuten.co.jp/search?keyword={encoded_keyword}",
        f"https://fril.jp/s/{encoded_keyword}",
        f"https://rakuma.rakuten.co.jp/category/1328/?keyword={encoded_keyword}",
        f"https://fril.jp/search?query={encoded_keyword}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for url in test_urls:
        print(f"Testing: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            print(f"  Status: {response.status_code}")
            print(f"  Final URL: {response.url}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('title')
                print(f"  Title: {title.text if title else 'No title'}")
                
                # 商品らしき要素を探す
                possible_items = [
                    soup.find_all('div', class_=lambda x: x and 'item' in x.lower()),
                    soup.find_all('article'),
                    soup.find_all('li', class_=lambda x: x and 'product' in x.lower()),
                    soup.find_all('div', class_=lambda x: x and 'card' in x.lower())
                ]
                
                for items in possible_items:
                    if items:
                        print(f"  Found {len(items)} potential items")
                        break
                
                print("  ✅ Success!\n")
                return response.url
            else:
                print("  ❌ Failed\n")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}\n")
    
    return None

def get_rakuma_search_api():
    """ラクマのAPIエンドポイントを探す"""
    print("\n=== Checking Rakuma API ===\n")
    
    # ラクマの公式サイトをチェック
    url = "https://rakuma.rakuten.co.jp/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"✅ Rakuma main page accessible")
            print(f"   URL: {response.url}")
            
            # JavaScriptからAPIエンドポイントを探す
            if 'api' in response.text.lower():
                print("   Found potential API references in page")
                
            # 検索ページを直接アクセス
            search_url = "https://fril.jp/search"
            response = requests.get(search_url, headers=headers)
            print(f"\n✅ Search page status: {response.status_code}")
            print(f"   URL: {response.url}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # URL形式をテスト
    working_url = test_rakuma_urls()
    
    if working_url:
        print(f"\n✅ Working URL format found: {working_url}")
    else:
        print("\n❌ No working URL format found")
    
    # API情報を確認
    get_rakuma_search_api()