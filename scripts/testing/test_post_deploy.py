#!/usr/bin/env python3
"""
デプロイ後のテスト - Yahoo以外の問題解決確認
"""

import requests
import json
import time
from datetime import datetime

def test_post_deploy():
    """デプロイ後のテスト実行"""
    
    print("🚀 デプロイ後テスト開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # デプロイ完了まで少し待機
    print("⏳ デプロイ完了を待機中...")
    time.sleep(10)
    
    # 1. エンドポイント存在確認
    print("\n1. エンドポイント存在確認")
    print("-" * 50)
    
    endpoints = [
        "/api/search/yahoo",
        "/api/search/ebay", 
        "/api/search/mercari",
        "/api/search/all",
        "/api/test-production"
    ]
    
    endpoint_status = {}
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 404:
                print(f"❌ {endpoint}: 404 (まだデプロイされていない)")
                endpoint_status[endpoint] = "404"
            elif response.status_code == 400:
                print(f"✅ {endpoint}: 400 (正常 - パラメータエラー)")
                endpoint_status[endpoint] = "400"
            elif response.status_code == 500:
                print(f"⚠️  {endpoint}: 500 (サーバーエラー)")
                endpoint_status[endpoint] = "500"
            else:
                print(f"❓ {endpoint}: {response.status_code}")
                endpoint_status[endpoint] = str(response.status_code)
                
        except Exception as e:
            print(f"💥 {endpoint}: 接続エラー ({str(e)})")
            endpoint_status[endpoint] = "error"
    
    # 2. 404エラーが残っている場合は追加待機
    has_404 = any(status == "404" for status in endpoint_status.values())
    
    if has_404:
        print("\n⏳ 404エラーが残存 - 追加待機中...")
        time.sleep(20)
        
        print("\n2. 再確認テスト")
        print("-" * 50)
        
        for endpoint in endpoints:
            if endpoint_status.get(endpoint) == "404":
                try:
                    url = f"{base_url}{endpoint}"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 404:
                        print(f"❌ {endpoint}: まだ404")
                    elif response.status_code == 400:
                        print(f"✅ {endpoint}: 400に改善")
                        endpoint_status[endpoint] = "400"
                    else:
                        print(f"❓ {endpoint}: {response.status_code}")
                        endpoint_status[endpoint] = str(response.status_code)
                        
                except Exception as e:
                    print(f"💥 {endpoint}: エラー ({str(e)})")
    
    # 3. 実際のAPI呼び出しテスト（Yahoo以外）
    print("\n3. 実際のAPI呼び出しテスト（Yahoo以外）")
    print("-" * 50)
    
    test_apis = [
        {
            "name": "eBay",
            "endpoint": "/api/search/ebay",
            "expected": "eBayトークン更新により改善期待"
        },
        {
            "name": "Mercari",
            "endpoint": "/api/search/mercari",
            "expected": "デプロイ後に404解決期待"
        },
        {
            "name": "統合検索",
            "endpoint": "/api/search/all",
            "expected": "デプロイ後に404解決期待"
        }
    ]
    
    api_results = {}
    
    for api in test_apis:
        print(f"\n🔍 {api['name']} APIテスト")
        
        if endpoint_status.get(api['endpoint']) == "404":
            print(f"   ❌ スキップ: エンドポイントが404")
            api_results[api['name']] = "404_skip"
            continue
        
        try:
            url = f"{base_url}{api['endpoint']}"
            params = {'jan_code': jan_code, 'limit': 3}
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=30)
            response_time = time.time() - start_time
            
            print(f"   ステータス: {response.status_code}")
            print(f"   レスポンス時間: {response_time:.2f}秒")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if data.get('success'):
                        if api['name'] == "統合検索":
                            total_results = data.get('total_results', 0)
                            platforms = data.get('platforms', {})
                            print(f"   ✅ 成功: {total_results}件")
                            
                            for platform, items in platforms.items():
                                count = len(items) if isinstance(items, list) else 0
                                print(f"     {platform}: {count}件")
                            
                            api_results[api['name']] = {
                                'status': 'success',
                                'total_count': total_results,
                                'platforms': platforms
                            }
                        else:
                            result_count = len(data.get('results', []))
                            print(f"   ✅ 成功: {result_count}件取得")
                            
                            if result_count > 0:
                                sample = data['results'][0]
                                print(f"   サンプル: {sample.get('title', 'タイトル不明')[:50]}...")
                            
                            api_results[api['name']] = {
                                'status': 'success',
                                'count': result_count
                            }
                    else:
                        error_msg = data.get('error', 'Unknown error')
                        print(f"   ❌ API失敗: {error_msg}")
                        api_results[api['name']] = {
                            'status': 'api_error',
                            'error': error_msg
                        }
                        
                except json.JSONDecodeError:
                    print(f"   ❌ JSON解析失敗")
                    api_results[api['name']] = {'status': 'json_error'}
                    
            else:
                print(f"   ❌ HTTPエラー: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   エラー詳細: {error_data.get('error', 'Unknown')}")
                except:
                    pass
                
                api_results[api['name']] = {
                    'status': 'http_error',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ タイムアウト")
            api_results[api['name']] = {'status': 'timeout'}
            
        except Exception as e:
            print(f"   💥 エラー: {str(e)}")
            api_results[api['name']] = {'status': 'error', 'message': str(e)}
    
    # 4. テスト結果サマリー
    print("\n4. テスト結果サマリー")
    print("=" * 70)
    
    # エンドポイント存在確認結果
    print("📍 エンドポイント存在確認:")
    endpoint_success = 0
    for endpoint, status in endpoint_status.items():
        if status in ["400", "500"]:  # 存在している
            print(f"   ✅ {endpoint}: 存在")
            endpoint_success += 1
        else:
            print(f"   ❌ {endpoint}: {status}")
    
    print(f"\n   エンドポイント成功率: {endpoint_success}/{len(endpoints)}")
    
    # API動作確認結果
    print("\n🔧 API動作確認:")
    api_success = 0
    for api_name, result in api_results.items():
        if isinstance(result, dict):
            status = result.get('status', 'unknown')
            if status == 'success':
                count = result.get('count', result.get('total_count', 0))
                print(f"   ✅ {api_name}: 成功 ({count}件)")
                api_success += 1
            elif status == 'api_error':
                error = result.get('error', 'Unknown')
                print(f"   ❌ {api_name}: APIエラー ({error})")
            elif status == 'http_error':
                status_code = result.get('status_code', 'Unknown')
                print(f"   ❌ {api_name}: HTTPエラー ({status_code})")
            else:
                print(f"   ❌ {api_name}: {status}")
        else:
            print(f"   ❌ {api_name}: {result}")
    
    print(f"\n   API成功率: {api_success}/{len(test_apis)}")
    
    # 5. 総合評価
    print("\n5. 総合評価")
    print("=" * 70)
    
    total_success = endpoint_success + api_success
    total_tests = len(endpoints) + len(test_apis)
    success_rate = total_success / total_tests
    
    if success_rate >= 0.8:
        grade = "A (良好)"
        status = "🎉 デプロイ成功！Yahoo以外の問題は解決"
    elif success_rate >= 0.6:
        grade = "B (改善)"
        status = "⚠️  部分的改善。追加対応が必要"
    else:
        grade = "C (要修正)"
        status = "❌ デプロイ問題が残存。再確認が必要"
    
    print(f"成功率: {success_rate:.1%}")
    print(f"評価: {grade}")
    print(f"状況: {status}")
    
    # 6. 次のアクション
    print("\n6. 次のアクション")
    print("-" * 30)
    
    if endpoint_success == len(endpoints):
        print("   ✅ すべてのエンドポイントがデプロイ済み")
        if api_success == len(test_apis):
            print("   🎉 Yahoo以外のすべてのAPIが正常動作")
            print("   📝 残るタスク: Yahoo APIキーの更新のみ")
        else:
            print("   🔧 一部APIに問題あり。個別対応が必要")
    else:
        print("   ⏳ デプロイが未完了。追加待機または手動デプロイが必要")
    
    return {
        'endpoint_success_rate': endpoint_success / len(endpoints),
        'api_success_rate': api_success / len(test_apis) if test_apis else 0,
        'overall_grade': grade,
        'endpoint_status': endpoint_status,
        'api_results': api_results
    }

if __name__ == "__main__":
    test_post_deploy()
