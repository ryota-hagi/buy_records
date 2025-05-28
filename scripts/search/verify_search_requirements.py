#!/usr/bin/env python3
"""
統合検索エンジンの要件確認スクリプト
- eBay、メルカリ、Yahoo!ショッピングから各20件取得
- 合計60件を安い順に並び替え
- 最終20件のリストを表示
"""

import requests
import json
import time
from typing import Dict, List, Any

def test_unified_search_requirements():
    """統合検索の要件を詳細に確認"""
    
    print("=" * 80)
    print("統合検索エンジン要件確認テスト")
    print("=" * 80)
    
    # テスト用JANコード
    jan_code = "4549995539073"
    base_url = "http://localhost:3001"
    
    print(f"テスト対象JANコード: {jan_code}")
    print(f"ベースURL: {base_url}")
    print("-" * 60)
    
    try:
        # 1. タスク作成
        print("1. タスク作成中...")
        task_response = requests.post(f"{base_url}/api/search/tasks", 
                                    json={"jan_code": jan_code},
                                    timeout=30)
        
        if task_response.status_code != 200:
            print(f"❌ タスク作成失敗: {task_response.status_code}")
            return
            
        task_data = task_response.json()
        if not task_data.get('success'):
            print(f"❌ タスク作成失敗: {task_data}")
            return
            
        task_id = task_data['task']['id']
        print(f"✅ タスク作成成功: {task_id}")
        
        # 2. タスク完了まで待機
        print("2. タスク実行監視中...")
        max_wait = 60  # 最大60秒待機
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            detail_response = requests.get(f"{base_url}/api/search/tasks/{task_id}")
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                task_info = detail_data.get('task', {})
                status = task_info.get('status', 'unknown')
                
                elapsed = int(time.time() - start_time)
                print(f"   {elapsed}秒経過 - ステータス: {status}")
                
                if status == 'completed':
                    print("✅ タスク完了")
                    break
                elif status == 'failed':
                    print(f"❌ タスク失敗: {task_info.get('error_message', 'Unknown error')}")
                    return
                    
            time.sleep(5)
        else:
            print("❌ タスクがタイムアウトしました")
            return
        
        # 3. 結果詳細分析
        print("\n3. 検索結果詳細分析...")
        print("-" * 60)
        
        # タスク詳細を再取得
        detail_response = requests.get(f"{base_url}/api/search/tasks/{task_id}")
        detail_data = detail_response.json()
        task_info = detail_data.get('task', {})
        
        # 結果データの確認
        if 'result' in task_info and task_info['result']:
            result_data = task_info['result']
            
            # 統合結果の確認
            if 'integrated_results' in result_data:
                integrated = result_data['integrated_results']
                
                print(f"📊 統合検索結果サマリー:")
                print(f"   - 商品名: {integrated.get('product_name', 'N/A')}")
                print(f"   - 総検索結果数: {integrated.get('total_results', 0)}件")
                print(f"   - 最終結果数: {len(integrated.get('items', []))}件")
                
                # プラットフォーム別結果確認
                platform_results = integrated.get('platform_results', {})
                print(f"\n📋 プラットフォーム別結果:")
                
                yahoo_count = len(platform_results.get('yahoo_shopping', []))
                mercari_count = len(platform_results.get('mercari', []))
                ebay_count = len(platform_results.get('ebay', []))
                
                print(f"   - Yahoo!ショッピング: {yahoo_count}件")
                print(f"   - メルカリ: {mercari_count}件")
                print(f"   - eBay: {ebay_count}件")
                print(f"   - 合計: {yahoo_count + mercari_count + ebay_count}件")
                
                # 要件チェック
                print(f"\n✅ 要件確認:")
                
                # 各プラットフォーム20件チェック
                yahoo_ok = yahoo_count <= 20
                mercari_ok = mercari_count <= 20
                ebay_ok = ebay_count <= 20
                
                print(f"   - Yahoo!ショッピング ≤ 20件: {'✅' if yahoo_ok else '❌'} ({yahoo_count}件)")
                print(f"   - メルカリ ≤ 20件: {'✅' if mercari_ok else '❌'} ({mercari_count}件)")
                print(f"   - eBay ≤ 20件: {'✅' if ebay_ok else '❌'} ({ebay_count}件)")
                
                # 最終結果20件チェック
                final_items = integrated.get('items', [])
                final_count_ok = len(final_items) <= 20
                print(f"   - 最終結果 ≤ 20件: {'✅' if final_count_ok else '❌'} ({len(final_items)}件)")
                
                # 価格順ソートチェック
                if final_items:
                    prices = [item.get('total_price', 0) for item in final_items if item.get('total_price')]
                    is_sorted = all(prices[i] <= prices[i+1] for i in range(len(prices)-1))
                    print(f"   - 価格順ソート: {'✅' if is_sorted else '❌'}")
                    
                    # 価格範囲表示
                    if prices:
                        min_price = min(prices)
                        max_price = max(prices)
                        print(f"   - 価格範囲: ¥{min_price:,} ～ ¥{max_price:,}")
                
                # 詳細結果表示（最初の5件）
                print(f"\n📝 最終結果詳細（上位5件）:")
                for i, item in enumerate(final_items[:5], 1):
                    platform = item.get('platform', 'unknown')
                    title = item.get('item_title', 'No title')[:50]
                    price = item.get('total_price', 0)
                    print(f"   {i}. [{platform}] ¥{price:,} - {title}...")
                
                # 実行時間
                summary = integrated.get('summary', {})
                exec_time = summary.get('execution_time_ms', 0)
                print(f"\n⏱️  実行時間: {exec_time}ms ({exec_time/1000:.1f}秒)")
                
                # 重複除去効果
                total_found = summary.get('total_found', 0)
                after_dedup = summary.get('after_deduplication', 0)
                if total_found > 0:
                    dedup_rate = ((total_found - after_dedup) / total_found) * 100
                    print(f"🔄 重複除去: {total_found}件 → {after_dedup}件 ({dedup_rate:.1f}%削減)")
                
            else:
                print("❌ integrated_resultsが見つかりません")
                print(f"利用可能なキー: {list(result_data.keys())}")
        else:
            print("❌ 結果データが見つかりません")
            print(f"タスク情報: {task_info}")
        
        print("\n" + "=" * 80)
        print("要件確認テスト完了")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_unified_search_requirements()
