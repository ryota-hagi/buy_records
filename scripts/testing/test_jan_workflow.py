#!/usr/bin/env python3
"""
JANコードワークフローのテストスクリプト
"""

import requests
import json
import time
import sys

def test_jan_workflow():
    """JANコードワークフローの動作確認"""
    
    base_url = "http://localhost:3001"
    test_jan_code = "4549995539073"  # 実在するJANコード
    
    print(f"JANコードワークフローテスト開始")
    print(f"テスト対象JANコード: {test_jan_code}")
    print(f"ベースURL: {base_url}")
    print("-" * 50)
    
    try:
        # 1. タスク作成
        print("1. タスク作成中...")
        create_response = requests.post(
            f"{base_url}/api/search/tasks",
            json={"jan_code": test_jan_code},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if create_response.status_code != 200:
            print(f"❌ タスク作成失敗: HTTP {create_response.status_code}")
            print(f"レスポンス: {create_response.text}")
            return False
            
        create_data = create_response.json()
        if not create_data.get('success'):
            print(f"❌ タスク作成失敗: {create_data.get('error')}")
            return False
            
        task_id = create_data['task']['id']
        task_name = create_data['task']['name']
        print(f"✅ タスク作成成功")
        print(f"   タスクID: {task_id}")
        print(f"   タスク名: {task_name}")
        
        # 2. タスク実行の監視
        print("\n2. タスク実行監視中...")
        max_wait_time = 120  # 最大2分待機
        check_interval = 5   # 5秒間隔でチェック
        
        for i in range(max_wait_time // check_interval):
            time.sleep(check_interval)
            
            # タスク状態確認
            status_response = requests.get(
                f"{base_url}/api/search/tasks/{task_id}",
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('success'):
                    task = status_data.get('task', {})
                    status = task.get('status', 'unknown')
                    
                    print(f"   {i*check_interval}秒経過 - ステータス: {status}")
                    
                    if status == 'completed':
                        print("✅ タスク完了")
                        
                        # 結果確認
                        result = task.get('result', {})
                        integrated_results = result.get('integrated_results', {})
                        total_count = integrated_results.get('count', 0)
                        
                        print(f"   検索結果: {total_count}件")
                        
                        if total_count > 0:
                            print("✅ 検索結果取得成功")
                            
                            # プラットフォーム別結果表示
                            platform_results = result.get('platform_results', {})
                            for platform, items in platform_results.items():
                                if items:
                                    print(f"   - {platform}: {len(items)}件")
                            
                            return True
                        else:
                            print("⚠️ 検索結果が0件です")
                            return False
                            
                    elif status == 'failed':
                        error_msg = task.get('error', 'Unknown error')
                        print(f"❌ タスク失敗: {error_msg}")
                        return False
                        
                    elif status in ['pending', 'running']:
                        continue  # 継続監視
                    else:
                        print(f"⚠️ 不明なステータス: {status}")
            else:
                print(f"⚠️ ステータス確認失敗: HTTP {status_response.status_code}")
        
        print("❌ タスク完了タイムアウト")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def test_task_list():
    """タスク一覧取得のテスト"""
    
    base_url = "http://localhost:3001"
    
    print("\n3. タスク一覧取得テスト...")
    
    try:
        response = requests.get(f"{base_url}/api/search/tasks", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                tasks = data.get('tasks', [])
                print(f"✅ タスク一覧取得成功: {len(tasks)}件")
                
                # 最新のタスクを表示
                if tasks:
                    latest_task = tasks[0]
                    print(f"   最新タスク:")
                    print(f"   - ID: {latest_task.get('id')}")
                    print(f"   - 名前: {latest_task.get('name')}")
                    print(f"   - ステータス: {latest_task.get('status')}")
                    print(f"   - 作成日時: {latest_task.get('created_at')}")
                
                return True
            else:
                print(f"❌ タスク一覧取得失敗: {data.get('error')}")
                return False
        else:
            print(f"❌ タスク一覧取得失敗: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ タスク一覧取得エラー: {e}")
        return False

def main():
    """メイン関数"""
    
    print("=" * 60)
    print("JANコードワークフロー 動作確認テスト")
    print("=" * 60)
    
    # 開発サーバーの動作確認
    try:
        response = requests.get("http://localhost:3001/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 開発サーバー動作確認")
        else:
            print("❌ 開発サーバーが応答しません")
            print("npm run dev でサーバーを起動してください")
            return
    except:
        print("❌ 開発サーバーに接続できません")
        print("npm run dev でサーバーを起動してください")
        return
    
    # JANコードワークフローテスト
    workflow_success = test_jan_workflow()
    
    # タスク一覧テスト
    list_success = test_task_list()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"JANコードワークフロー: {'✅ 成功' if workflow_success else '❌ 失敗'}")
    print(f"タスク一覧取得: {'✅ 成功' if list_success else '❌ 失敗'}")
    
    if workflow_success and list_success:
        print("\n🎉 すべてのテストが成功しました！")
        print("JANコードワークフローは正常に動作しています。")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")
        print("ログを確認して問題を修正してください。")

if __name__ == "__main__":
    main()
