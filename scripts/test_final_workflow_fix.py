#!/usr/bin/env python3
"""
最終ワークフロー修正テスト - フォールバック機能付きAPIエンドポイント使用
"""

import requests
import json
import time
from datetime import datetime

def test_final_workflow_fix():
    """最終ワークフロー修正テスト実行"""
    
    print("🎯 最終ワークフロー修正テスト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # デプロイ完了まで待機
    print("⏳ Vercel自動デプロイ完了を待機中（90秒）...")
    time.sleep(90)
    
    # 1. 修正済みAPIエンドポイントの直接テスト
    print("\n1. 修正済みAPIエンドポイントの直接テスト")
    print("-" * 50)
    
    platforms = [
        {"name": "Yahoo!ショッピング", "endpoint": "/api/search/yahoo"},
        {"name": "eBay", "endpoint": "/api/search/ebay"},
        {"name": "Mercari", "endpoint": "/api/search/mercari"}
    ]
    
    platform_results = {}
    
    for platform in platforms:
        print(f"\n🔍 {platform['name']} 直接APIテスト")
        print("-" * 30)
        
        try:
            url = f"{base_url}{platform['endpoint']}"
            params = {'jan_code': jan_code, 'limit': 3} if platform['name'] == 'Yahoo!ショッピング' else {'query': 'Nintendo Switch Mario Kart', 'limit': 3}
            
            response = requests.get(url, params=params, timeout=30)
            print(f"   ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   成功フラグ: {data.get('success', False)}")
                print(f"   結果数: {len(data.get('results', []))}")
                
                if data.get('success') and data.get('results'):
                    results = data['results']
                    sample = results[0]
                    print(f"   サンプルタイトル: {sample.get('title', 'なし')[:50]}...")
                    print(f"   サンプル価格: {sample.get('price', 'なし')}")
                    
                    # フォールバック使用の確認
                    if data.get('note'):
                        print(f"   📝 注記: {data.get('note')}")
                    
                    platform_results[platform['name']] = 'success_with_results'
                elif data.get('success'):
                    print(f"   成功だが結果0件")
                    platform_results[platform['name']] = 'success_no_results'
                else:
                    error = data.get('error', 'Unknown error')
                    print(f"   APIエラー: {error}")
                    platform_results[platform['name']] = f'api_error: {error}'
            
            else:
                print(f"   HTTPエラー: {response.status_code}")
                platform_results[platform['name']] = f'http_error: {response.status_code}'
                
        except Exception as e:
            print(f"   例外エラー: {str(e)}")
            platform_results[platform['name']] = f'exception: {str(e)}'
    
    # 2. ワークフローシステムのテスト（タスク作成）
    print(f"\n2. ワークフローシステムのテスト（タスク作成）")
    print("-" * 50)
    
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
                print(f"タスクID: {task_id}")
                print(f"タスク名: {task.get('name', 'なし')}")
                print(f"ステータス: {task.get('status', 'なし')}")
                
                task_creation_success = True
            else:
                print(f"タスク作成失敗")
                task_creation_success = False
        else:
            print(f"タスク作成HTTPエラー: {response.status_code}")
            task_creation_success = False
                
    except Exception as e:
        print(f"タスク作成例外: {str(e)}")
        task_creation_success = False
    
    # 3. タスク実行の監視
    print(f"\n3. タスク実行の監視")
    print("-" * 50)
    
    task_completion_success = False
    final_results_count = 0
    
    if task_id:
        print(f"タスク {task_id} の実行を監視中...")
        
        for attempt in range(12):  # 最大2分間監視
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
                                task_completion_success = True
                                final_results_count = results_count
                                break
                            elif status == 'failed':
                                print(f"   ❌ タスク失敗")
                                break
                        else:
                            print(f"   試行 {attempt + 1}: タスクが見つかりません")
                    else:
                        print(f"   試行 {attempt + 1}: タスク一覧取得失敗")
                else:
                    print(f"   試行 {attempt + 1}: HTTP {response.status_code}")
                
                if attempt < 11:  # 最後の試行でない場合
                    time.sleep(10)  # 10秒待機
                    
            except Exception as e:
                print(f"   試行 {attempt + 1}: 例外 {str(e)}")
                if attempt < 11:
                    time.sleep(10)
    else:
        print("タスクIDが取得できないため、監視をスキップ")
    
    # 4. 結果分析と評価
    print(f"\n4. 結果分析と評価")
    print("-" * 50)
    
    # 直接APIの結果分析
    success_with_results = sum(1 for result in platform_results.values() if result == 'success_with_results')
    success_no_results = sum(1 for result in platform_results.values() if result == 'success_no_results')
    error_count = len(platform_results) - success_with_results - success_no_results
    
    print(f"直接API結果:")
    print(f"  成功（結果あり）: {success_with_results}件")
    print(f"  成功（結果なし）: {success_no_results}件")
    print(f"  エラー: {error_count}件")
    
    for platform, result in platform_results.items():
        if result == 'success_with_results':
            print(f"  ✅ {platform}: 正常動作")
        elif result == 'success_no_results':
            print(f"  ⚠️  {platform}: 動作するが結果なし")
        else:
            print(f"  ❌ {platform}: {result}")
    
    # ワークフローの結果分析
    print(f"\nワークフロー結果:")
    if task_creation_success:
        print(f"  ✅ タスク作成: 成功")
    else:
        print(f"  ❌ タスク作成: 失敗")
    
    if task_completion_success:
        print(f"  ✅ タスク実行: 成功（{final_results_count}件の結果）")
    else:
        print(f"  ❌ タスク実行: 失敗または未完了")
    
    # 5. 総合評価
    print(f"\n5. 総合評価")
    print("-" * 50)
    
    total_working = success_with_results + success_no_results
    total_platforms = len(platform_results)
    api_working_rate = total_working / total_platforms if total_platforms > 0 else 0
    
    # 評価基準
    if api_working_rate >= 1.0 and task_completion_success and final_results_count > 0:
        grade = "A+ (完璧)"
        status = "🎉 全システム正常動作！ワークフロー問題完全解決！"
    elif api_working_rate >= 0.67 and task_completion_success:
        grade = "A (優秀)"
        status = "🎉 ワークフロー問題解決、大部分のAPIが動作中"
    elif api_working_rate >= 0.67 and task_creation_success:
        grade = "B+ (改善)"
        status = "⚠️  API修正成功、ワークフロー実行に課題"
    elif api_working_rate >= 0.33:
        grade = "B (部分改善)"
        status = "⚠️  一部API修正成功、更なる改善が必要"
    else:
        grade = "C (要修正)"
        status = "❌ 根本的な問題が残存"
    
    print(f"直接API動作率: {api_working_rate:.1%} ({total_working}/{total_platforms})")
    print(f"ワークフロー動作: {'✅' if task_completion_success else '❌'}")
    print(f"最終結果数: {final_results_count}件")
    print(f"総合評価: {grade}")
    print(f"状況: {status}")
    
    # 6. 修正効果の確認
    print(f"\n6. 修正効果の確認")
    print("-" * 50)
    
    print(f"修正前の問題:")
    print(f"  - ワークフロー: 全プラットフォーム0件（1秒で完了）")
    print(f"  - 直接API: eBay・Mercariで500エラー")
    print(f"  - 統合検索: Yahoo!のみ動作")
    
    print(f"\n修正後の状況:")
    if success_with_results >= 2:
        print(f"  ✅ 複数プラットフォームで結果取得成功")
    if task_completion_success and final_results_count > 0:
        print(f"  ✅ ワークフローで実際の結果取得成功")
    if api_working_rate >= 0.67:
        print(f"  ✅ フォールバック機能により高い可用性実現")
    
    # 7. 次のアクション
    print(f"\n7. 次のアクション")
    print("-" * 50)
    
    if grade.startswith("A"):
        print(f"✅ ワークフロー問題は解決されました！")
        if final_results_count > 0:
            print(f"🎉 実際の商品検索結果が取得できています")
        print(f"📝 システムは本格運用可能な状態です")
    else:
        print(f"🔧 追加の修正が必要です")
        if not task_completion_success:
            print(f"📝 ワークフローシステムの更なる調査が必要")
        if api_working_rate < 0.67:
            print(f"📝 APIエンドポイントの更なる修正が必要")
    
    return {
        'api_working_rate': api_working_rate,
        'grade': grade,
        'platform_results': platform_results,
        'task_completion_success': task_completion_success,
        'final_results_count': final_results_count,
        'success_with_results': success_with_results
    }

if __name__ == "__main__":
    test_final_workflow_fix()
