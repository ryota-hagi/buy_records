#!/usr/bin/env python3
"""
API問題の診断 - 統合検索エンジンが動かない原因を特定
"""

import requests
import json
import time
from datetime import datetime

def diagnose_api_issue():
    """API問題の診断実行"""
    
    print("🔍 API問題の診断")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"
    
    # 1. 個別APIエンドポイントのテスト
    print(f"\n1. 個別APIエンドポイントのテスト")
    print("-" * 40)
    
    apis = [
        ("Yahoo Shopping", f"{base_url}/api/search/yahoo", {"jan_code": jan_code, "limit": 5}),
        ("eBay", f"{base_url}/api/search/ebay", {"query": "マリオカート8", "limit": 5}),
        ("Mercari", f"{base_url}/api/search/mercari", {"query": "マリオカート8", "limit": 5}),
        ("統合検索", f"{base_url}/api/search/all", {"query": "マリオカート8", "limit": 5})
    ]
    
    for name, url, params in apis:
        print(f"\n{name} API テスト:")
        try:
            response = requests.get(url, params=params, timeout=30)
            print(f"  ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  成功フラグ: {data.get('success', False)}")
                
                if data.get('success'):
                    results = data.get('results', [])
                    print(f"  結果数: {len(results)}")
                    if len(results) > 0:
                        sample = results[0]
                        print(f"  サンプル: {sample.get('title', 'タイトルなし')[:50]}...")
                    else:
                        print(f"  ⚠️ 結果は0件")
                else:
                    error = data.get('error', 'Unknown error')
                    print(f"  ❌ エラー: {error}")
            else:
                print(f"  ❌ HTTPエラー: {response.status_code}")
                print(f"  レスポンス: {response.text[:200]}...")
                
        except Exception as e:
            print(f"  ❌ 例外: {str(e)}")
    
    # 2. 統合検索エンジンの直接テスト
    print(f"\n2. 統合検索エンジンの直接テスト")
    print("-" * 40)
    
    try:
        # 統合検索エンジンのテスト用エンドポイント
        url = f"{base_url}/api/search/test"
        payload = {"jan_code": jan_code}
        
        print(f"統合検索エンジンテスト実行...")
        response = requests.post(url, json=payload, timeout=60)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功フラグ: {data.get('success', False)}")
            
            if data.get('success'):
                result = data.get('result', {})
                final_results = result.get('final_results', [])
                platform_results = result.get('platform_results', {})
                
                print(f"最終結果数: {len(final_results)}")
                print(f"プラットフォーム別:")
                print(f"  - Yahoo: {len(platform_results.get('yahoo_shopping', []))}件")
                print(f"  - eBay: {len(platform_results.get('ebay', []))}件")
                print(f"  - Mercari: {len(platform_results.get('mercari', []))}件")
                
                if len(final_results) > 0:
                    sample = final_results[0]
                    print(f"サンプル結果:")
                    print(f"  - タイトル: {sample.get('item_title', 'なし')}")
                    print(f"  - 価格: {sample.get('total_price', 'なし')}")
                    print(f"  - プラットフォーム: {sample.get('platform', 'なし')}")
                else:
                    print(f"⚠️ 統合検索でも結果が0件")
            else:
                error = data.get('error', 'Unknown error')
                print(f"❌ 統合検索エラー: {error}")
        else:
            print(f"❌ 統合検索HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ 統合検索例外: {str(e)}")
    
    # 3. 環境変数の確認
    print(f"\n3. 環境変数の確認")
    print("-" * 40)
    
    try:
        url = f"{base_url}/api/debug/env"
        response = requests.get(url, timeout=30)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            env_status = data.get('env_status', {})
            
            print(f"環境変数ステータス:")
            for key, status in env_status.items():
                print(f"  - {key}: {'✅' if status else '❌'}")
        else:
            print(f"❌ 環境変数確認失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 環境変数確認例外: {str(e)}")
    
    # 4. 問題の分析
    print(f"\n4. 問題の分析")
    print("-" * 40)
    
    print(f"現在の症状:")
    print(f"  - ワークフロータスクが17回以上running状態で停止")
    print(f"  - 結果数がずっと0件")
    print(f"  - 統合検索エンジンが応答しない可能性")
    
    print(f"\n考えられる原因:")
    print(f"  1. 統合検索エンジンの無限ループ")
    print(f"  2. APIエンドポイントのタイムアウト")
    print(f"  3. 環境変数の問題")
    print(f"  4. Vercelの実行時間制限")
    print(f"  5. データベース接続問題")
    
    print(f"\n次のアクション:")
    print(f"  1. 個別APIエンドポイントが動作するか確認")
    print(f"  2. 統合検索エンジンのタイムアウト設定を確認")
    print(f"  3. より軽量な検索処理に変更")
    print(f"  4. エラーハンドリングの強化")

if __name__ == "__main__":
    diagnose_api_issue()
