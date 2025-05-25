#!/usr/bin/env python3
"""
すべてのAPIを実際のAPIに修正し、モックデータを排除するスクリプト
"""

import requests
import json
import time

def test_yahoo_api_directly():
    """Yahoo!ショッピングAPIを直接テスト"""
    print("🔍 Yahoo!ショッピングAPI直接テスト")
    
    app_id = "dj00aiZpPVBkdm9nV2F0WTZDVyZzPWNvbnN1bWVyc2VjcmV0Jng9OTk-"
    url = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
    
    params = {
        'appid': app_id,
        'query': 'Nintendo Switch',
        'results': 5
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"  ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get('hits', [])
            print(f"  ✅ Yahoo!ショッピングAPI: {len(hits)}件取得成功")
            
            if hits:
                for i, item in enumerate(hits[:2]):
                    print(f"    {i+1}. {item.get('name', 'タイトル不明')} - ¥{item.get('price', 0):,}")
            return True
        else:
            print(f"  ❌ Yahoo!ショッピングAPI: HTTP {response.status_code}")
            print(f"  レスポンス: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Yahoo!ショッピングAPI: {str(e)}")
        return False

def test_environment_variables():
    """Next.jsサーバーの環境変数をテスト"""
    print("\n🔍 Next.jsサーバー環境変数テスト")
    
    try:
        response = requests.get("http://localhost:3000/api/debug/env", timeout=10)
        if response.status_code == 200:
            data = response.json()
            yahoo_app_id = data.get('YAHOO_SHOPPING_APP_ID')
            
            if yahoo_app_id:
                print(f"  ✅ YAHOO_SHOPPING_APP_ID: 設定済み ({yahoo_app_id[:10]}...)")
                return True
            else:
                print(f"  ❌ YAHOO_SHOPPING_APP_ID: 未設定")
                return False
        else:
            print(f"  ❌ 環境変数API: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 環境変数API: {str(e)}")
        return False

def main():
    print("🚀 全APIシステム実API化修正スクリプト")
    print("=" * 60)
    
    # 1. Yahoo!ショッピングAPI直接テスト
    yahoo_direct_ok = test_yahoo_api_directly()
    
    # 2. Next.js環境変数テスト
    env_ok = test_environment_variables()
    
    print("\n" + "=" * 60)
    print("📋 診断結果")
    print("=" * 60)
    
    print(f"Yahoo!ショッピングAPI直接呼び出し: {'✅' if yahoo_direct_ok else '❌'}")
    print(f"Next.js環境変数読み込み: {'✅' if env_ok else '❌'}")
    
    if yahoo_direct_ok and not env_ok:
        print("\n🔧 問題: Next.jsサーバーで環境変数が読み込まれていません")
        print("解決策:")
        print("1. サーバーを再起動する")
        print("2. .env.localファイルの形式を確認する")
        print("3. 環境変数の設定を修正する")
    elif not yahoo_direct_ok:
        print("\n🔧 問題: Yahoo!ショッピングAPIキーが無効です")
        print("解決策:")
        print("1. APIキーを確認する")
        print("2. Yahoo!デベロッパーコンソールで設定を確認する")
    else:
        print("\n✅ 基本的な設定は正常です")
    
    print("\n次のステップ:")
    print("1. Yahoo!ショッピングAPIの修正")
    print("2. eBayとMercariの実API実装")
    print("3. モックデータの完全排除")

if __name__ == "__main__":
    main()
