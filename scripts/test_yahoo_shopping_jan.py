#!/usr/bin/env python3
"""
Yahoo!ショッピングのJANコード検索テスト
指定されたJANコードでYahoo!ショッピングの検索機能をテストします。
"""

import sys
import os
sys.path.append('.')

from src.collectors.yahoo_shopping import YahooShoppingClient
from src.jan.jan_lookup import get_product_name_from_jan

def test_yahoo_shopping_jan_search():
    """Yahoo!ショッピングのJANコード検索をテストします"""
    try:
        print("=== Yahoo!ショッピング JANコード検索テスト ===\n")
        
        # Yahoo!ショッピングクライアントを初期化
        client = YahooShoppingClient()
        print("Yahoo!ショッピングクライアントを初期化しました\n")
        
        # テスト用JANコード
        jan_code = "4902370548501"
        print(f"テスト対象JANコード: {jan_code}")
        
        # JANコードから商品名を取得
        product_name = get_product_name_from_jan(jan_code)
        print(f"JANコードから取得した商品名: {product_name}")
        
        # 1. JANコード検索をテスト
        print(f"\n--- JANコード検索テスト ---")
        jan_results = client.search_by_jan_code(jan_code, limit=5)
        print(f"JANコード検索結果: {len(jan_results)}件")
        
        if jan_results:
            print("\n=== JANコード検索結果 ===")
            for i, item in enumerate(jan_results, 1):
                print(f"{i}. {item.get('title', 'No title')}")
                print(f"   価格: ¥{item.get('price', 0):,}")
                print(f"   URL: {item.get('url', 'No URL')}")
                print(f"   ストア: {item.get('store_name', 'Unknown')}")
                print()
        else:
            print("JANコード検索で結果が見つかりませんでした")
        
        # 2. 商品名検索をテスト（フォールバック）
        if product_name:
            print(f"\n--- 商品名検索テスト ---")
            print(f"検索クエリ: {product_name}")
            name_results = client.search_items(product_name, limit=5)
            print(f"商品名検索結果: {len(name_results)}件")
            
            if name_results:
                print("\n=== 商品名検索結果 ===")
                for i, item in enumerate(name_results, 1):
                    print(f"{i}. {item.get('title', 'No title')}")
                    print(f"   価格: ¥{item.get('price', 0):,}")
                    print(f"   URL: {item.get('url', 'No URL')}")
                    print(f"   ストア: {item.get('store_name', 'Unknown')}")
                    print()
            else:
                print("商品名検索で結果が見つかりませんでした")
        
        # 3. 一般的な商品名での検索テスト
        print(f"\n--- 一般的な商品名検索テスト ---")
        test_query = "Nintendo Switch"
        print(f"検索クエリ: {test_query}")
        general_results = client.search_items(test_query, limit=3)
        print(f"一般検索結果: {len(general_results)}件")
        
        if general_results:
            print("\n=== 一般検索結果 ===")
            for i, item in enumerate(general_results, 1):
                print(f"{i}. {item.get('title', 'No title')}")
                print(f"   価格: ¥{item.get('price', 0):,}")
                print(f"   URL: {item.get('url', 'No URL')}")
                print(f"   ストア: {item.get('store_name', 'Unknown')}")
                print()
        else:
            print("一般検索で結果が見つかりませんでした")
        
        print(f"\n{'='*50}")
        print("テスト完了")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yahoo_shopping_jan_search()
