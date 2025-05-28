#!/usr/bin/env python3
"""
eBay検索のテストスクリプト
"""

import sys
import os
sys.path.append('.')

from src.collectors.ebay import EbayClient

def test_ebay_search():
    """eBay検索をテストします"""
    try:
        print("eBay検索テストを開始...")
        
        # eBayクライアントを初期化
        client = EbayClient()
        print("eBayクライアントを初期化しました")
        
        # Nintendo Switchで検索
        search_term = "Nintendo Switch"
        print(f"検索キーワード: {search_term}")
        
        # アクティブな商品を検索
        print("アクティブな商品を検索中...")
        results = client.search_active_items(search_term, limit=5)
        
        print(f"検索結果: {len(results)}件")
        
        if results:
            print("\n=== 検索結果 ===")
            for i, item in enumerate(results, 1):
                print(f"{i}. {item.get('title', 'No title')}")
                print(f"   価格: ${item.get('price', 0)} {item.get('currency', 'USD')}")
                print(f"   コンディション: {item.get('condition', 'Unknown')}")
                print(f"   URL: {item.get('url', 'No URL')}")
                print()
        else:
            print("検索結果が見つかりませんでした")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ebay_search()
