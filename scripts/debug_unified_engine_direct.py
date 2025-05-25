#!/usr/bin/env python3
"""
統合検索エンジンの直接デバッグ
"""

import requests
import json
import time
from datetime import datetime

def debug_unified_engine_direct():
    """統合検索エンジンの直接デバッグ"""
    
    print("🔍 統合検索エンジン直接デバッグ")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"
    
    # 1. 統合検索エンジンのテストエンドポイントを直接呼び出し
    print(f"\n1. 統合検索エンジンテストエンドポイント直接呼び出し")
    print("-" * 50)
    
    try:
        url = f"{base_url}/api/search/test"
        payload = {"jan_code": jan_code}
        
        print(f"URL: {url}")
        print(f"Payload: {payload}")
        print(f"統合検索エンジンテスト実行中...")
        
        response = requests.post(url, json=payload, timeout=120)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功フラグ: {data.get('success', False)}")
            
            if data.get('success'):
                result = data.get('result', {})
                final_results = result.get('final_results', [])
                platform_results = result.get('platform_results', {})
                
                print(f"✅ 統合検索エンジン成功！")
                print(f"最終結果数: {len(final_results)}")
                print(f"プラットフォーム別結果:")
                print(f"  - Yahoo: {len(platform_results.get('yahoo_shopping', []))}件")
                print(f"  - eBay: {len(platform_results.get('ebay', []))}件")
                print(f"  - Mercari: {len(platform_results.get('mercari', []))}件")
                
                if len(final_results) > 0:
                    sample = final_results[0]
                    print(f"サンプル結果:")
                    print(f"  - タイトル: {sample.get('item_title', 'なし')}")
                    print(f"  - 価格: {sample.get('total_price', 'なし')}")
                    print(f"  - プラットフォーム: {sample.get('platform', 'なし')}")
                    
                    print(f"\n🎯 統合検索エンジンは正常に動作しています！")
                    print(f"問題はワークフローシステムの統合部分にあります。")
                else:
                    print(f"⚠️ 統合検索エンジンは動作するが結果が0件")
            else:
                error = data.get('error', 'Unknown error')
                print(f"❌ 統合検索エンジンエラー: {error}")
                print(f"詳細レスポンス: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text[:1000]}...")
            
    except Exception as e:
        print(f"❌ 統合検索エンジンテスト例外: {str(e)}")
    
    # 2. 個別APIエンドポイントの再確認
    print(f"\n2. 個別APIエンドポイントの再確認")
    print("-" * 50)
    
    apis = [
        ("Yahoo Shopping", f"{base_url}/api/search/yahoo", {"jan_code": jan_code, "limit": 5}),
        ("eBay", f"{base_url}/api/search/ebay", {"query": "マリオカート8", "limit": 5}),
        ("Mercari", f"{base_url}/api/search/mercari", {"query": "マリオカート8", "limit": 5})
    ]
    
    api_working = True
    for name, url, params in apis:
        print(f"\n{name} API:")
        try:
            response = requests.get(url, params=params, timeout=30)
            print(f"  ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                results_count = len(data.get('results', []))
                print(f"  成功: {success}")
                print(f"  結果数: {results_count}")
                
                if not success or results_count == 0:
                    api_working = False
                    print(f"  ❌ {name} APIに問題があります")
            else:
                api_working = False
                print(f"  ❌ {name} API HTTPエラー: {response.status_code}")
                
        except Exception as e:
            api_working = False
            print(f"  ❌ {name} API例外: {str(e)}")
    
    # 3. 問題の分析と解決策
    print(f"\n3. 問題の分析と解決策")
    print("-" * 50)
    
    if api_working:
        print(f"✅ 個別APIは正常に動作しています")
        print(f"❌ 問題は統合検索エンジンまたはワークフローシステムにあります")
        
        print(f"\n考えられる原因:")
        print(f"1. 統合検索エンジンのフィールドマッピング問題")
        print(f"2. Promise.allSettledの処理問題")
        print(f"3. TypeScriptコンパイルエラー")
        print(f"4. 環境変数の問題")
        print(f"5. タイムアウト設定の問題")
        
        print(f"\n次のアクション:")
        print(f"1. 統合検索エンジンを簡素化")
        print(f"2. エラーハンドリングを強化")
        print(f"3. ログ出力を増やす")
        print(f"4. 直接API呼び出し方式に変更")
    else:
        print(f"❌ 個別APIに問題があります")
        print(f"まず個別APIを修正する必要があります")

if __name__ == "__main__":
    debug_unified_engine_direct()
