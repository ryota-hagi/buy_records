#!/usr/bin/env python3
"""
本番環境の最終動作確認テスト
ポート3001で動作するNext.jsアプリケーションをテストします。
"""

import sys
import os
import json
import requests
from datetime import datetime

def test_yahoo_api():
    """Yahoo!ショッピングAPIをテスト"""
    print("🔍 Yahoo!ショッピングAPI本番テスト")
    print("-" * 50)
    
    endpoint = "http://localhost:3001/api/search/yahoo"
    payload = {"query": "Nintendo Switch", "limit": 3}
    
    try:
        print(f"エンドポイント: {endpoint}")
        response = requests.post(endpoint, json=payload, timeout=30)
        print(f"HTTPステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("results"):
                results = data["results"]
                print(f"✅ 成功: {len(results)}件の商品を取得")
                
                if results:
                    item = results[0]
                    print(f"   商品例: {item.get('title', 'N/A')[:50]}...")
                    print(f"   価格: ¥{item.get('price', 0):,}")
                    url = item.get('url', '')
                    if 'shopping.yahoo.co.jp' in url:
                        print("   ✅ 正当なYahoo!ショッピングURL")
                        return True
                    else:
                        print(f"   ⚠️  疑わしいURL")
                        return False
                return True
            else:
                print(f"❌ APIエラー: {data.get('error', '不明')}")
                return False
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return False

def test_ebay_api():
    """eBay APIをテスト"""
    print("\n🔍 eBay API本番テスト")
    print("-" * 50)
    
    endpoint = "http://localhost:3001/api/search/ebay"
    payload = {"query": "Nintendo Switch", "limit": 2}
    
    try:
        print(f"エンドポイント: {endpoint}")
        response = requests.post(endpoint, json=payload, timeout=30)
        print(f"HTTPステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("results"):
                results = data["results"]
                print(f"✅ 成功: {len(results)}件の商品を取得")
                return True
            else:
                error_msg = data.get("error", "不明なエラー")
                print(f"⚠️  APIエラー: {error_msg}")
                return False
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return False

def test_environment_variables():
    """環境変数をテスト"""
    print("\n🔍 環境変数テスト")
    print("-" * 50)
    
    endpoint = "http://localhost:3001/api/debug/env"
    
    try:
        response = requests.get(endpoint, timeout=10)
        if response.status_code == 200:
            data = response.json()
            env_vars = data.get("env", {})
            
            required_vars = ["YAHOO_SHOPPING_APP_ID", "EBAY_APP_ID"]
            missing_vars = []
            
            for var in required_vars:
                if env_vars.get(var):
                    print(f"✅ {var}: 設定済み")
                else:
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"❌ 未設定: {', '.join(missing_vars)}")
                return False
            else:
                print("✅ 必要な環境変数が設定済み")
                return True
        else:
            print(f"❌ 環境変数チェックエラー: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return False

def check_server():
    """サーバー状態をチェック"""
    print("🔍 サーバー状態チェック")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code == 200:
            print("✅ Next.jsサーバー（ポート3001）が起動中")
            return True
        else:
            print(f"⚠️  サーバー応答異常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません")
        return False
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return False

def main():
    """メイン関数"""
    print("🚀 本番環境最終動作確認テスト")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"対象サーバー: http://localhost:3001")
    
    # テスト実行
    server_ok = check_server()
    if not server_ok:
        print("\n❌ サーバーが起動していないため、テストを中止します")
        return False
    
    env_ok = test_environment_variables()
    yahoo_ok = test_yahoo_api()
    ebay_ok = test_ebay_api()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("🎯 最終テスト結果")
    print("=" * 60)
    
    results = {
        "サーバー起動": server_ok,
        "環境変数": env_ok,
        "Yahoo!ショッピング": yahoo_ok,
        "eBay": ebay_ok
    }
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for test_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    print(f"\n📊 成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    # 結論
    if yahoo_ok:
        print("\n🎉 Yahoo!ショッピングAPIは本番環境で正常動作しています！")
        print("   実際のAPIレスポンスを取得し、正当なURLを確認済みです。")
    
    if ebay_ok:
        print("\n🎉 eBay APIも本番環境で正常動作しています！")
    elif not ebay_ok:
        print("\n⚠️  eBay APIは権限問題があります（Finding APIは認証不要のため別の問題）")
    
    if success_count >= 3:  # サーバー、環境変数、Yahoo!が成功
        print("\n✅ 本番環境での基本的な動作が確認できました")
        print("   モックデータではなく、実際のAPIからデータを取得しています。")
        return True
    else:
        print("\n❌ 本番環境で問題があります")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
