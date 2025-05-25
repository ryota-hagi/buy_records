#!/usr/bin/env python3
"""
最終版統合検索エンジンテスト
"""

import requests
import json
import time
from datetime import datetime

def test_final_unified_engine():
    """最終版統合検索エンジンテスト実行"""
    
    print("🎯 最終版統合検索エンジンテスト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # デプロイ完了まで待機
    print("⏳ デプロイ完了を待機中（45秒）...")
    time.sleep(45)
    
    # 1. 個別APIエンドポイントの確認
    print(f"\n1. 個別APIエンドポイントの確認")
    print("-" * 40)
    
    apis = [
        ("Yahoo Shopping", f"{base_url}/api/search/yahoo", {"jan_code": jan_code, "limit": 3}),
        ("eBay", f"{base_url}/api/search/ebay", {"query": "マリオカート8", "limit": 3}),
        ("Mercari", f"{base_url}/api/search/mercari", {"query": "マリオカート8", "limit": 3})
    ]
    
    api_results = {}
    for name, url, params in apis:
        print(f"\n{name} API:")
        try:
            response = requests.get(url, params=params, timeout=20)
            print(f"  ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                results_count = len(data.get('results', []))
                print(f"  成功: {success}")
                print(f"  結果数: {results_count}")
                api_results[name] = {'success': success, 'count': results_count}
                
                if results_count > 0:
                    sample = data['results'][0]
                    print(f"  サンプル: {sample.get('title', 'タイトルなし')[:50]}...")
            else:
                print(f"  ❌ HTTPエラー: {response.status_code}")
                api_results[name] = {'success': False, 'count': 0}
                
        except Exception as e:
            print(f"  ❌ 例外: {str(e)}")
            api_results[name] = {'success': False, 'count': 0}
    
    # 2. 新しいタスクを作成
    print(f"\n2. 最終版統合検索エンジンでタスク作成")
    print("-" * 40)
    
    task_id = None
    try:
        url = f"{base_url}/api/search/tasks"
        payload = {'jan_code': jan_code}
        
        print(f"タスク作成実行: {jan_code}")
        response = requests.post(url, json=payload, timeout=30)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功フラグ: {data.get('success', False)}")
            
            if data.get('success') and data.get('task'):
                task = data['task']
                task_id = task.get('id')
                print(f"✅ タスクID: {task_id}")
                print(f"タスク名: {task.get('name', 'なし')}")
                print(f"ステータス: {task.get('status', 'なし')}")
            else:
                print(f"❌ タスク作成失敗")
                return
        else:
            print(f"❌ タスク作成HTTPエラー: {response.status_code}")
            return
                
    except Exception as e:
        print(f"❌ タスク作成例外: {str(e)}")
        return
    
    # 3. タスク実行の監視
    print(f"\n3. 最終版統合検索エンジンの実行監視")
    print("-" * 40)
    
    if task_id:
        print(f"タスク {task_id} の実行を監視中...")
        
        for attempt in range(15):  # 最大2分間監視
            try:
                url = f"{base_url}/api/search/tasks"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('tasks'):
                        # 作成したタスクを検索
                        target_task = None
                        for task in data['tasks']:
                            if task.get('id') == task_id:
                                target_task = task
                                break
                        
                        if target_task:
                            status = target_task.get('status', 'unknown')
                            results_count = target_task.get('results_count', 0)
                            
                            print(f"   試行 {attempt + 1}: ステータス={status}, 結果数={results_count}")
                            
                            if status == 'completed':
                                print(f"   ✅ タスク完了！")
                                
                                # 結果の詳細確認
                                result = target_task.get('result', {})
                                if result:
                                    integrated_results = result.get('integrated_results', {})
                                    platform_results = result.get('platform_results', {})
                                    
                                    print(f"   📊 統合結果: {integrated_results.get('count', 0)}件")
                                    print(f"   📊 プラットフォーム別:")
                                    print(f"      - Yahoo: {len(platform_results.get('yahoo_shopping', []))}件")
                                    print(f"      - eBay: {len(platform_results.get('ebay', []))}件")
                                    print(f"      - Mercari: {len(platform_results.get('mercari', []))}件")
                                
                                # search_resultsテーブルの結果確認
                                search_results = target_task.get('results', [])
                                print(f"   💾 データベース保存結果: {len(search_results)}件")
                                
                                if len(search_results) > 0:
                                    sample = search_results[0]
                                    print(f"   💾 サンプル結果:")
                                    print(f"      - タイトル: {sample.get('title', 'なし')[:50]}...")
                                    print(f"      - 価格: {sample.get('total_price', 'なし')}")
                                    print(f"      - プラットフォーム: {sample.get('platform', 'なし')}")
                                    
                                    # 最終評価
                                    integrated_count = integrated_results.get('count', 0)
                                    if integrated_count > 0 and results_count > 0:
                                        success_rate = (results_count / integrated_count) * 100
                                        
                                        print(f"\n🎉 最終版統合検索エンジン成功！")
                                        print(f"   統合検索: {integrated_count}件")
                                        print(f"   データベース保存: {results_count}件")
                                        print(f"   保存成功率: {success_rate:.1f}%")
                                        
                                        # 個別APIとの比較
                                        print(f"\n📊 個別API vs 統合検索比較:")
                                        for api_name, api_result in api_results.items():
                                            if api_result['success']:
                                                print(f"   {api_name}: 個別={api_result['count']}件")
                                        
                                        if success_rate >= 90:
                                            print(f"\n🏆 評価: A+ (完璧！)")
                                        elif success_rate >= 80:
                                            print(f"\n🥇 評価: A (優秀)")
                                        elif success_rate >= 70:
                                            print(f"\n🥈 評価: B (良好)")
                                        else:
                                            print(f"\n🥉 評価: C (改善が必要)")
                                        
                                        print(f"\n✅ 統合検索エンジン修正完了！")
                                        print(f"   1つのワークフローで管理しやすくなりました")
                                        return
                                    else:
                                        print(f"\n❌ まだ問題があります")
                                        print(f"   統合検索: {integrated_count}件")
                                        print(f"   データベース保存: {results_count}件")
                                else:
                                    print(f"   ❌ データベースに結果が保存されていません")
                                
                                break
                            elif status == 'failed':
                                print(f"   ❌ タスク失敗")
                                error = target_task.get('error', 'Unknown error')
                                print(f"   エラー: {error}")
                                break
                        else:
                            print(f"   試行 {attempt + 1}: タスクが見つかりません")
                    else:
                        print(f"   試行 {attempt + 1}: タスク一覧取得失敗")
                else:
                    print(f"   試行 {attempt + 1}: HTTP {response.status_code}")
                
                if attempt < 14:  # 最後の試行でない場合
                    time.sleep(8)  # 8秒待機
                    
            except Exception as e:
                print(f"   試行 {attempt + 1}: 例外 {str(e)}")
                if attempt < 14:
                    time.sleep(8)
    
    print(f"\n❌ テスト完了 - 期待した結果が得られませんでした")

if __name__ == "__main__":
    test_final_unified_engine()
