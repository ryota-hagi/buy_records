#!/usr/bin/env python3
"""
現在のメルカリとeBay APIの動作テスト
"""

import requests
import json
import time
from datetime import datetime

def test_mercari_api():
    """メルカリAPIのテスト"""
    print("=" * 50)
    print("メルカリAPIテスト開始")
    print("=" * 50)
    
    # テスト用の商品名
    test_queries = [
        "Nintendo Switch",
        "iPhone",
        "サントリー 伊右衛門"
    ]
    
    base_url = "http://localhost:3002/api/search/mercari"
    
    for query in test_queries:
        print(f"\n🔍 テスト検索: {query}")
        print("-" * 30)
        
        try:
            # GETリクエストでテスト
            response = requests.get(base_url, params={
                'query': query,
                'limit': 5
            }, timeout=30)
            
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"成功: {data.get('total_results', 0)}件取得")
                print(f"プラットフォーム: {data.get('platform', 'unknown')}")
                print(f"データソース: {data.get('data_source', 'unknown')}")
                
                if data.get('results'):
                    first_item = data['results'][0]
                    print(f"最初の商品: {first_item.get('title', 'タイトルなし')[:50]}...")
                    print(f"価格: {first_item.get('price', 0)}円")
                else:
                    print("⚠️ 結果が空です")
                    if data.get('warning'):
                        print(f"警告: {data['warning']}")
                    if data.get('error'):
                        print(f"エラー: {data['error']}")
            else:
                print(f"❌ エラー: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"エラー詳細: {error_data}")
                except:
                    print(f"レスポンス: {response.text[:200]}...")
                    
        except requests.exceptions.Timeout:
            print("❌ タイムアウトエラー")
        except requests.exceptions.ConnectionError:
            print("❌ 接続エラー - サーバーが起動していない可能性があります")
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
        
        time.sleep(2)  # レート制限対策

def test_ebay_api():
    """eBay APIのテスト"""
    print("\n" + "=" * 50)
    print("eBay APIテスト開始")
    print("=" * 50)
    
    # テスト用の商品名
    test_queries = [
        "Nintendo Switch",
        "iPhone",
        "Sony PlayStation"
    ]
    
    base_url = "http://localhost:3002/api/search/ebay"
    
    for query in test_queries:
        print(f"\n🔍 テスト検索: {query}")
        print("-" * 30)
        
        try:
            # GETリクエストでテスト
            response = requests.get(base_url, params={
                'query': query,
                'limit': 5
            }, timeout=30)
            
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"成功: {data.get('total_results', 0)}件取得")
                print(f"プラットフォーム: {data.get('platform', 'unknown')}")
                
                if data.get('exchange_rate'):
                    print(f"為替レート: 1 USD = {data['exchange_rate']} JPY")
                
                if data.get('results'):
                    first_item = data['results'][0]
                    print(f"最初の商品: {first_item.get('title', 'タイトルなし')[:50]}...")
                    print(f"価格: {first_item.get('price', 0)}円")
                    print(f"送料: {first_item.get('shipping_fee', 0)}円")
                    print(f"合計: {first_item.get('total_price', 0)}円")
                else:
                    print("⚠️ 結果が空です")
                    if data.get('warning'):
                        print(f"警告: {data['warning']}")
                    if data.get('error'):
                        print(f"エラー: {data['error']}")
            else:
                print(f"❌ エラー: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"エラー詳細: {error_data}")
                except:
                    print(f"レスポンス: {response.text[:200]}...")
                    
        except requests.exceptions.Timeout:
            print("❌ タイムアウトエラー")
        except requests.exceptions.ConnectionError:
            print("❌ 接続エラー - サーバーが起動していない可能性があります")
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
        
        time.sleep(2)  # レート制限対策

def test_unified_search():
    """統合検索のテスト"""
    print("\n" + "=" * 50)
    print("統合検索APIテスト開始")
    print("=" * 50)
    
    test_query = "Nintendo Switch"
    base_url = "http://localhost:3002/api/search/all"
    
    print(f"\n🔍 統合検索テスト: {test_query}")
    print("-" * 30)
    
    try:
        response = requests.get(base_url, params={
            'query': test_query,
            'limit': 5
        }, timeout=60)  # 統合検索は時間がかかる可能性
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 各プラットフォームの結果を確認
            platforms = ['yahoo', 'ebay', 'mercari']
            total_results = 0
            
            for platform in platforms:
                platform_data = data.get(platform, {})
                platform_results = platform_data.get('total_results', 0)
                total_results += platform_results
                
                print(f"{platform.upper()}: {platform_results}件")
                if platform_data.get('warning'):
                    print(f"  ⚠️ {platform_data['warning']}")
                if platform_data.get('error'):
                    print(f"  ❌ {platform_data['error']}")
            
            print(f"\n合計結果数: {total_results}件")
            
            # 統合結果の確認
            if data.get('combined_results'):
                combined_count = len(data['combined_results'])
                print(f"統合結果: {combined_count}件")
                
                if combined_count > 0:
                    first_item = data['combined_results'][0]
                    print(f"最初の商品: {first_item.get('title', 'タイトルなし')[:50]}...")
                    print(f"プラットフォーム: {first_item.get('platform', 'unknown')}")
                    print(f"価格: {first_item.get('total_price', 0)}円")
            else:
                print("⚠️ 統合結果が空です")
                
        else:
            print(f"❌ エラー: {response.status_code}")
            try:
                error_data = response.json()
                print(f"エラー詳細: {error_data}")
            except:
                print(f"レスポンス: {response.text[:200]}...")
                
    except requests.exceptions.Timeout:
        print("❌ タイムアウトエラー")
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー - サーバーが起動していない可能性があります")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")

def main():
    """メイン実行関数"""
    print("🚀 API動作テスト開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 各APIをテスト
    test_mercari_api()
    test_ebay_api()
    test_unified_search()
    
    print("\n" + "=" * 50)
    print("✅ テスト完了")
    print("=" * 50)

if __name__ == "__main__":
    main()
