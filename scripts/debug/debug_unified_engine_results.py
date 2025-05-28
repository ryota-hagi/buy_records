#!/usr/bin/env python3
"""
統合検索エンジンの結果を直接デバッグ
"""

import requests
import json
from datetime import datetime

def debug_unified_engine_results():
    """統合検索エンジンの結果を直接デバッグ"""
    
    print("🔍 統合検索エンジン結果デバッグ")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "https://buy-records.vercel.app"
    task_id = "376c1587-f6d2-489c-aed4-03ea3bbba836"
    
    try:
        # タスクの詳細情報を取得
        check_url = f"{base_url}/api/search/tasks/{task_id}"
        print(f"タスクID: {task_id}")
        print(f"確認URL: {check_url}")
        
        response = requests.get(check_url, timeout=30)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"レスポンス構造:")
            print(f"- success: {data.get('success')}")
            
            if data.get('success'):
                task_info = data.get('task', {})
                print(f"- task keys: {list(task_info.keys())}")
                print(f"- status: {task_info.get('status')}")
                print(f"- results_count: {task_info.get('results_count')}")
                print(f"- results length: {len(task_info.get('results', []))}")
                
                # resultフィールドの詳細確認
                result_field = task_info.get('result')
                if result_field:
                    print(f"\n📊 resultフィールドの詳細:")
                    print(f"- result keys: {list(result_field.keys()) if isinstance(result_field, dict) else 'Not a dict'}")
                    
                    if isinstance(result_field, dict):
                        integrated_results = result_field.get('integrated_results')
                        if integrated_results:
                            print(f"- integrated_results keys: {list(integrated_results.keys())}")
                            print(f"- integrated_results count: {integrated_results.get('count')}")
                            print(f"- integrated_results items length: {len(integrated_results.get('items', []))}")
                            
                            # サンプルアイテムを表示
                            items = integrated_results.get('items', [])
                            if items:
                                print(f"\n📝 サンプルアイテム:")
                                sample = items[0]
                                print(f"- item keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}")
                                if isinstance(sample, dict):
                                    print(f"- platform: {sample.get('platform')}")
                                    print(f"- item_title: {sample.get('item_title')}")
                                    print(f"- total_price: {sample.get('total_price')}")
                        
                        platform_results = result_field.get('platform_results')
                        if platform_results:
                            print(f"\n🔍 プラットフォーム別結果:")
                            for platform, results in platform_results.items():
                                if isinstance(results, list):
                                    print(f"- {platform}: {len(results)}件")
                                    if results:
                                        sample = results[0]
                                        print(f"  サンプル: {sample.get('item_title', 'タイトルなし')[:30]}...")
                
                # processing_logsの確認
                processing_logs = task_info.get('processing_logs', [])
                if processing_logs:
                    print(f"\n📋 処理ログ:")
                    for log in processing_logs[-3:]:  # 最新3件
                        if isinstance(log, dict):
                            print(f"- {log.get('timestamp', 'No timestamp')}: {log.get('message', 'No message')}")
                
                # search_resultsテーブルの確認
                print(f"\n🗄️ search_resultsテーブルの状況:")
                print(f"- results_count (from API): {task_info.get('results_count', 0)}")
                print(f"- results array length: {len(task_info.get('results', []))}")
                
                # 統合検索エンジンが実際に結果を生成したかの判定
                has_integrated_results = False
                integrated_count = 0
                
                if result_field and isinstance(result_field, dict):
                    integrated_results = result_field.get('integrated_results')
                    if integrated_results and isinstance(integrated_results, dict):
                        integrated_count = integrated_results.get('count', 0)
                        has_integrated_results = integrated_count > 0
                
                print(f"\n🎯 診断結果:")
                print(f"- 統合検索エンジン実行: ✅ 完了")
                print(f"- 統合結果生成: {'✅' if has_integrated_results else '❌'} ({integrated_count}件)")
                print(f"- データベース保存: {'❌' if integrated_count > 0 and task_info.get('results_count', 0) == 0 else '✅'}")
                
                if has_integrated_results and task_info.get('results_count', 0) == 0:
                    print(f"\n🚨 問題特定:")
                    print(f"統合検索エンジンは{integrated_count}件の結果を生成しましたが、")
                    print(f"search_resultsテーブルに保存されていません。")
                    print(f"データベース保存処理に問題があります。")
                elif not has_integrated_results:
                    print(f"\n🚨 問題特定:")
                    print(f"統合検索エンジンが結果を生成していません。")
                    print(f"個別API呼び出しまたは結果統合処理に問題があります。")
                else:
                    print(f"\n✅ 正常:")
                    print(f"統合検索エンジンとデータベース保存が正常に動作しています。")
            else:
                print(f"❌ タスク取得失敗")
                print(f"レスポンス: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"レスポンス: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ 例外: {str(e)}")

if __name__ == "__main__":
    debug_unified_engine_results()
