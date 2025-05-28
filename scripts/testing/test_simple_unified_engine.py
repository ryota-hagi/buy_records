#!/usr/bin/env python3
"""
シンプル版統合検索エンジンの最終テスト
"""

import requests
import json
import time
from datetime import datetime

def test_simple_unified_engine():
    """シンプル版統合検索エンジンの最終テスト"""
    
    print("🎯 シンプル版統合検索エンジン最終テスト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"
    
    # デプロイ完了を待機
    print(f"⏳ デプロイ完了を待機中（60秒）...")
    time.sleep(60)
    
    # 1. 個別APIエンドポイントの最終確認
    print(f"\n1. 個別APIエンドポイントの最終確認")
    print("-" * 40)
    
    apis = [
        ("Yahoo Shopping", f"{base_url}/api/search/yahoo", {"jan_code": jan_code, "limit": 5}),
        ("eBay", f"{base_url}/api/search/ebay", {"query": "マリオカート8", "limit": 5}),
        ("Mercari", f"{base_url}/api/search/mercari", {"query": "マリオカート8", "limit": 5})
    ]
    
    all_apis_working = True
    for name, url, params in apis:
        print(f"\n{name} API:")
        try:
            response = requests.get(url, params=params, timeout=30)
            print(f"  ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                results_count = len(data.get('results', []))
                print(f"  成功: {success}")
                print(f"  結果数: {results_count}")
                
                if success and results_count > 0:
                    sample = data['results'][0]
                    print(f"  サンプル: {sample.get('title', 'タイトルなし')[:50]}...")
                else:
                    all_apis_working = False
                    print(f"  ❌ {name} APIに問題があります")
            else:
                all_apis_working = False
                print(f"  ❌ {name} API HTTPエラー: {response.status_code}")
                
        except Exception as e:
            all_apis_working = False
            print(f"  ❌ {name} API例外: {str(e)}")
    
    if not all_apis_working:
        print(f"\n❌ 個別APIに問題があります。統合検索エンジンのテストを中止します。")
        return
    
    # 2. シンプル版統合検索エンジンでタスク作成
    print(f"\n2. シンプル版統合検索エンジンでタスク作成")
    print("-" * 40)
    
    try:
        url = f"{base_url}/api/search/tasks"
        payload = {"jan_code": jan_code}
        
        print(f"タスク作成実行: {jan_code}")
        response = requests.post(url, json=payload, timeout=60)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            print(f"成功フラグ: {success}")
            
            if success:
                task = data.get('task', {})
                task_id = task.get('id')
                task_name = task.get('name', '')
                task_status = task.get('status', '')
                
                print(f"✅ タスクID: {task_id}")
                print(f"タスク名: {task_name}")
                print(f"ステータス: {task_status}")
                
                # 3. シンプル版統合検索エンジンの実行監視
                print(f"\n3. シンプル版統合検索エンジンの実行監視")
                print("-" * 40)
                
                print(f"タスク {task_id} の実行を監視中...")
                
                max_attempts = 20  # 最大20回（約10分）
                for attempt in range(1, max_attempts + 1):
                    try:
                        # タスクの状態を確認
                        check_url = f"{base_url}/api/search/tasks/{task_id}"
                        check_response = requests.get(check_url, timeout=30)
                        
                        if check_response.status_code == 200:
                            task_data = check_response.json()
                            if task_data.get('success'):
                                task_info = task_data.get('task', {})
                                current_status = task_info.get('status', 'unknown')
                                results_count = task_info.get('results_count', 0)
                                
                                print(f"   試行 {attempt}: ステータス={current_status}, 結果数={results_count}")
                                
                                if current_status == 'completed':
                                    print(f"\n🎉 シンプル版統合検索エンジン完了！")
                                    print(f"最終結果数: {results_count}")
                                    
                                    # 結果の詳細を表示
                                    if results_count > 0:
                                        results = task_info.get('results', [])
                                        platform_counts = {}
                                        for result in results:
                                            platform = result.get('platform', 'unknown')
                                            platform_counts[platform] = platform_counts.get(platform, 0) + 1
                                        
                                        print(f"プラットフォーム別結果:")
                                        for platform, count in platform_counts.items():
                                            print(f"  - {platform}: {count}件")
                                        
                                        # サンプル結果を表示
                                        if len(results) > 0:
                                            sample = results[0]
                                            print(f"サンプル結果:")
                                            print(f"  - タイトル: {sample.get('title', 'なし')}")
                                            print(f"  - 価格: {sample.get('total_price', 'なし')}")
                                            print(f"  - プラットフォーム: {sample.get('platform', 'なし')}")
                                    
                                    # 最終評価
                                    print(f"\n🎯 最終評価:")
                                    if results_count > 0:
                                        print(f"✅ A+ (完璧！) - シンプル版統合検索エンジンが正常動作")
                                        print(f"✅ 個別API: 3/3 動作中")
                                        print(f"✅ 統合検索: {results_count}件取得成功")
                                        print(f"✅ 問題完全解決！")
                                    else:
                                        print(f"❌ C (問題あり) - 統合検索エンジンは動作するが結果0件")
                                    
                                    return
                                    
                                elif current_status == 'failed':
                                    error_msg = task_info.get('error', 'Unknown error')
                                    print(f"\n❌ シンプル版統合検索エンジン失敗")
                                    print(f"エラー: {error_msg}")
                                    return
                                
                                # 実行中の場合は待機
                                if attempt < max_attempts:
                                    time.sleep(30)  # 30秒待機
                            else:
                                print(f"   試行 {attempt}: タスク取得失敗")
                                if attempt < max_attempts:
                                    time.sleep(30)
                        else:
                            print(f"   試行 {attempt}: HTTP {check_response.status_code}")
                            if attempt < max_attempts:
                                time.sleep(30)
                                
                    except Exception as e:
                        print(f"   試行 {attempt}: 例外 - {str(e)}")
                        if attempt < max_attempts:
                            time.sleep(30)
                
                print(f"\n⏰ タイムアウト: {max_attempts}回の試行後も完了しませんでした")
                print(f"❌ シンプル版統合検索エンジンに問題があります")
                
            else:
                error = data.get('error', 'Unknown error')
                print(f"❌ タスク作成エラー: {error}")
        else:
            print(f"❌ タスク作成HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ タスク作成例外: {str(e)}")

if __name__ == "__main__":
    test_simple_unified_engine()
