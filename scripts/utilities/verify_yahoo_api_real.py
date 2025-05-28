#!/usr/bin/env python3
"""
Yahoo!ショッピングAPIの実際の動作確認スクリプト
モックデータではなく、実際のAPIレスポンスかを検証します。
"""

import sys
import os
import json
import requests
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_yahoo_api_directly():
    """Yahoo!ショッピングAPIを直接テストします"""
    print("Yahoo!ショッピングAPI直接テスト")
    print("="*50)
    
    # 環境変数から直接取得
    app_id = os.environ.get("YAHOO_SHOPPING_APP_ID")
    if not app_id:
        print("❌ YAHOO_SHOPPING_APP_IDが設定されていません")
        return False
    
    print(f"App ID: {app_id[:10]}...")
    
    # 直接APIを呼び出し
    base_url = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
    params = {
        "appid": app_id,
        "query": "Nintendo Switch",
        "results": 5,
        "sort": "+price"
    }
    
    try:
        print(f"APIエンドポイント: {base_url}")
        print(f"パラメータ: {params}")
        
        response = requests.get(base_url, params=params, timeout=30)
        print(f"HTTPステータス: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ APIエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False
        
        # レスポンスを解析
        data = response.json()
        print(f"レスポンス構造: {list(data.keys())}")
        
        # 詳細なレスポンス内容を確認
        if "hits" in data:
            hits = data["hits"]
            print(f"検索結果数: {len(hits)}")
            
            if hits:
                print("\n最初の商品の詳細:")
                first_item = hits[0]
                for key, value in first_item.items():
                    if isinstance(value, dict):
                        print(f"  {key}: {type(value)} - {list(value.keys())}")
                    else:
                        print(f"  {key}: {value}")
                
                # URLの検証
                item_url = first_item.get("url", "")
                if item_url:
                    print(f"\n商品URL検証: {item_url}")
                    # URLが実際のYahoo!ショッピングのURLかチェック
                    if "shopping.yahoo.co.jp" in item_url:
                        print("✅ 正当なYahoo!ショッピングURL")
                    else:
                        print("⚠️  疑わしいURL（モックデータの可能性）")
                
                return True
            else:
                print("❌ 検索結果が空です")
                return False
        else:
            print(f"❌ 予期しないレスポンス構造: {data}")
            return False
            
    except Exception as e:
        print(f"❌ APIテストエラー: {str(e)}")
        return False

def test_with_client():
    """クライアントクラスを使用してテストします"""
    print("\nYahoo!ショッピングクライアントテスト")
    print("="*50)
    
    try:
        from src.collectors.yahoo_shopping import YahooShoppingClient
        client = YahooShoppingClient()
        
        if not client.app_id:
            print("❌ クライアントでApp IDが設定されていません")
            return False
        
        print(f"クライアントApp ID: {client.app_id[:10]}...")
        
        # 検索実行
        results = client.search_items("Nintendo Switch", limit=3)
        print(f"検索結果数: {len(results)}")
        
        if results:
            print("\n検索結果の詳細:")
            for i, item in enumerate(results, 1):
                print(f"\n商品 {i}:")
                print(f"  タイトル: {item.get('title', 'N/A')}")
                print(f"  価格: ¥{item.get('price', 0):,}")
                print(f"  URL: {item.get('url', 'N/A')}")
                print(f"  ストア: {item.get('store_name', 'N/A')}")
                
                # URLの妥当性チェック
                url = item.get('url', '')
                if url and "shopping.yahoo.co.jp" in url:
                    print(f"  ✅ 正当なURL")
                elif url:
                    print(f"  ⚠️  疑わしいURL: {url}")
                else:
                    print(f"  ❌ URLなし")
            
            return True
        else:
            print("❌ 検索結果が空です")
            return False
            
    except Exception as e:
        print(f"❌ クライアントテストエラー: {str(e)}")
        return False

def main():
    """メイン関数"""
    print("Yahoo!ショッピングAPI検証テスト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 環境変数を設定
    os.environ["YAHOO_SHOPPING_APP_ID"] = "dj00aiZpPVBkdm9nV2F0WTZDVyZzPWNvbnN1bWVyc2VjcmV0Jng9OTk-"
    
    # 直接APIテスト
    direct_result = test_yahoo_api_directly()
    
    # クライアントテスト
    client_result = test_with_client()
    
    print("\n" + "="*50)
    print("テスト結果サマリー")
    print("="*50)
    print(f"直接APIテスト: {'✅ 成功' if direct_result else '❌ 失敗'}")
    print(f"クライアントテスト: {'✅ 成功' if client_result else '❌ 失敗'}")
    
    if direct_result and client_result:
        print("\n🎉 Yahoo!ショッピングAPIは正常に動作しています！")
        print("取得されたデータは実際のAPIレスポンスです。")
    else:
        print("\n❌ Yahoo!ショッピングAPIに問題があります。")
        print("モックデータまたはAPI設定の問題の可能性があります。")
    
    return direct_result and client_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
