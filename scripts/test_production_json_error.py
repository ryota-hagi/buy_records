#!/usr/bin/env python3
"""
本番環境でのJSONエラーを調査するスクリプト
"""

import requests
import json
import sys

def test_production_api():
    """本番環境のAPIをテスト"""
    
    base_url = "https://buy-records.vercel.app"
    
    print("🔍 本番環境APIテスト開始")
    print(f"Base URL: {base_url}")
    print("=" * 50)
    
    # テスト用JANコード
    jan_code = "4902370542912"
    
    # 1. タスク作成APIをテスト
    print("\n1. タスク作成APIテスト")
    print("-" * 30)
    
    try:
        url = f"{base_url}/api/search/tasks"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        payload = {
            "jan_code": jan_code
        }
        
        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\nレスポンス:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # レスポンステキストを取得
        response_text = response.text
        print(f"Response Text Length: {len(response_text)}")
        print(f"Response Text (first 500 chars): {response_text[:500]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"JSON Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get('success') and data.get('task'):
                    task_id = data['task']['id']
                    print(f"✅ タスク作成成功: {task_id}")
                    
                    # タスク詳細を取得
                    print(f"\n2. タスク詳細取得テスト")
                    print("-" * 30)
                    
                    detail_url = f"{base_url}/api/search/tasks/{task_id}"
                    detail_response = requests.get(detail_url, headers=headers, timeout=30)
                    
                    print(f"Detail URL: {detail_url}")
                    print(f"Detail Status: {detail_response.status_code}")
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        print(f"Detail Response: {json.dumps(detail_data, indent=2, ensure_ascii=False)}")
                    else:
                        print(f"❌ タスク詳細取得失敗: {detail_response.text}")
                        
                else:
                    print(f"❌ タスク作成失敗: {data}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析エラー: {e}")
                print(f"Raw response: {response_text}")
                
        else:
            print(f"❌ HTTP エラー: {response.status_code}")
            print(f"Error response: {response_text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        
    # 3. 統合検索エンジンの直接テスト
    print(f"\n3. 統合検索エンジン直接テスト")
    print("-" * 30)
    
    try:
        # 統合検索エンジンのテスト用エンドポイントがあるかチェック
        test_url = f"{base_url}/api/search/test"
        test_response = requests.get(test_url, headers=headers, timeout=30)
        
        print(f"Test URL: {test_url}")
        print(f"Test Status: {test_response.status_code}")
        
        if test_response.status_code == 200:
            test_data = test_response.json()
            print(f"Test Response: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Test endpoint not available: {test_response.text}")
            
    except Exception as e:
        print(f"統合検索エンジンテストエラー: {e}")

if __name__ == "__main__":
    test_production_api()
