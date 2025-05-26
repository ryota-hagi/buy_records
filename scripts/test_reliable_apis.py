#!/usr/bin/env python3
"""
確実なAPI検索システムのテストスクリプト
メルカリとeBayの新しい確実な検索システムをテストします。
"""

import requests
import json
import time
from datetime import datetime

def test_api_endpoint(url, params, platform_name):
    """APIエンドポイントをテストする"""
    print(f"\n{'='*50}")
    print(f"{platform_name}APIテスト開始")
    print(f"{'='*50}")
    
    test_queries = [
        "Nintendo Switch",
        "iPhone",
        "Sony PlayStation"
    ]
    
    for query in test_queries:
        print(f"\n🔍 テスト検索: {query}")
        print("-" * 30)
        
        try:
            test_params = params.copy()
            test_params['query'] = query
            test_params['limit'] = 5
            
            start_time = time.time()
            response = requests.get(url, params=test_params, timeout=60)
            end_time = time.time()
            
            print(f"ステータスコード: {response.status_code}")
            print(f"レスポンス時間: {end_time - start_time:.2f}秒")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    results = data.get('results', [])
                    print(f"成功: {len(results)}件取得")
                    print(f"プラットフォーム: {data.get('platform', 'unknown')}")
                    print(f"データソース: {data.get('data_source', 'unknown')}")
                    
                    if 'exchange_rate' in data:
                        print(f"為替レート: 1 USD = {data['exchange_rate']} JPY")
                    
                    if results:
                        print(f"最初の結果:")
                        first_result = results[0]
                        print(f"  タイトル: {first_result.get('title', 'N/A')}")
                        print(f"  価格: {first_result.get('price', 0)}円")
                        print(f"  URL: {first_result.get('url', 'N/A')}")
                        print(f"  状態: {first_result.get('condition', 'N/A')}")
                    else:
                        print("⚠️ 結果が空です")
                        if 'warning' in data:
                            print(f"警告: {data['warning']}")
                else:
                    print(f"❌ API失敗: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTPエラー: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"エラー詳細: {error_data}")
                except:
                    print(f"レスポンス: {response.text[:200]}...")
                    
        except requests.exceptions.Timeout:
            print("❌ タイムアウトエラー")
        except requests.exceptions.RequestException as e:
            print(f"❌ リクエストエラー: {str(e)}")
        except Exception as e:
            print(f"❌ 予期しないエラー: {str(e)}")

def test_unified_search():
    """統合検索APIをテストする"""
    print(f"\n{'='*50}")
    print(f"統合検索APIテスト開始")
    print(f"{'='*50}")
    
    base_url = "http://localhost:3003"
    url = f"{base_url}/api/search/all"
    
    test_queries = [
        "Nintendo Switch",
        "iPhone"
    ]
    
    for query in test_queries:
        print(f"\n🔍 統合検索テスト: {query}")
        print("-" * 30)
        
        try:
            params = {
                'query': query,
                'limit': 5
            }
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=120)
            end_time = time.time()
            
            print(f"ステータスコード: {response.status_code}")
            print(f"レスポンス時間: {end_time - start_time:.2f}秒")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    results = data.get('results', [])
                    platforms = data.get('platforms', {})
                    
                    print(f"合計結果数: {len(results)}件")
                    
                    # プラットフォーム別結果
                    for platform, platform_results in platforms.items():
                        print(f"{platform.upper()}: {len(platform_results)}件")
                    
                    if results:
                        print(f"\n最初の結果:")
                        first_result = results[0]
                        print(f"  プラットフォーム: {first_result.get('platform', 'N/A')}")
                        print(f"  タイトル: {first_result.get('title', 'N/A')}")
                        print(f"  価格: {first_result.get('price', 0)}円")
                    else:
                        print("⚠️ 統合結果が空です")
                        if 'errors' in data:
                            print(f"エラー: {data['errors']}")
                else:
                    print(f"❌ 統合検索失敗: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTPエラー: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 統合検索エラー: {str(e)}")

def main():
    print("🚀 確実なAPI検索システムテスト開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:3003"
    
    # メルカリAPIテスト
    test_api_endpoint(
        f"{base_url}/api/search/mercari",
        {},
        "メルカリ"
    )
    
    # eBayAPIテスト
    test_api_endpoint(
        f"{base_url}/api/search/ebay",
        {},
        "eBay"
    )
    
    # 統合検索テスト
    test_unified_search()
    
    print(f"\n{'='*50}")
    print("✅ テスト完了")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
