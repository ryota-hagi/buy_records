#!/usr/bin/env python3
"""
本番環境修正のテストスクリプト
JANコード検索エンジンが正常に動作するかテストします。
"""

import sys
import os
import json
import warnings
warnings.filterwarnings('ignore')

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, '.')

def test_jan_lookup():
    """JANコード商品名取得のテスト"""
    print("=== JANコード商品名取得テスト ===")
    try:
        from src.jan.jan_lookup import get_product_name_from_jan
        
        # 環境変数からテスト用JANコードを取得、なければデフォルト値を使用
        test_jan = os.environ.get('TEST_JAN_CODE', '4902370548501')
        print(f"テスト用JANコード: {test_jan}")
        
        product_name = get_product_name_from_jan(test_jan)
        
        if product_name:
            print(f"✅ 成功: JANコード {test_jan} -> {product_name}")
            return True
        else:
            print(f"❌ 失敗: JANコード {test_jan} の商品名を取得できませんでした")
            return False
            
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def test_search_engine():
    """JANコード検索エンジンのテスト"""
    print("\n=== JANコード検索エンジンテスト ===")
    try:
        from src.jan.search_engine import JANSearchEngine
        
        engine = JANSearchEngine()
        # 環境変数からテスト用JANコードを取得、なければデフォルト値を使用
        test_jan = os.environ.get('TEST_JAN_CODE', '4902370548501')
        
        print(f"JANコード {test_jan} で検索を開始...")
        results = engine.search_by_jan(test_jan, limit=5)
        
        if results:
            print(f"✅ 成功: {len(results)}件の結果を取得")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result.get('item_title', 'タイトル不明')} - ¥{result.get('total_price', 0):,}")
            return True
        else:
            print("❌ 失敗: 検索結果が取得できませんでした")
            return False
            
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def test_platform_strategies():
    """プラットフォーム戦略のテスト"""
    print("\n=== プラットフォーム戦略テスト ===")
    try:
        from src.search.platform_strategies import PlatformSearchManager
        
        manager = PlatformSearchManager()
        available_platforms = list(manager.strategies.keys())
        
        print(f"✅ 利用可能なプラットフォーム: {', '.join(available_platforms)}")
        return True
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("本番環境修正テストを開始します...\n")
    
    # 環境情報を表示
    print(f"Python バージョン: {sys.version}")
    print(f"プロジェクトルート: {project_root}")
    print(f"現在のディレクトリ: {os.getcwd()}")
    print(f"Pythonパス: {sys.path[:3]}...\n")
    
    # テスト実行
    tests = [
        ("JANコード商品名取得", test_jan_lookup),
        ("プラットフォーム戦略", test_platform_strategies),
        ("JANコード検索エンジン", test_search_engine),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name}でエラー: {e}")
    
    print(f"\n=== テスト結果 ===")
    print(f"合格: {passed}/{total}")
    
    if passed == total:
        print("✅ すべてのテストが成功しました！")
        return 0
    else:
        print("❌ 一部のテストが失敗しました")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
