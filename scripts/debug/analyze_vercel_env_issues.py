#!/usr/bin/env python3
"""
Vercel環境変数設定の問題分析
画像から確認された設定問題を特定
"""

def analyze_vercel_env_issues():
    """Vercel環境変数の問題を分析"""
    
    print("🚨 Vercel環境変数設定の重大な問題を発見！")
    print("=" * 70)
    
    # 画像から確認された環境変数
    current_env_vars = [
        "GOOGLE_TRANSLATE_API_KEY",
        "EBAY_CLIENT_SECRET", 
        "apify_api",
        "EBAY_CERT_ID",
        "EBAY_DEV_ID",
        "SUPABASE_SERVICE_ROLE_KEY",
        "GOOGLE_CLOUD_CREDENTIALS_JSON",
        "JAN_LOOKUP_APP_ID",
        "EBAY_APP_ID",
        "YAHOO_SHOPPING_APP_ID",
        "DISCOGS_TOKEN",
        "DISCOGS_USER_AGENT",
        "MERCARI_REQUEST_DELAY",
        "EBAY_TOKEN_EXPIRY",
        "EBAY_VERIFICATION_TOKEN",
        "EBAY_USER_TOKEN",
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY"
    ]
    
    # コードで期待される環境変数
    expected_env_vars = [
        "YAHOO_SHOPPING_APP_ID",  # ✅ 存在
        "EBAY_APP_ID",           # ✅ 存在
        "EBAY_CLIENT_SECRET",    # ✅ 存在
        "EBAY_DEV_ID",           # ✅ 存在
        "EBAY_CERT_ID",          # ✅ 存在
    ]
    
    print("📋 環境変数チェック結果")
    print("-" * 50)
    
    for var in expected_env_vars:
        if var in current_env_vars:
            print(f"✅ {var}: 設定済み")
        else:
            print(f"❌ {var}: 未設定")
    
    print("\n🔍 発見された問題")
    print("=" * 70)
    
    issues = [
        {
            "issue": "Yahoo!ショッピングAPIキーの形式問題",
            "description": "dj00aiZpPVBkdm9nV2F0WTZDVyZzPWNvbnN1bWVyc2VjcmV0Jng9OTk- が表示されている",
            "problem": "これはコード内のハードコーディングされたデフォルト値",
            "solution": "正しいYahoo!ショッピングAPIキーに更新が必要",
            "severity": "🚨 Critical"
        },
        {
            "issue": "eBayトークンの有効期限",
            "description": "EBAY_TOKEN_EXPIRY: 2026-11-13T13:23:04Z",
            "problem": "トークンが期限切れまたは無効の可能性",
            "solution": "eBay Developer Consoleで新しいトークンを生成",
            "severity": "⚠️ High"
        },
        {
            "issue": "環境変数の命名不一致",
            "description": "一部の環境変数名がコードと異なる可能性",
            "problem": "大文字小文字やアンダースコアの違い",
            "solution": "コードと環境変数名を完全一致させる",
            "severity": "⚠️ Medium"
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['severity']} {issue['issue']}")
        print(f"   説明: {issue['description']}")
        print(f"   問題: {issue['problem']}")
        print(f"   解決策: {issue['solution']}")
    
    print("\n🎯 最優先で修正すべき問題")
    print("=" * 70)
    
    critical_fixes = [
        {
            "priority": 1,
            "action": "Yahoo!ショッピングAPIキーの更新",
            "current": "dj00aiZpPVBkdm9nV2F0WTZDVyZzPWNvbnN1bWVyc2VjcmV0Jng9OTk-",
            "required": "Yahoo Developer Consoleから取得した正しいAPIキー",
            "impact": "Yahoo!ショッピング検索の400エラーを解決"
        },
        {
            "priority": 2,
            "action": "eBayトークンの更新",
            "current": "期限切れまたは無効なトークン",
            "required": "eBay Developer Consoleから新しいアクセストークンを生成",
            "impact": "eBay検索の500エラーを解決"
        },
        {
            "priority": 3,
            "action": "環境変数名の確認",
            "current": "大文字小文字の不一致の可能性",
            "required": "コードと完全に一致する変数名",
            "impact": "環境変数が読み込まれない問題を解決"
        }
    ]
    
    for fix in critical_fixes:
        print(f"\n優先度{fix['priority']}: {fix['action']}")
        print(f"   現在: {fix['current']}")
        print(f"   必要: {fix['required']}")
        print(f"   効果: {fix['impact']}")
    
    print("\n🔧 即座に実行すべき手順")
    print("=" * 70)
    
    steps = [
        "1. Yahoo Developer Console (https://developer.yahoo.co.jp/) にアクセス",
        "2. 新しいYahoo!ショッピングAPIキーを生成",
        "3. Vercelで YAHOO_SHOPPING_APP_ID を新しいキーに更新",
        "4. eBay Developer Console (https://developer.ebay.com/) にアクセス",
        "5. 新しいアクセストークンを生成",
        "6. Vercelで EBAY_USER_TOKEN を新しいトークンに更新",
        "7. Vercelで再デプロイを実行",
        "8. テストAPIで環境変数の確認"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    return issues, critical_fixes

def create_env_verification_script():
    """環境変数検証用のテストスクリプトを作成"""
    
    test_script = '''
import requests
import json

def test_vercel_env_vars():
    """Vercel環境変数をテスト"""
    
    url = "https://buy-records.vercel.app/api/test-production"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("🧪 Vercel環境変数テスト結果")
            print("=" * 50)
            print(f"環境: {data['data']['environment']}")
            print(f"リージョン: {data['data']['vercel_region']}")
            print(f"Yahoo APIキー存在: {data['data']['yahoo_api_key_exists']}")
            print(f"Yahoo APIキー長: {data['data']['yahoo_api_key_length']}")
            print(f"eBay APIキー存在: {data['data']['ebay_api_key_exists']}")
            print(f"eBay APIキー長: {data['data']['ebay_api_key_length']}")
            
            # 問題の特定
            if data['data']['yahoo_api_key_length'] == 60:
                print("⚠️  Yahoo APIキーがデフォルト値の可能性")
            
            if not data['data']['yahoo_api_key_exists']:
                print("❌ Yahoo APIキーが設定されていません")
                
            if not data['data']['ebay_api_key_exists']:
                print("❌ eBay APIキーが設定されていません")
                
        else:
            print(f"❌ テストAPI失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")

if __name__ == "__main__":
    test_vercel_env_vars()
'''
    
    print("\n🧪 環境変数検証スクリプト")
    print("=" * 70)
    print("以下のスクリプトで環境変数を確認できます:")
    print(test_script)

if __name__ == "__main__":
    issues, critical_fixes = analyze_vercel_env_issues()
    create_env_verification_script()
    
    print(f"\n🎯 結論: 環境変数設定に重大な問題があります")
    print(f"特にYahoo!ショッピングAPIキーがデフォルト値のままです。")
