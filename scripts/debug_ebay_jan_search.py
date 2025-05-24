#!/usr/bin/env python3
"""
eBay JANコード検索のデバッグスクリプト
"""

import sys
import os
sys.path.append('.')

from src.search.platform_strategies import EbayStrategy

def debug_ebay_jan_search():
    """eBay JANコード検索をデバッグします"""
    try:
        print("eBay JANコード検索デバッグを開始...")
        
        # eBay戦略を初期化
        strategy = EbayStrategy()
        print("eBay戦略を初期化しました")
        
        # JANコード
        jan_code = "4902370548501"
        print(f"JANコード: {jan_code}")
        
        # 検索を実行
        print("eBay検索を実行中...")
        results = strategy.search(jan_code, jan_code, limit=5)
        
        print(f"検索結果: {len(results)}件")
        
        if results:
            print("\n=== eBay検索結果 ===")
            for i, item in enumerate(results, 1):
                print(f"{i}. {item.get('item_title', 'No title')}")
                print(f"   プラットフォーム: {item.get('platform', 'Unknown')}")
                print(f"   価格: ¥{item.get('total_price', 0)}")
                print(f"   通貨: {item.get('currency', 'Unknown')}")
                print(f"   検索語: {item.get('search_term', 'Unknown')}")
                print(f"   URL: {item.get('item_url', 'No URL')}")
                print()
        else:
            print("eBayから検索結果が見つかりませんでした")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ebay_jan_search()
