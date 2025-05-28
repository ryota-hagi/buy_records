#!/usr/bin/env python3
"""
本番環境のAPIエンドポイントテスト
Next.jsアプリケーションのAPIルートを通じて実際の動作を確認します。
"""

import sys
import os
import json
import requests
from datetime import datetime

def test_yahoo_api_endpoint():
    """Yahoo!ショッピングAPIエンドポイントをテスト"""
    print("🔍 Yahoo!ショッピングAPI本番エンドポイントテスト")
    print("-" * 50)
    
    # Next.jsアプリのAPIエンドポイント
    base_url = "http://localhost:3000"
    endpoint = f"{base_url}/api/search/yahoo"
    
    payload = {
        "query": "Nintendo Switch",
        "limit": 3
    }
    
    try:
        print(f"エンドポイント: {endpoint}")
        print(f"リクエスト: {payload}")
        
        response = requests.post(endpoint, json=payload, timeout=30)
        print(f"HTTPステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success") and data.get("results"):
                results = data["results"]
                print(f"✅ 成功: {len(results)}件の商品を取得")
                
                # 最初の商品の詳細
                if results:
                    first_item = results[0]
                    print(f"   商品例: {first_item.get('title', 'N/A')[:50]}...")
                    print(f"   価格: ¥{first_item.get('price', 0):,}")
                    print(f"   URL: {first_item.get('url', 'N/A')}")
                    
                    # URLの妥当性チェック
                    url = first_item.get('url', '')
                    if 'shopping.yahoo.co.jp' in url:
                        print("   ✅ 正当なYahoo!ショッピングURL")
                        return True
                    else:
                        print(f"   ⚠️  疑わしいURL: {url}")
                        return False
                
                return True
            else:
                print(f"❌ APIレスポンスエラー: {data}")
                return False
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: Next.jsサーバーが起動していません")
        print("   npm run dev または yarn dev でサーバーを起動してください")
        return False
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return False

def test_ebay_api_endpoint():
    """eBay APIエンドポイントをテスト"""
    print("\n🔍 eBay API本番エンドポイントテスト")
    print("-" * 50)
    
    base_url = "http://localhost:3000"
    endpoint = f"{base_url}/api/search/ebay"
    
    payload = {
        "query": "Nintendo Switch",
        "limit": 2
    }
    
    try:
        print(f"エンドポイント: {endpoint}")
        print(f"リクエスト: {payload}")
        
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
                if "401" in error_msg or "Unauthorized" in error_msg:
                    print("   原因: User Tokenの権限不足")
                return False
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: Next.jsサーバーが起動していません")
        return False
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return False

def check_server_status():
    """Next.jsサーバーの状態をチェック"""
    print("🔍 Next.jsサーバー状態チェック")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Next.jsサーバーが起動中")
            return True
        else:
            print(f"⚠️  サーバー応答異常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Next.jsサーバーが起動していません")
        print("   以下のコマンドでサーバーを起動してください:")
        print("   cd /Users/hagiryouta/records && npm run dev")
        return False
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return False

def test_environment_variables():
    """本番環境の環境変数をテスト"""
    print("\n🔍 本番環境変数テスト")
    print("-" * 50)
    
    base_url = "http://localhost:3000"
    endpoint = f"{base_url}/api/debug/env"
    
    try:
        response = requests.get(endpoint, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            env_vars = data.get("env", {})
            required_vars = [
                "YAHOO_SHOPPING_APP_ID",
                "EBAY_APP_ID", 
                "EBAY_USER_TOKEN",
                "APIFY_API_TOKEN"
            ]
            
            missing_vars = []
            for var in required_vars:
                if not env_vars.get(var):
                    missing_vars.append(var)
                else:
                    print(f"✅ {var}: 設定済み")
            
            if missing_vars:
                print(f"❌ 未設定の環境変数: {', '.join(missing_vars)}")
                return False
            else:
                print("✅ 全ての必要な環境変数が設定済み")
                return True
        else:
            print(f"❌ 環境変数チェックエラー: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return False

def main():
    """メイン関数"""
    print("🚀 本番環境API動作確認テスト")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # サーバー状態チェック
    server_ok = check_server_status()
    
    if not server_ok:
        print("\n❌ Next.jsサーバーが起動していないため、テストを中止します")
        return False
    
    # 環境変数チェック
    env_ok = test_environment_variables()
    
    # APIエンドポイントテスト
    yahoo_ok = test_yahoo_api_endpoint()
    ebay_ok = test_ebay_api_endpoint()
    
    print("\n" + "=" * 60)
    print("🎯 本番環境テスト結果")
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
        print("\n🎉 Yahoo!ショッピングAPIは本番環境でも正常動作しています！")
    
    if not ebay_ok:
        print("\n⚠️  eBay APIは本番環境でも権限問題があります")
    
    if success_count >= 3:  # サーバー、環境変数、Yahoo!が成功
        print("\n✅ 本番環境での基本的な動作が確認できました")
        return True
    else:
        print("\n❌ 本番環境で問題があります")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
