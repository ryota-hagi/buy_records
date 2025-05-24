#!/usr/bin/env python3
"""
改善されたeBay検索機能のテストスクリプト
複数クエリ生成、リトライ機能、品質フィルタリングをテストします。
"""

import sys
import os
import logging
sys.path.append('.')

from src.search.platform_strategies import EbayStrategy
from src.jan.jan_lookup import get_product_name_from_jan
from src.utils.translator import translator

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_improved_ebay_search():
    """改善されたeBay検索機能をテストします"""
    try:
        print("=== 改善されたeBay検索機能テスト ===\n")
        
        # eBay戦略を初期化
        strategy = EbayStrategy()
        print("eBay戦略を初期化しました\n")
        
        # テストケース1: JANコードから商品名を取得してeBay検索
        jan_code = "4901777300446"  # サントリー 緑茶 伊右衛門 600ml ペット
        print(f"テストケース1: JANコード検索")
        print(f"JANコード: {jan_code}")
        
        # JANコードから商品名を取得
        product_name = get_product_name_from_jan(jan_code)
        print(f"商品名: {product_name}")
        
        if product_name:
            # 複数クエリ生成をテスト
            print(f"\n--- 複数クエリ生成テスト ---")
            queries = translator.generate_multiple_queries(product_name)
            print(f"生成されたクエリ数: {len(queries)}")
            for i, query in enumerate(queries, 1):
                print(f"  {i}. {query}")
            
            # eBay検索を実行
            print(f"\n--- eBay検索実行 ---")
            results = strategy.search(product_name, jan_code, limit=5)
            
            print(f"検索結果: {len(results)}件")
            
            if results:
                print("\n=== eBay検索結果 ===")
                for i, item in enumerate(results, 1):
                    print(f"{i}. {item.get('item_title', 'No title')}")
                    print(f"   プラットフォーム: {item.get('platform', 'Unknown')}")
                    print(f"   価格: ¥{item.get('total_price', 0):,}")
                    print(f"   通貨: {item.get('currency', 'Unknown')}")
                    print(f"   検索語: {item.get('search_term', 'Unknown')}")
                    print(f"   関連性スコア: {item.get('relevance_score', 'N/A')}")
                    print(f"   コンディション: {item.get('item_condition', 'Unknown')}")
                    print(f"   URL: {item.get('item_url', 'No URL')}")
                    print()
            else:
                print("eBayから検索結果が見つかりませんでした")
        
        # テストケース2: 直接商品名での検索
        print(f"\n{'='*50}")
        print(f"テストケース2: 直接商品名検索")
        test_product = "Nintendo Switch"
        print(f"商品名: {test_product}")
        
        # 複数クエリ生成をテスト
        print(f"\n--- 複数クエリ生成テスト ---")
        queries = translator.generate_multiple_queries(test_product)
        print(f"生成されたクエリ数: {len(queries)}")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
        
        # eBay検索を実行
        print(f"\n--- eBay検索実行 ---")
        results = strategy.search(test_product, limit=3)
        
        print(f"検索結果: {len(results)}件")
        
        if results:
            print("\n=== eBay検索結果 ===")
            for i, item in enumerate(results, 1):
                print(f"{i}. {item.get('item_title', 'No title')}")
                print(f"   プラットフォーム: {item.get('platform', 'Unknown')}")
                print(f"   価格: ¥{item.get('total_price', 0):,}")
                print(f"   通貨: {item.get('currency', 'Unknown')}")
                print(f"   検索語: {item.get('search_term', 'Unknown')}")
                print(f"   関連性スコア: {item.get('relevance_score', 'N/A')}")
                print(f"   コンディション: {item.get('item_condition', 'Unknown')}")
                print(f"   URL: {item.get('item_url', 'No URL')}")
                print()
        else:
            print("eBayから検索結果が見つかりませんでした")
        
        # テストケース3: 日本語商品名での検索
        print(f"\n{'='*50}")
        print(f"テストケース3: 日本語商品名検索")
        japanese_product = "ポケモンカード"
        print(f"商品名: {japanese_product}")
        
        # 複数クエリ生成をテスト
        print(f"\n--- 複数クエリ生成テスト ---")
        queries = translator.generate_multiple_queries(japanese_product)
        print(f"生成されたクエリ数: {len(queries)}")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
        
        # eBay検索を実行
        print(f"\n--- eBay検索実行 ---")
        results = strategy.search(japanese_product, limit=3)
        
        print(f"検索結果: {len(results)}件")
        
        if results:
            print("\n=== eBay検索結果 ===")
            for i, item in enumerate(results, 1):
                print(f"{i}. {item.get('item_title', 'No title')}")
                print(f"   プラットフォーム: {item.get('platform', 'Unknown')}")
                print(f"   価格: ¥{item.get('total_price', 0):,}")
                print(f"   通貨: {item.get('currency', 'Unknown')}")
                print(f"   検索語: {item.get('search_term', 'Unknown')}")
                print(f"   関連性スコア: {item.get('relevance_score', 'N/A')}")
                print(f"   コンディション: {item.get('item_condition', 'Unknown')}")
                print(f"   URL: {item.get('item_url', 'No URL')}")
                print()
        else:
            print("eBayから検索結果が見つかりませんでした")
        
        print(f"\n{'='*50}")
        print("テスト完了")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def test_translation_features():
    """翻訳機能の改善をテストします"""
    try:
        print("\n=== 翻訳機能改善テスト ===\n")
        
        test_products = [
            "サントリー 緑茶 伊右衛門 600ml ペット",
            "Nintendo Switch 本体",
            "ポケモンカード ピカチュウ",
            "コカ・コーラ 500ml 24本",
            "iPhone 15 Pro Max"
        ]
        
        for product in test_products:
            print(f"商品名: {product}")
            
            # 基本翻訳
            basic_translation = translator.translate_product_name(product)
            print(f"基本翻訳: {basic_translation}")
            
            # 複数クエリ生成
            queries = translator.generate_multiple_queries(product)
            print(f"複数クエリ ({len(queries)}個):")
            for i, query in enumerate(queries, 1):
                print(f"  {i}. {query}")
            
            print("-" * 40)
        
    except Exception as e:
        print(f"翻訳テストでエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 翻訳機能テスト
    test_translation_features()
    
    # eBay検索テスト
    test_improved_ebay_search()
