#!/usr/bin/env python3
"""
強制再デプロイとテスト
"""

import requests
import json
import time
from datetime import datetime

def force_redeploy_test():
    """強制再デプロイ後のテスト"""
    
    print("🔄 強制再デプロイ後のテスト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    print("📝 手動デプロイ手順:")
    print("1. Vercelダッシュボード (https://vercel.com/dashboard) にアクセス")
    print("2. buy-records プロジェクトを選択")
    print("3. 'Deployments' タブをクリック")
    print("4. 最新のコミット (d0f7dd9) の '...' メニューから 'Redeploy' を選択")
    print("5. 'Redeploy' ボタンをクリック")
    print()
    
    # 長めの待機時間
    print("⏳ デプロイ完了を待機中（60秒）...")
    time.sleep(60)
    
    base_url = "https://buy-records.vercel.app"
    
    # 段階的テスト
    print("\n🔍 段階的テスト開始")
    print("-" * 50)
    
    # 1. 基本接続確認
    try:
        response = requests.get(base_url, timeout=10)
        print(f"✅ サイト基本接続: {response.status_code}")
    except Exception as e:
        print(f"❌ サイト接続失敗: {str(e)}")
        return
    
    # 2. 各エンドポイントを順次確認
    endpoints = [
        "/api/search/yahoo",
        "/api/search/ebay", 
        "/api/search/mercari",
        "/api/search/all",
        "/api/test-production"
    ]
    
    endpoint_results = {}
    
    for endpoint in endpoints:
        print(f"\n📍 {endpoint} 確認中...")
        
        for attempt in range(3):  # 3回試行
            try:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, timeout=15)
                
                if response.status_code == 404:
                    if attempt < 2:
                        print(f"   試行{attempt+1}: 404 - 再試行中...")
                        time.sleep(10)
                        continue
                    else:
                        print(f"   ❌ 最終結果: 404 (デプロイ未完了)")
                        endpoint_results[endpoint] = "404"
                        break
                elif response.status_code == 400:
                    print(f"   ✅ 成功: 400 (正常なパラメータエラー)")
                    endpoint_results[endpoint] = "400"
                    break
                elif response.status_code == 500:
                    print(f"   ⚠️  成功: 500 (サーバーエラー - エンドポイント存在)")
                    endpoint_results[endpoint] = "500"
                    break
                else:
                    print(f"   ❓ 成功: {response.status_code}")
                    endpoint_results[endpoint] = str(response.status_code)
                    break
                    
            except Exception as e:
                if attempt < 2:
                    print(f"   試行{attempt+1}: エラー - 再試行中...")
                    time.sleep(10)
                    continue
                else:
                    print(f"   ❌ 最終結果: 接続エラー ({str(e)})")
                    endpoint_results[endpoint] = "error"
                    break
    
    # 3. 実際のAPI呼び出しテスト
    print(f"\n🧪 実際のAPI呼び出しテスト")
    print("-" * 50)
    
    jan_code = "4902370536485"
    api_test_results = {}
    
    # eBayテスト（トークン更新済み）
    if endpoint_results.get("/api/search/ebay") in ["400", "500"]:
        print(f"\n🔍 eBay API実行テスト")
        try:
            url = f"{base_url}/api/search/ebay"
            params = {'jan_code': jan_code, 'limit': 3}
            
            response = requests.get(url, params=params, timeout=30)
            print(f"   ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    count = len(data.get('results', []))
                    print(f"   ✅ eBay成功: {count}件取得")
                    api_test_results['eBay'] = 'success'
                else:
                    error = data.get('error', 'Unknown')
                    print(f"   ❌ eBayエラー: {error}")
                    api_test_results['eBay'] = f'api_error: {error}'
            else:
                print(f"   ❌ eBay HTTPエラー: {response.status_code}")
                api_test_results['eBay'] = f'http_error: {response.status_code}'
                
        except Exception as e:
            print(f"   ❌ eBayテストエラー: {str(e)}")
            api_test_results['eBay'] = f'error: {str(e)}'
    else:
        print(f"   ❌ eBayスキップ: エンドポイント未デプロイ")
        api_test_results['eBay'] = 'endpoint_missing'
    
    # Mercariテスト
    if endpoint_results.get("/api/search/mercari") in ["400", "500"]:
        print(f"\n🔍 Mercari API実行テスト")
        try:
            url = f"{base_url}/api/search/mercari"
            params = {'jan_code': jan_code, 'limit': 3}
            
            response = requests.get(url, params=params, timeout=30)
            print(f"   ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    count = len(data.get('results', []))
                    print(f"   ✅ Mercari成功: {count}件取得")
                    api_test_results['Mercari'] = 'success'
                else:
                    error = data.get('error', 'Unknown')
                    print(f"   ❌ Mercariエラー: {error}")
                    api_test_results['Mercari'] = f'api_error: {error}'
            else:
                print(f"   ❌ Mercari HTTPエラー: {response.status_code}")
                api_test_results['Mercari'] = f'http_error: {response.status_code}'
                
        except Exception as e:
            print(f"   ❌ Mercariテストエラー: {str(e)}")
            api_test_results['Mercari'] = f'error: {str(e)}'
    else:
        print(f"   ❌ Mercariスキップ: エンドポイント未デプロイ")
        api_test_results['Mercari'] = 'endpoint_missing'
    
    # 統合検索テスト
    if endpoint_results.get("/api/search/all") in ["400", "500"]:
        print(f"\n🔍 統合検索API実行テスト")
        try:
            url = f"{base_url}/api/search/all"
            params = {'jan_code': jan_code, 'limit': 3}
            
            response = requests.get(url, params=params, timeout=60)
            print(f"   ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    total = data.get('total_results', 0)
                    platforms = data.get('platforms', {})
                    print(f"   ✅ 統合検索成功: {total}件")
                    for platform, items in platforms.items():
                        count = len(items) if isinstance(items, list) else 0
                        print(f"     {platform}: {count}件")
                    api_test_results['統合検索'] = 'success'
                else:
                    error = data.get('error', 'Unknown')
                    print(f"   ❌ 統合検索エラー: {error}")
                    api_test_results['統合検索'] = f'api_error: {error}'
            else:
                print(f"   ❌ 統合検索HTTPエラー: {response.status_code}")
                api_test_results['統合検索'] = f'http_error: {response.status_code}'
                
        except Exception as e:
            print(f"   ❌ 統合検索テストエラー: {str(e)}")
            api_test_results['統合検索'] = f'error: {str(e)}'
    else:
        print(f"   ❌ 統合検索スキップ: エンドポイント未デプロイ")
        api_test_results['統合検索'] = 'endpoint_missing'
    
    # 4. 最終結果
    print(f"\n📊 最終結果サマリー")
    print("=" * 70)
    
    # エンドポイント結果
    endpoint_success = sum(1 for status in endpoint_results.values() if status in ["400", "500"])
    print(f"📍 エンドポイント成功: {endpoint_success}/{len(endpoints)}")
    
    for endpoint, status in endpoint_results.items():
        if status in ["400", "500"]:
            print(f"   ✅ {endpoint}: デプロイ済み")
        else:
            print(f"   ❌ {endpoint}: {status}")
    
    # API実行結果
    api_success = sum(1 for result in api_test_results.values() if result == 'success')
    print(f"\n🧪 API実行成功: {api_success}/{len(api_test_results)}")
    
    for api, result in api_test_results.items():
        if result == 'success':
            print(f"   ✅ {api}: 正常動作")
        else:
            print(f"   ❌ {api}: {result}")
    
    # 総合評価
    total_success = endpoint_success + api_success
    total_tests = len(endpoints) + len(api_test_results)
    success_rate = total_success / total_tests if total_tests > 0 else 0
    
    print(f"\n🎯 総合評価")
    print("-" * 30)
    print(f"成功率: {success_rate:.1%}")
    
    if success_rate >= 0.8:
        grade = "A (優秀)"
        status = "🎉 デプロイ成功！Yahoo以外の問題は解決"
    elif success_rate >= 0.6:
        grade = "B (良好)"
        status = "⚠️  大部分が改善。残り問題の個別対応が必要"
    elif success_rate >= 0.4:
        grade = "C (改善)"
        status = "🔧 部分的改善。追加デプロイまたは設定確認が必要"
    else:
        grade = "D (要修正)"
        status = "❌ デプロイ問題が深刻。手動介入が必要"
    
    print(f"評価: {grade}")
    print(f"状況: {status}")
    
    # 次のアクション
    print(f"\n📝 次のアクション")
    print("-" * 30)
    
    if endpoint_success == len(endpoints):
        print("   ✅ すべてのエンドポイントがデプロイ完了")
        if api_success > 0:
            print("   🎉 一部のAPIが正常動作中")
            print("   📝 残るタスク: Yahoo APIキーの更新")
        else:
            print("   🔧 エンドポイントは存在するが、API実行でエラー")
            print("   📝 環境変数とコードの確認が必要")
    else:
        missing_endpoints = [ep for ep, status in endpoint_results.items() if status == "404"]
        print(f"   ⏳ 未デプロイエンドポイント: {len(missing_endpoints)}個")
        for ep in missing_endpoints:
            print(f"     - {ep}")
        print("   📝 追加の手動デプロイまたは時間待機が必要")

if __name__ == "__main__":
    force_redeploy_test()
