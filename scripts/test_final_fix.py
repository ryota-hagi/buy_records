#!/usr/bin/env python3
"""
最終修正テスト - データベースフィールドマッピング修正後の確認
"""

import requests
import json
import time
from datetime import datetime

def test_final_fix():
    """最終修正テスト実行"""
    
    print("🎯 最終修正テスト - データベースフィールドマッピング修正後")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # デプロイ完了まで待機
    print("⏳ デプロイ完了を待機中（45秒）...")
    time.sleep(45)
    
    # 1. 新しいテストタスクを作成
    print(f"\n1. 新しいテストタスクを作成")
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
    
    # 2. タスク実行の監視
    print(f"\n2. タスク実行の監視")
    print("-" * 40)
    
    if task_id:
        print(f"タスク {task_id} の実行を監視中...")
        
        for attempt in range(20):  # 最大3分間監視
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
                                    summary = result.get('summary', {})
                                    
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
                                    print(f"      - URL: {sample.get('url', 'なし')[:50]}...")
                                    
                                    # 修正確認
                                    integrated_count = integrated_results.get('count', 0)
                                    if integrated_count > 0 and results_count > 0:
                                        print(f"\n🎉 修正成功！")
                                        print(f"   統合検索: {integrated_count}件")
                                        print(f"   データベース保存: {results_count}件")
                                        print(f"   フィールドマッピング修正が正常に動作しています")
                                        
                                        # 成功率計算
                                        success_rate = (results_count / integrated_count) * 100
                                        print(f"   保存成功率: {success_rate:.1f}%")
                                        
                                        if success_rate >= 90:
                                            print(f"   ✅ 優秀な保存成功率です")
                                        elif success_rate >= 70:
                                            print(f"   ⚠️ 保存成功率が少し低いです")
                                        else:
                                            print(f"   ❌ 保存成功率が低すぎます")
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
                
                if attempt < 19:  # 最後の試行でない場合
                    time.sleep(9)  # 9秒待機
                    
            except Exception as e:
                print(f"   試行 {attempt + 1}: 例外 {str(e)}")
                if attempt < 19:
                    time.sleep(9)
    
    # 3. 最終評価
    print(f"\n3. 最終評価")
    print("-" * 40)
    
    if task_id:
        try:
            # 最終状態を再確認
            url = f"{base_url}/api/search/tasks"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('tasks'):
                    target_task = None
                    for task in data['tasks']:
                        if task.get('id') == task_id:
                            target_task = task
                            break
                    
                    if target_task:
                        status = target_task.get('status', 'unknown')
                        results_count = target_task.get('results_count', 0)
                        result = target_task.get('result', {})
                        
                        print(f"最終ステータス: {status}")
                        print(f"データベース結果数: {results_count}")
                        
                        if result:
                            integrated_count = result.get('integrated_results', {}).get('count', 0)
                            print(f"統合検索結果数: {integrated_count}")
                            
                            if integrated_count > 0 and results_count > 0:
                                success_rate = (results_count / integrated_count) * 100
                                print(f"\n🎯 総合評価:")
                                print(f"   ワークフロー: ✅ 正常動作")
                                print(f"   統合検索: ✅ {integrated_count}件取得")
                                print(f"   データベース保存: ✅ {results_count}件保存")
                                print(f"   保存成功率: {success_rate:.1f}%")
                                
                                if success_rate >= 90:
                                    print(f"   🏆 評価: A+ (完璧！)")
                                elif success_rate >= 80:
                                    print(f"   🥇 評価: A (優秀)")
                                elif success_rate >= 70:
                                    print(f"   🥈 評価: B (良好)")
                                else:
                                    print(f"   🥉 評価: C (改善が必要)")
                                
                                print(f"\n✅ 問題修正完了！")
                                print(f"   検索結果がUIに正しく表示されるはずです")
                            else:
                                print(f"\n❌ まだ問題が残っています")
                                print(f"   統合検索: {integrated_count}件")
                                print(f"   データベース保存: {results_count}件")
        
        except Exception as e:
            print(f"最終確認エラー: {str(e)}")

if __name__ == "__main__":
    test_final_fix()
