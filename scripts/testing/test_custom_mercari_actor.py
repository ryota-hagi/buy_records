#!/usr/bin/env python3
"""
カスタムMercari Actorのテストスクリプト
"""

import requests
import json
import time

def test_mercari_api():
    """Mercari APIエンドポイントをテスト"""
    
    # テスト用のパラメータ
    test_params = {
        'query': 'Nintendo Switch',
        'limit': 5
    }
    
    print("=== Mercari カスタムActor テスト ===")
    print(f"検索クエリ: {test_params['query']}")
    print(f"取得件数: {test_params['limit']}")
    
    try:
        # ローカルAPIエンドポイントを呼び出し
        url = "http://localhost:3000/api/search/mercari"
        
        print(f"\nAPIエンドポイント: {url}")
        print("リクエスト送信中...")
        
        response = requests.get(url, params=test_params, timeout=180)
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API呼び出し成功")
            print(f"プラットフォーム: {data.get('platform', 'N/A')}")
            print(f"検索クエリ: {data.get('query', 'N/A')}")
            print(f"取得件数: {data.get('total_results', 0)}")
            print(f"データソース: {data.get('data_source', 'N/A')}")
            
            # 結果の詳細を表示
            results = data.get('results', [])
            if results:
                print(f"\n📦 検索結果 ({len(results)}件):")
                for i, item in enumerate(results[:3], 1):  # 最初の3件のみ表示
                    print(f"  {i}. {item.get('title', 'タイトル不明')}")
                    print(f"     価格: {item.get('priceText', 'N/A')}")
                    print(f"     URL: {item.get('url', 'N/A')}")
                    if len(results) > 3:
                        print(f"  ... 他 {len(results) - 3} 件")
            else:
                print("⚠️ 検索結果が0件です")
                
        else:
            print(f"❌ API呼び出し失敗: {response.status_code}")
            try:
                error_data = response.json()
                print(f"エラー詳細: {error_data}")
            except:
                print(f"レスポンス: {response.text}")
                
    except requests.exceptions.Timeout:
        print("❌ タイムアウトエラー（3分）")
        print("Apify Actorの実行に時間がかかっている可能性があります")
        
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー")
        print("Next.jsサーバーが起動していることを確認してください")
        print("コマンド: npm run dev")
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")

def check_apify_status():
    """Apify Actorの状態を確認"""
    print("\n=== Apify Actor 状態確認 ===")
    print("1. Apify Consoleにアクセス: https://console.apify.com/actors")
    print("2. 'mercari-scraper' アクターを確認")
    print("3. アクター名をコピーして、以下のファイルを更新:")
    print("   src/app/api/search/mercari/route.ts")
    print("   'YOUR_USERNAME/mercari-scraper' を実際の名前に置き換え")

def main():
    print("🚀 カスタムMercari Actor テスト開始")
    
    # Apify状態確認
    check_apify_status()
    
    # ユーザーに確認
    print("\n" + "="*50)
    choice = input("APIテストを実行しますか？ (y/n): ").lower()
    
    if choice == 'y':
        test_mercari_api()
    else:
        print("テストをスキップしました")
    
    print("\n=== 次のステップ ===")
    print("1. Apify Consoleでアクター名を確認・更新")
    print("2. .env.local にAPIF_API_TOKENを設定")
    print("3. Next.jsサーバーを起動: npm run dev")
    print("4. 再度テスト実行")

if __name__ == "__main__":
    main()
