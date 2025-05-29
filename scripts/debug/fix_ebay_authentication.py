#!/usr/bin/env python3
"""
eBay API認証の修正と検証スクリプト
"""
import os
import sys
import base64
import requests
from datetime import datetime, timedelta

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.config import get_config

def test_ebay_authentication():
    """eBay API認証をテストし、必要に応じて修正"""
    print("=== eBay API Authentication Fix ===\n")
    
    # 設定読み込み
    app_id = get_config("EBAY_APP_ID")
    cert_id = get_config("EBAY_CERT_ID")
    client_secret = get_config("EBAY_CLIENT_SECRET")
    user_token = get_config("EBAY_USER_TOKEN", required=False)
    environment = get_config("EBAY_ENVIRONMENT", "PRODUCTION")
    
    if not app_id or not client_secret:
        print("❌ eBay API credentials not found in .env")
        return False
    
    print(f"✅ App ID: {app_id[:10]}...")
    print(f"✅ Environment: {environment}")
    
    # エンドポイント設定
    if environment == "PRODUCTION":
        auth_url = "https://api.ebay.com/identity/v1/oauth2/token"
        api_url = "https://api.ebay.com"
    else:
        auth_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        api_url = "https://api.sandbox.ebay.com"
    
    # Client Credentials フローでトークン取得
    print("\n📍 Testing Client Credentials flow...")
    
    credentials = f"{app_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    payload = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }
    
    try:
        response = requests.post(auth_url, headers=headers, data=payload)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            expires_in = token_data["expires_in"]
            
            print(f"✅ Successfully obtained access token")
            print(f"   - Token: {access_token[:20]}...")
            print(f"   - Expires in: {expires_in} seconds ({expires_in // 3600} hours)")
            
            # トークンをテスト
            print("\n📍 Testing token with Browse API...")
            test_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
            }
            
            test_url = f"{api_url}/buy/browse/v1/item_summary/search"
            test_params = {
                "q": "test",
                "limit": 1
            }
            
            test_response = requests.get(test_url, headers=test_headers, params=test_params)
            
            if test_response.status_code == 200:
                print("✅ Token is valid and working!")
                print(f"   - Response: {test_response.json().get('total', 'N/A')} items found")
                return True
            else:
                print(f"❌ Token test failed: {test_response.status_code}")
                print(f"   - Error: {test_response.text}")
                return False
                
        else:
            print(f"❌ Failed to get access token: {response.status_code}")
            print(f"   - Error: {response.text}")
            
            # 詳細なエラー情報
            if response.status_code == 401:
                print("\n⚠️  Authentication failed. Please check:")
                print("   1. EBAY_APP_ID is correct")
                print("   2. EBAY_CLIENT_SECRET is correct")
                print("   3. App is registered for the correct environment")
            
            return False
            
    except Exception as e:
        print(f"❌ Error during authentication: {str(e)}")
        return False

def update_env_file():
    """必要に応じて.envファイルを更新"""
    print("\n📍 Checking .env configuration...")
    
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        
        # EBAY_TOKEN_EXPIRYをコメントアウト（Client Credentialsフローでは不要）
        if 'EBAY_TOKEN_EXPIRY=' in content and not content.strip().startswith('#'):
            print("⚠️  Found EBAY_TOKEN_EXPIRY in .env - commenting out (not needed for Client Credentials)")
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.strip().startswith('EBAY_TOKEN_EXPIRY='):
                    new_lines.append(f"# {line}")
                else:
                    new_lines.append(line)
            
            with open(env_path, 'w') as f:
                f.write('\n'.join(new_lines))
            print("✅ Updated .env file")

if __name__ == "__main__":
    # 認証テスト
    success = test_ebay_authentication()
    
    if success:
        print("\n✅ eBay authentication is working correctly!")
        update_env_file()
    else:
        print("\n❌ eBay authentication needs attention")
        print("\nRecommended actions:")
        print("1. Verify EBAY_APP_ID and EBAY_CLIENT_SECRET in .env")
        print("2. Check if app is registered for PRODUCTION environment")
        print("3. Ensure app has necessary scopes enabled")