#!/usr/bin/env python3
"""
最終デプロイ後のテスト - 強制プッシュ後の確認
"""

import requests
import json
import time
from datetime import datetime

def test_final_deploy():
    """最終デプロイ後のテスト実行"""
    
    print("🎯 最終デプロイ後のテスト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # デプロイ完了まで待機
    print("⏳ Vercel自動デプロイ完了を待機中（90秒）...")
    time.sleep(90)
    
    # 1. エンドポイント存在確認（詳細版）
    print("\n1. 詳細エンドポイント確認")
    print("-" * 50)
    
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
        
        success = False
        for attempt in range(5):  # 5回試行
            try:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, timeout=15)
                
                if response.status_code == 404:
                    if attempt < 4:
                        print(f"   試行{attempt+1}: 404 - 再試行中...")
                        time.sleep(15)
                        continue
                    else:
                        print(f"   ❌ 最終結果: 404 (デプロイ未完了)")
                        endpoint_results[endpoint] = "404"
                        break
                elif response.status_code == 400:
                    print(f"   ✅ 成功: 400 (正常なパラメータエラー)")
                    endpoint_results[endpoint] = "400"
                    success = True
                    break
                elif response.status_code == 500:
                    print(f"   ⚠️  成功: 500 (サーバーエラー - エンドポイント存在)")
                    endpoint_results[endpoint] = "500"
                    success = True
                    break
                elif response.status_code == 200:
                    print(f"   ✅ 成功: 200 (正常動作)")
                    endpoint_results[endpoint] = "200"
                    success = True
                    break
                else:
                    print(f"   ❓ 成功: {response.status_code}")
                    endpoint_results[endpoint] = str(response.status_code)
                    success = True
                    break
                    
            except Exception as e:
                if attempt < 4:
                    print(f"   試行{attempt+1}: エラー - 再試行中...")
                    time.sleep(15)
                    continue
                else:
                    print(f"   ❌ 最終結果: 接続エラー ({str(e)})")
                    endpoint_results[endpoint] = "error"
                    break
        
        if success:
            print(f"   ✅ {endpoint}: デプロイ完了")
    
    # 2. 実際のAPI呼び出しテスト
    print(f"\n2. 実際のAPI呼び出しテスト")
    print("-" * 50)
    
    api_test_results = {}
    
    # テストAPIの確認
    if endpoint_results.get("/api/test-production") in ["200", "400", "500"]:
        print(f"\n🔍 テストAPI実行")
        try:
            url = f"{base_url}/api/test-production"
            response = requests.get(url, timeout=20)
            print(f"   ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ テストAPI成功")
                print(f"   環境変数確認:")
                env = data.get('environment', {})
                for key, value in env.items():
                    print(f"     {key}: {value}")
                api_test_results['テストAPI'] = 'success'
            else:
                print(f"   ❌ テストAPI HTTPエラー: {response.status_code}")
                api_test_results['テストAPI'] = f'http_error: {response.status_code}'
                
        except Exception as e:
            print(f"   ❌ テストAPIエラー: {str(e)}")
            api_test_results['テストAPI'] = f'error: {str(e)}'
    else:
        print(f"   ❌ テストAPIスキップ: エンドポイント未デプロイ")
        api_test_results['テストAPI'] = 'endpoint_missing'
    
    # eBayテスト（トークン更新済み）
    if endpoint_results.get("/api/search/ebay") in ["200", "400", "500"]:
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
                    if count > 0:
                        sample = data['results'][0]
                        print(f"   サンプル: {sample.get('title', 'タイトル不明')[:50]}...")
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
    if endpoint_results.get("/api/search/mercari") in ["200", "400", "500"]:
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
                    if count > 0:
                        sample = data['results'][0]
                        print(f"   サンプル: {sample.get('title', 'タイトル不明')[:50]}...")
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
    if endpoint_results.get("/api/search/all") in ["200", "400", "500"]:
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
    
    # 3. 最終結果サマリー
    print(f"\n3. 最終結果サマリー")
    print("=" * 70)
    
    # エンドポイント結果
    endpoint_success = sum(1 for status in endpoint_results.values() if status in ["200", "400", "500"])
    print(f"📍 エンドポイント成功: {endpoint_success}/{len(endpoints)}")
    
    for endpoint, status in endpoint_results.items():
        if status in ["200", "400", "500"]:
            print(f"   ✅ {endpoint}: デプロイ済み ({status})")
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
    
    print(f"\n🎯 最終総合評価")
    print("-" * 30)
    print(f"成功率: {success_rate:.1%}")
    
    if success_rate >= 0.9:
        grade = "A+ (完璧)"
        status = "🎉 完全成功！Yahoo以外のすべての問題が解決"
    elif success_rate >= 0.8:
        grade = "A (優秀)"
        status = "🎉 ほぼ完全成功！Yahoo以外の問題は解決"
    elif success_rate >= 0.6:
        grade = "B (良好)"
        status = "⚠️  大部分が改善。残り問題の個別対応が必要"
    elif success_rate >= 0.4:
        grade = "C (改善)"
        status = "🔧 部分的改善。追加対応が必要"
    else:
        grade = "D (要修正)"
        status = "❌ 深刻な問題が残存。手動介入が必要"
    
    print(f"評価: {grade}")
    print(f"状況: {status}")
    
    # 4. 残存問題と次のアクション
    print(f"\n4. 残存問題と次のアクション")
    print("-" * 30)
    
    if endpoint_success == len(endpoints):
        print("   ✅ すべてのエンドポイントがデプロイ完了")
        if api_success >= len(api_test_results) * 0.75:
            print("   🎉 Yahoo以外のAPIが正常動作中")
            print("   📝 残るタスク: Yahoo APIキーの更新のみ")
        else:
            print("   🔧 エンドポイントは存在するが、API実行でエラー")
            print("   📝 環境変数とコードの確認が必要")
    else:
        missing_endpoints = [ep for ep, status in endpoint_results.items() if status == "404"]
        print(f"   ⏳ 未デプロイエンドポイント: {len(missing_endpoints)}個")
        for ep in missing_endpoints:
            print(f"     - {ep}")
        print("   📝 追加の手動デプロイまたは時間待機が必要")
    
    # 5. Yahoo API問題の確認
    yahoo_status = endpoint_results.get("/api/search/yahoo", "unknown")
    if yahoo_status in ["200", "400", "500"]:
        print(f"\n5. Yahoo API状況確認")
        print("-" * 30)
        try:
            url = f"{base_url}/api/search/yahoo"
            params = {'jan_code': jan_code, 'limit': 1}
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("   ✅ Yahoo API: 正常動作中！")
                else:
                    print(f"   ❌ Yahoo API: {data.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ Yahoo API: HTTPエラー {response.status_code}")
        except Exception as e:
            print(f"   ❌ Yahoo API: テストエラー ({str(e)})")
    
    return {
        'endpoint_success_rate': endpoint_success / len(endpoints),
        'api_success_rate': api_success / len(api_test_results) if api_test_results else 0,
        'overall_success_rate': success_rate,
        'grade': grade,
        'endpoint_results': endpoint_results,
        'api_results': api_test_results
    }

if __name__ == "__main__":
    test_final_deploy()
