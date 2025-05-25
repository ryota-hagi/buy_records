#!/usr/bin/env python3
"""
デバッグログ付きワークフローテスト
"""

import requests
import json
import time
from datetime import datetime

def test_debug_workflow():
    """デバッグログ付きワークフローテスト実行"""
    
    print("🔍 デバッグログ付きワークフローテスト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # デプロイ完了まで少し待機
    print("⏳ デプロイ完了を待機中（30秒）...")
    time.sleep(30)
    
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
    
    # 2. タスク実行の監視（詳細ログ確認）
    print(f"\n2. タスク実行の監視（詳細ログ確認）")
    print("-" * 40)
    
    if task_id:
        print(f"タスク {task_id} の実行を監視中...")
        
        for attempt in range(15):  # 最大2.5分間監視
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
                            
                            # 処理ログの確認
                            processing_logs = target_task.get('processing_logs', [])
                            if processing_logs:
                                latest_log = processing_logs[-1] if isinstance(processing_logs, list) else processing_logs
                                if isinstance(latest_log, dict):
                                    print(f"   最新ログ: {latest_log.get('message', 'なし')}")
                            
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
                                    print(f"   📊 サマリー: {summary}")
                                
                                # search_resultsテーブルの結果確認
                                search_results = target_task.get('results', [])
                                print(f"   💾 データベース保存結果: {len(search_results)}件")
                                
                                if len(search_results) > 0:
                                    sample = search_results[0]
                                    print(f"   💾 サンプル結果:")
                                    print(f"      - タイトル: {sample.get('item_title', 'なし')[:50]}...")
                                    print(f"      - 価格: {sample.get('total_price', 'なし')}")
                                    print(f"      - プラットフォーム: {sample.get('platform', 'なし')}")
                                
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
                    time.sleep(10)  # 10秒待機
                    
            except Exception as e:
                print(f"   試行 {attempt + 1}: 例外 {str(e)}")
                if attempt < 14:
                    time.sleep(10)
    
    # 3. 問題分析
    print(f"\n3. 問題分析")
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
                            
                            if integrated_count > 0 and results_count == 0:
                                print(f"🔍 問題発見: 統合検索では{integrated_count}件取得したが、データベースに0件保存")
                                print(f"   → データベース保存処理に問題がある可能性")
                                print(f"   → Vercelのログを確認して[SAVE_RESULTS]タグのログを探してください")
                            elif integrated_count == 0:
                                print(f"🔍 問題発見: 統合検索自体が0件")
                                print(f"   → APIエンドポイントの問題の可能性")
                            elif results_count > 0:
                                print(f"✅ 正常: 統合検索{integrated_count}件、データベース{results_count}件保存")
                        else:
                            print(f"🔍 問題発見: resultフィールドが空")
                            print(f"   → タスク実行自体に問題がある可能性")
        
        except Exception as e:
            print(f"最終確認エラー: {str(e)}")
    
    print(f"\n4. 次のアクション")
    print("-" * 40)
    print(f"1. Vercelのログを確認:")
    print(f"   https://vercel.com/dashboard → buy-records → Functions → Logs")
    print(f"2. [SAVE_RESULTS]タグのログを探す")
    print(f"3. データベース保存エラーの詳細を確認")
    print(f"4. 必要に応じてデータベーススキーマを確認")

if __name__ == "__main__":
    test_debug_workflow()
