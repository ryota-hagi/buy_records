#!/usr/bin/env python3
"""
eBayトークン更新後の詳細診断
"""

import requests
import json
from datetime import datetime

def diagnose_post_update():
    """トークン更新後の問題を詳細診断"""
    
    print("🔍 eBayトークン更新後の詳細診断")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 1. 基本的な接続確認
    print("1. 基本接続確認")
    print("-" * 40)
    
    base_url = "https://buy-records.vercel.app"
    
    try:
        response = requests.get(base_url, timeout=10)
        print(f"✅ サイト接続: {response.status_code}")
    except Exception as e:
        print(f"❌ サイト接続失敗: {str(e)}")
        return
    
    # 2. 各APIエンドポイントの存在確認
    print("\n2. APIエンドポイント存在確認")
    print("-" * 40)
    
    endpoints = [
        "/api/search/yahoo",
        "/api/search/ebay", 
        "/api/search/mercari",
        "/api/search/all",
        "/api/test-production"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 404:
                print(f"❌ {endpoint}: 404 (エンドポイント不存在)")
            elif response.status_code == 500:
                print(f"⚠️  {endpoint}: 500 (サーバーエラー)")
            elif response.status_code == 400:
                print(f"✅ {endpoint}: 400 (パラメータエラー - 正常)")
            else:
                print(f"❓ {endpoint}: {response.status_code}")
                
        except Exception as e:
            print(f"💥 {endpoint}: 接続エラー ({str(e)})")
    
    # 3. 詳細エラー分析
    print("\n3. 詳細エラー分析")
    print("-" * 40)
    
    # Yahoo APIの詳細エラー
    try:
        url = f"{base_url}/api/search/yahoo"
        params = {'jan_code': '4902370536485', 'limit': 1}
        response = requests.get(url, params=params, timeout=15)
        
        print(f"Yahoo API:")
        print(f"  ステータス: {response.status_code}")
        
        if response.status_code == 500:
            try:
                error_data = response.json()
                print(f"  エラー: {error_data.get('error', 'Unknown')}")
                print(f"  詳細: {error_data.get('details', 'No details')}")
            except:
                print(f"  レスポンス: {response.text[:200]}...")
                
    except Exception as e:
        print(f"Yahoo API診断エラー: {str(e)}")
    
    # eBay APIの詳細エラー
    try:
        url = f"{base_url}/api/search/ebay"
        params = {'jan_code': '4902370536485', 'limit': 1}
        response = requests.get(url, params=params, timeout=15)
        
        print(f"\neBay API:")
        print(f"  ステータス: {response.status_code}")
        
        if response.status_code == 500:
            try:
                error_data = response.json()
                print(f"  エラー: {error_data.get('error', 'Unknown')}")
                print(f"  詳細: {error_data.get('details', 'No details')}")
            except:
                print(f"  レスポンス: {response.text[:200]}...")
                
    except Exception as e:
        print(f"eBay API診断エラー: {str(e)}")
    
    # 4. 環境変数確認（テストAPI経由）
    print("\n4. 環境変数確認")
    print("-" * 40)
    
    try:
        # テストAPIが404なので、直接確認は困難
        print("⚠️  テストAPIが404のため、環境変数の直接確認は不可")
        print("   Vercelダッシュボードでの確認が必要")
        
    except Exception as e:
        print(f"環境変数確認エラー: {str(e)}")
    
    # 5. 推定される問題と解決策
    print("\n5. 推定される問題と解決策")
    print("=" * 70)
    
    problems = [
        {
            "問題": "デプロイ問題",
            "症状": "404エラー（Mercari、統合検索、テストAPI）",
            "原因": "最新コードがVercelにデプロイされていない",
            "解決策": "Vercelで手動再デプロイを実行"
        },
        {
            "問題": "環境変数問題",
            "症状": "500エラー（Yahoo、eBay）",
            "原因": "APIキー/トークンが正しく設定されていない",
            "解決策": "Vercel環境変数の再確認・更新"
        },
        {
            "問題": "コード問題",
            "症状": "500エラーが継続",
            "原因": "APIルートハンドラーのバグ",
            "解決策": "ローカルでのデバッグとコード修正"
        },
        {
            "問題": "IP制限",
            "症状": "特定のAPIで403エラー",
            "原因": "VercelのIPアドレスが制限対象",
            "解決策": "プロキシサービスまたは代替API"
        }
    ]
    
    for i, problem in enumerate(problems, 1):
        print(f"\n{i}. {problem['問題']}")
        print(f"   症状: {problem['症状']}")
        print(f"   原因: {problem['原因']}")
        print(f"   解決策: {problem['解決策']}")
    
    # 6. 即座に実行すべきアクション
    print("\n6. 即座に実行すべきアクション")
    print("=" * 70)
    
    actions = [
        "1. Vercelダッシュボードで手動再デプロイを実行",
        "2. 環境変数YAHOO_SHOPPING_APP_IDを正しい値に更新",
        "3. 環境変数EBAY_USER_TOKENが正しく設定されているか確認",
        "4. デプロイ後、再度APIテストを実行",
        "5. それでも解決しない場合、ローカル環境でのデバッグ"
    ]
    
    for action in actions:
        print(f"   {action}")
    
    # 7. 現在の状況サマリー
    print("\n7. 現在の状況サマリー")
    print("=" * 70)
    
    print("✅ 完了済み:")
    print("   - IPアドレス特定（216.198.79.1 - Amazon/Vercel）")
    print("   - eBayトークン更新")
    print("   - コードレベルの修正")
    
    print("\n❌ 未解決:")
    print("   - Yahoo API: 500エラー（環境変数問題）")
    print("   - eBay API: 500エラー（設定問題）")
    print("   - Mercari API: 404エラー（デプロイ問題）")
    print("   - 統合検索: 404エラー（デプロイ問題）")
    
    print("\n🎯 最優先タスク:")
    print("   1. Vercel再デプロイ（404エラー解決）")
    print("   2. Yahoo APIキー更新（500エラー解決）")
    print("   3. 全体テスト再実行")

if __name__ == "__main__":
    diagnose_post_update()
