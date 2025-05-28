#!/usr/bin/env python3
"""
プラットフォーム別検索戦略のテストスクリプト
新しい検索戦略が正しく動作するかテストします。
"""

import sys
import os
import logging
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.search.platform_strategies import PlatformSearchManager
from src.jan.search_engine import JANSearchEngine
from src.utils.translator import translator, translate_for_platform

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_translator():
    """翻訳機能をテストします"""
    print("\n=== Google Cloud Translation API翻訳機能テスト ===")
    
    test_cases = [
        "アサヒ ビール",
        "コカコーラ 炭酸水",
        "明治 チョコレート",
        "カルビー ポテトチップス",
        "サントリー 緑茶"
    ]
    
    for product_name in test_cases:
        translated = translator.translate_product_name(product_name)
        print(f"日本語: {product_name}")
        print(f"英語: {translated}")
        print(f"eBay用: {translate_for_platform(product_name, 'ebay')}")
        print(f"メルカリ用: {translate_for_platform(product_name, 'mercari')}")
        print("-" * 50)

def test_platform_strategies():
    """プラットフォーム戦略をテストします"""
    print("\n=== プラットフォーム戦略テスト ===")
    
    manager = PlatformSearchManager()
    
    # テスト用JANコード（アサヒビール）
    jan_code = "4901777119963"
    product_name = "アサヒ ビール"
    
    platforms = ['yahoo_shopping', 'mercari', 'ebay']
    
    for platform in platforms:
        print(f"\n--- {platform}での検索テスト ---")
        try:
            # JANコード検索
            results = manager.search_platform(platform, jan_code, jan_code, 5)
            print(f"JANコード検索結果: {len(results)}件")
            
            if results:
                for i, item in enumerate(results[:2]):  # 最初の2件を表示
                    print(f"  {i+1}. {item.get('item_title', 'タイトルなし')}")
                    print(f"     価格: {item.get('total_price', 0)}円")
                    print(f"     プラットフォーム: {item.get('platform', 'unknown')}")
            
            # 商品名検索
            results = manager.search_platform(platform, product_name, None, 5)
            print(f"商品名検索結果: {len(results)}件")
            
        except Exception as e:
            print(f"エラー: {e}")

def test_jan_search_engine():
    """JANコード検索エンジンをテストします"""
    print("\n=== JANコード検索エンジンテスト ===")
    
    engine = JANSearchEngine()
    
    # テスト用JANコード
    jan_code = "4901777119963"
    
    print(f"JANコード: {jan_code}")
    print("検索を開始します...")
    
    try:
        # JANコード検索
        results = engine.search_by_jan(jan_code, limit=10)
        print(f"検索結果: {len(results)}件")
        
        if results:
            print("\n--- 検索結果（上位5件） ---")
            for i, item in enumerate(results[:5]):
                print(f"{i+1}. {item.get('item_title', 'タイトルなし')}")
                print(f"   価格: {item.get('total_price', 0)}円")
                print(f"   プラットフォーム: {item.get('platform', 'unknown')}")
                print(f"   URL: {item.get('item_url', 'URLなし')}")
                print()
        
        # サマリー情報
        summary = engine.get_search_summary(results)
        print("--- 検索サマリー ---")
        print(f"総件数: {summary['total_count']}")
        print(f"最安値: {summary['lowest_price']}円")
        print(f"最高値: {summary['highest_price']}円")
        print(f"平均価格: {summary['average_price']}円")
        print(f"中央値: {summary['median_price']}円")
        print(f"プラットフォーム別件数: {summary['platform_counts']}")
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

def test_product_name_search():
    """商品名検索をテストします"""
    print("\n=== 商品名検索テスト ===")
    
    engine = JANSearchEngine()
    
    product_name = "アサヒ ビール"
    
    print(f"商品名: {product_name}")
    print("検索を開始します...")
    
    try:
        results = engine.search_by_product_name(product_name, limit=10)
        print(f"検索結果: {len(results)}件")
        
        if results:
            print("\n--- 検索結果（上位3件） ---")
            for i, item in enumerate(results[:3]):
                print(f"{i+1}. {item.get('item_title', 'タイトルなし')}")
                print(f"   価格: {item.get('total_price', 0)}円")
                print(f"   プラットフォーム: {item.get('platform', 'unknown')}")
                print()
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    print("プラットフォーム別検索戦略テスト")
    print("=" * 50)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 翻訳機能テスト
        test_translator()
        
        # プラットフォーム戦略テスト
        test_platform_strategies()
        
        # JANコード検索エンジンテスト
        test_jan_search_engine()
        
        # 商品名検索テスト
        test_product_name_search()
        
        print("\n=== テスト完了 ===")
        print("すべてのテストが完了しました。")
        
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
