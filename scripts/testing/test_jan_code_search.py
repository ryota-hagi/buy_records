#!/usr/bin/env python3
"""
JANコード検索の実際のテストスクリプト
"""

import sys
import os
sys.path.append('.')

from src.collectors.ebay import EbayClient
from src.collectors.yahoo_shopping import YahooShoppingClient

def test_jan_code_search():
    """JANコード検索をテストします"""
    
    # テスト用JANコード（Nintendo Switch Pro コントローラー）
    jan_code = "4902370542912"
    print(f"=== JANコード検索テスト: {jan_code} ===")
    print("商品名: Nintendo Switch Pro コントローラー")
    print()
    
    # eBay検索テスト
    print("--- eBay検索テスト ---")
    try:
        ebay_client = EbayClient()
        print("eBayクライアントを初期化しました")
        
        # JANコードで検索
        ebay_results = ebay_client.search_active_items(jan_code, limit=10)
        print(f"eBay検索結果: {len(ebay_results)}件")
        
        if ebay_results:
            print("\n=== eBay検索結果 ===")
            for i, item in enumerate(ebay_results[:3], 1):
                print(f"{i}. {item.get('title', 'No title')}")
                print(f"   価格: ${item.get('price', 0)} {item.get('currency', 'USD')}")
                print(f"   URL: {item.get('url', 'No URL')}")
                print()
        else:
            print("eBayでJANコードの検索結果が見つかりませんでした")
            
    except Exception as e:
        print(f"eBay検索エラー: {e}")
    
    print()
    
    # Yahoo Shopping検索テスト
    print("--- Yahoo Shopping検索テスト ---")
    try:
        yahoo_client = YahooShoppingClient()
        print("Yahoo Shoppingクライアントを初期化しました")
        
        # JANコードで検索
        yahoo_results = yahoo_client.search_by_jan_code(jan_code, limit=10)
        print(f"Yahoo Shopping検索結果: {len(yahoo_results)}件")
        
        if yahoo_results:
            print("\n=== Yahoo Shopping検索結果 ===")
            for i, item in enumerate(yahoo_results[:3], 1):
                print(f"{i}. {item.get('name', 'No name')}")
                print(f"   価格: ¥{item.get('price', 0)}")
                print(f"   URL: {item.get('url', 'No URL')}")
                print()
        else:
            print("Yahoo ShoppingでJANコードの検索結果が見つかりませんでした")
            
    except Exception as e:
        print(f"Yahoo Shopping検索エラー: {e}")
    
    print()
    print("=== テスト完了 ===")

if __name__ == "__main__":
    test_jan_code_search()
