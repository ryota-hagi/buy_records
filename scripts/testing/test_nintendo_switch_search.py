#!/usr/bin/env python3
"""
Nintendo Switch JANコード検索テスト
実際のJANコード「4902370548501」でプラットフォーム検索をテストします。
"""

import sys
import os
import logging
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.search.platform_strategies import PlatformSearchManager
from src.jan.search_engine import JANSearchEngine
from src.jan.jan_lookup import get_product_name_from_jan
from src.utils.translator import translator

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_nintendo_switch_search():
    """Nintendo Switch JANコード検索をテストします"""
    print("=== Nintendo Switch JANコード検索テスト ===\n")
    
    # 実際のNintendo Switch JANコード
    jan_code = "4902370548501"
    print(f"テスト対象JANコード: {jan_code}")
    
    # JANコードから商品名を取得
    product_name = get_product_name_from_jan(jan_code)
    print(f"JANコードから取得した商品名: {product_name}")
    
    if not product_name:
        print("商品名を取得できませんでした。テストを終了します。")
        return
    
    # Google翻訳APIで英語に翻訳
    english_name = translator.translate_product_name(product_name)
    print(f"Google翻訳による英語名: {english_name}")
    print()
    
    # プラットフォーム検索管理クラスを初期化
    manager = PlatformSearchManager()
    
    # 各プラットフォームでテスト
    platforms = ['yahoo_shopping', 'mercari', 'ebay']
    
    for platform in platforms:
        print(f"--- {platform}での検索テスト ---")
        try:
            results = manager.search_platform(platform, jan_code, jan_code, 5)
            print(f"検索結果: {len(results)}件")
            
            if results:
                print("検索結果:")
                for i, item in enumerate(results, 1):
                    print(f"  {i}. {item.get('item_title', 'タイトルなし')}")
                    print(f"     価格: ¥{item.get('total_price', 0):,}")
                    print(f"     プラットフォーム: {item.get('platform', 'unknown')}")
                    print(f"     URL: {item.get('item_url', 'URLなし')}")
                    print()
            else:
                print("  結果が見つかりませんでした")
            
        except Exception as e:
            print(f"  エラー: {e}")
            import traceback
            traceback.print_exc()
        
        print()

def test_jan_search_engine():
    """JANコード検索エンジンをテストします"""
    print("=== JANコード検索エンジンテスト ===\n")
    
    engine = JANSearchEngine()
    jan_code = "4902370548501"
    
    print(f"JANコード: {jan_code}")
    print("統合検索を開始します...")
    
    try:
        results = engine.search_by_jan(jan_code, limit=20)
        print(f"統合検索結果: {len(results)}件")
        
        if results:
            print("\n--- 検索結果（価格順） ---")
            for i, item in enumerate(results, 1):
                print(f"{i}. {item.get('item_title', 'タイトルなし')}")
                print(f"   価格: ¥{item.get('total_price', 0):,}")
                print(f"   プラットフォーム: {item.get('platform', 'unknown')}")
                print(f"   URL: {item.get('item_url', 'URLなし')}")
                print()
        
        # サマリー情報
        summary = engine.get_search_summary(results)
        print("--- 検索サマリー ---")
        print(f"総件数: {summary['total_count']}")
        print(f"最安値: ¥{summary['lowest_price']:,}")
        print(f"最高値: ¥{summary['highest_price']:,}")
        print(f"平均価格: ¥{summary['average_price']:,}")
        print(f"中央値: ¥{summary['median_price']:,}")
        print(f"プラットフォーム別件数: {summary['platform_counts']}")
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    print("Nintendo Switch JANコード検索テスト")
    print("=" * 50)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 個別プラットフォーム検索テスト
        test_nintendo_switch_search()
        
        # 統合検索エンジンテスト
        test_jan_search_engine()
        
        print("=" * 50)
        print("テスト完了")
        
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
