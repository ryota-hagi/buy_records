#!/usr/bin/env python3
"""
商品名検索機能のテストスクリプト
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any

def test_product_name_search(product_name: str, base_url: str = "http://localhost:3000") -> Dict[str, Any]:
    """商品名検索APIをテスト"""
    try:
        print(f"\n{'='*60}")
        print(f"商品名検索テスト: {product_name}")
        print(f"{'='*60}\n")
        
        # APIエンドポイント
        url = f"{base_url}/api/search/product-name"
        
        # パラメータ
        params = {
            "product_name": product_name,
            "limit": 20
        }
        
        print(f"リクエストURL: {url}")
        print(f"パラメータ: {json.dumps(params, ensure_ascii=False, indent=2)}")
        
        # タイマー開始
        start_time = time.time()
        
        # APIリクエスト
        response = requests.get(url, params=params, timeout=60)
        
        # 応答時間
        elapsed_time = time.time() - start_time
        
        print(f"\nステータスコード: {response.status_code}")
        print(f"応答時間: {elapsed_time:.2f}秒")
        
        if response.status_code == 200:
            data = response.json()
            
            # 基本情報
            print(f"\n[検索結果サマリー]")
            print(f"検索成功: {data.get('success', False)}")
            print(f"検索タイプ: {data.get('search_type', 'unknown')}")
            print(f"検索クエリ: {data.get('query', '')}")
            print(f"総結果数: {data.get('total_results', 0)}")
            print(f"検索プラットフォーム数: {data.get('platforms_searched', 0)}")
            
            # 関連性統計
            relevance_stats = data.get('relevance_stats', {})
            if relevance_stats:
                print(f"\n[関連性統計]")
                print(f"高関連性 (80以上): {relevance_stats.get('high_relevance', 0)}件")
                print(f"中関連性 (50-79): {relevance_stats.get('medium_relevance', 0)}件")
                print(f"低関連性 (50未満): {relevance_stats.get('low_relevance', 0)}件")
                print(f"平均スコア: {relevance_stats.get('average_score', 0)}")
            
            # プラットフォーム別結果
            platforms = data.get('platforms', {})
            if platforms:
                print(f"\n[プラットフォーム別結果]")
                for platform, items in platforms.items():
                    print(f"- {platform}: {len(items)}件")
            
            # エラー情報
            errors = data.get('errors', [])
            if errors:
                print(f"\n[エラー]")
                for error in errors:
                    print(f"- {error}")
            
            # 上位5件の結果を表示
            results = data.get('results', [])
            if results:
                print(f"\n[上位結果 (最大5件)]")
                for i, item in enumerate(results[:5], 1):
                    print(f"\n{i}. {item.get('title', 'タイトルなし')}")
                    print(f"   プラットフォーム: {item.get('platform', 'unknown')}")
                    print(f"   価格: ¥{item.get('price', 0):,}")
                    print(f"   送料: ¥{item.get('shipping_fee', 0):,}")
                    print(f"   合計: ¥{item.get('total_price', 0):,}")
                    print(f"   関連性スコア: {item.get('relevance_score', 0)}")
                    print(f"   状態: {item.get('condition', '不明')}")
                    print(f"   URL: {item.get('url', '')[:60]}...")
            
            # コスト情報
            cost_summary = data.get('cost_summary', {})
            if cost_summary and cost_summary.get('total_estimated_cost', 0) > 0:
                print(f"\n[コスト情報]")
                print(f"推定コスト: ${cost_summary.get('total_estimated_cost', 0):.4f} {cost_summary.get('currency', 'USD')}")
            
            return {
                "success": True,
                "product_name": product_name,
                "total_results": data.get('total_results', 0),
                "response_time": elapsed_time,
                "relevance_stats": relevance_stats,
                "platforms": list(platforms.keys()),
                "errors": errors
            }
            
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            print(f"\nエラー: {error_data.get('error', response.text)}")
            return {
                "success": False,
                "product_name": product_name,
                "error": error_data.get('error', response.text),
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        print(f"\nタイムアウトエラー")
        return {
            "success": False,
            "product_name": product_name,
            "error": "リクエストタイムアウト"
        }
    except Exception as e:
        print(f"\n例外エラー: {str(e)}")
        return {
            "success": False,
            "product_name": product_name,
            "error": str(e)
        }

def run_all_tests():
    """複数の商品名でテストを実行"""
    test_cases = [
        # 日本語商品名
        "Nintendo Switch",
        "サントリー 緑茶 伊右衛門",
        "iPhone 15 Pro",
        "PlayStation 5",
        "ポケモンカード",
        
        # 英語商品名
        "Sony WH-1000XM5",
        "Apple AirPods Pro",
        "Samsung Galaxy S24",
        
        # 複雑なクエリ
        "任天堂 スイッチ 有機EL",
        "Apple MacBook Pro M3"
    ]
    
    results = []
    
    for product_name in test_cases:
        result = test_product_name_search(product_name)
        results.append(result)
        time.sleep(2)  # API負荷軽減のため待機
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print("テスト結果サマリー")
    print(f"{'='*60}\n")
    
    success_count = sum(1 for r in results if r.get('success', False))
    total_count = len(results)
    
    print(f"成功: {success_count}/{total_count}")
    print(f"失敗: {total_count - success_count}/{total_count}")
    
    # 成功したテストの詳細
    print(f"\n[成功したテスト]")
    for result in results:
        if result.get('success', False):
            print(f"- {result['product_name']}: {result['total_results']}件 ({result['response_time']:.2f}秒)")
            if result.get('relevance_stats'):
                print(f"  平均関連性スコア: {result['relevance_stats'].get('average_score', 0)}")
    
    # 失敗したテストの詳細
    failed_tests = [r for r in results if not r.get('success', False)]
    if failed_tests:
        print(f"\n[失敗したテスト]")
        for result in failed_tests:
            print(f"- {result['product_name']}: {result.get('error', '不明なエラー')}")
    
    # プラットフォーム別統計
    all_platforms = set()
    for result in results:
        if result.get('success', False) and result.get('platforms'):
            all_platforms.update(result['platforms'])
    
    if all_platforms:
        print(f"\n[検索されたプラットフォーム]")
        for platform in sorted(all_platforms):
            print(f"- {platform}")

def test_single_product(product_name: str):
    """単一商品のテスト"""
    result = test_product_name_search(product_name)
    
    if result.get('success', False):
        print(f"\n✅ テスト成功")
    else:
        print(f"\n❌ テスト失敗")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # コマンドライン引数で商品名が指定された場合
        product_name = " ".join(sys.argv[1:])
        test_single_product(product_name)
    else:
        # 引数なしの場合は全テストケースを実行
        run_all_tests()