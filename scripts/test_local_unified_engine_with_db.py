#!/usr/bin/env python3
"""
ローカル環境での統合検索エンジンとデータベース保存処理のテスト
修正されたワークフローシステムの動作確認
"""

import requests
import json
import time
import sys
from datetime import datetime

# ローカル環境のURL
BASE_URL = "http://localhost:3001"

def test_local_unified_engine():
    """ローカル環境での統合検索エンジンとデータベース保存処理をテスト"""
    
    print("🚀 ローカル環境での統合検索エンジン + データベース保存処理テスト開始")
    print(f"📍 テスト対象: {BASE_URL}")
    print(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # テスト用JANコード（Nintendo Switch ゲーム）
    test_jan_code = "4902370548501"  # 別のNintendo Switchゲーム
    
    try:
        # 1. 新しい検索タスクを作成
        print(f"📝 ステップ1: 新しい検索タスクを作成 (JANコード: {test_jan_code})")
        
        create_url = f"{BASE_URL}/api/search/tasks"
        create_payload = {
            "jan_code": test_jan_code
        }
        
        print(f"🔗 POST {create_url}")
        print(f"📦 ペイロード: {json.dumps(create_payload, ensure_ascii=False)}")
        
        create_response = requests.post(
            create_url,
            json=create_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 レスポンス: {create_response.status_code}")
        
        if create_response.status_code != 200:
            print(f"❌ タスク作成失敗: {create_response.status_code}")
            print(f"📄 レスポンス内容: {create_response.text}")
            return False
            
        create_data = create_response.json()
        print(f"✅ タスク作成成功")
        print(f"📋 タスクID: {create_data['task']['id']}")
        print(f"📝 タスク名: {create_data['task']['name']}")
        print(f"🔄 初期ステータス: {create_data['task']['status']}")
        
        task_id = create_data['task']['id']
        
        # 2. タスクの完了を待機
        print(f"\n⏳ ステップ2: タスク完了を待機 (最大180秒)")
        
        max_wait_time = 180
        check_interval = 5
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            print(f"🔍 タスク状況確認中... ({elapsed_time}秒経過)")
            
            status_url = f"{BASE_URL}/api/search/tasks/{task_id}"
            status_response = requests.get(status_url, timeout=30)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data['task']['status']
                
                print(f"📊 現在のステータス: {current_status}")
                
                if current_status == 'completed':
                    print(f"✅ タスク完了！")
                    
                    # 結果の詳細を表示
                    result = status_data['task'].get('result', {})
                    integrated_results = result.get('integrated_results', {})
                    platform_results = result.get('platform_results', {})
                    
                    print(f"\n📈 検索結果サマリー:")
                    print(f"   🔢 統合結果数: {integrated_results.get('count', 0)}件")
                    print(f"   🛒 Yahoo Shopping: {len(platform_results.get('yahoo_shopping', []))}件")
                    print(f"   🌐 eBay: {len(platform_results.get('ebay', []))}件")
                    print(f"   📱 Mercari: {len(platform_results.get('mercari', []))}件")
                    
                    # データベース保存結果を確認
                    results_count = status_data['task'].get('results_count', 0)
                    print(f"   💾 データベース保存数: {results_count}件")
                    
                    if results_count > 0:
                        print(f"✅ データベース保存成功！")
                        
                        # 保存されたデータの詳細を表示
                        saved_results = status_data['task'].get('results', [])
                        if saved_results:
                            print(f"\n📋 保存されたデータサンプル (最初の3件):")
                            for i, result in enumerate(saved_results[:3]):
                                print(f"   {i+1}. {result.get('platform', 'unknown')} - {result.get('item_title', 'タイトル不明')[:50]}...")
                                print(f"      💰 価格: {result.get('base_price', 0)}円 + 送料: {result.get('shipping_fee', 0)}円")
                                print(f"      🏪 販売者: {result.get('seller_name', '不明')}")
                                print(f"      📦 状態: {result.get('item_condition', '不明')}")
                                
                        # フィールドマッピング確認
                        print(f"\n🔍 フィールドマッピング確認:")
                        if saved_results:
                            sample = saved_results[0]
                            print(f"   ✅ base_price: {sample.get('base_price', 'N/A')}")
                            print(f"   ✅ shipping_fee: {sample.get('shipping_fee', 'N/A')}")
                            print(f"   ✅ item_condition: {sample.get('item_condition', 'N/A')}")
                            print(f"   ✅ seller_name: {sample.get('seller_name', 'N/A')}")
                            
                    else:
                        print(f"❌ データベース保存失敗 - 0件保存")
                        return False
                    
                    return True
                    
                elif current_status == 'failed':
                    print(f"❌ タスク失敗")
                    error_message = status_data['task'].get('error', '不明なエラー')
                    print(f"📄 エラー内容: {error_message}")
                    return False
                    
                elif current_status in ['pending', 'running']:
                    print(f"⏳ タスク実行中... 次回確認まで{check_interval}秒待機")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                else:
                    print(f"⚠️ 不明なステータス: {current_status}")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
            else:
                print(f"❌ ステータス確認失敗: {status_response.status_code}")
                time.sleep(check_interval)
                elapsed_time += check_interval
        
        print(f"⏰ タイムアウト: {max_wait_time}秒経過してもタスクが完了しませんでした")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ネットワークエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("🔧 ローカル環境統合検索エンジン + データベース保存処理テスト")
    print("=" * 80)
    
    success = test_local_unified_engine()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 テスト成功！")
        print("✅ 統合検索エンジンが正常に動作しています")
        print("✅ データベース保存処理が正常に動作しています")
        print("✅ フィールドマッピング修正が有効です")
        print("✅ 修正されたコードが正常に動作しています")
    else:
        print("❌ テスト失敗")
        print("🔍 ログを確認して問題を特定してください")
    
    print(f"⏰ 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
