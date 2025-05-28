#!/usr/bin/env python3
"""
eBay Token設定のデバッグスクリプト
"""

import sys
import os
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.config import get_config

def debug_ebay_config():
    """eBay設定をデバッグします"""
    print("eBay設定デバッグ")
    print("="*50)
    
    # 各設定値を確認
    app_id = get_config("EBAY_APP_ID", required=False)
    cert_id = get_config("EBAY_CERT_ID", required=False)
    client_secret = get_config("EBAY_CLIENT_SECRET", required=False)
    user_token = get_config("EBAY_USER_TOKEN", required=False)
    token_expiry = get_config("EBAY_TOKEN_EXPIRY", required=False)
    environment = get_config("EBAY_ENVIRONMENT", required=False)
    
    print(f"EBAY_APP_ID: {'設定済み' if app_id else '未設定'}")
    if app_id:
        print(f"  値: {app_id[:10]}...")
    
    print(f"EBAY_CERT_ID: {'設定済み' if cert_id else '未設定'}")
    if cert_id:
        print(f"  値: {cert_id[:10]}...")
    
    print(f"EBAY_CLIENT_SECRET: {'設定済み' if client_secret else '未設定'}")
    if client_secret:
        print(f"  値: {client_secret[:10]}...")
    
    print(f"EBAY_USER_TOKEN: {'設定済み' if user_token else '未設定'}")
    if user_token:
        print(f"  値: {user_token[:20]}...")
        print(f"  長さ: {len(user_token)} 文字")
    
    print(f"EBAY_TOKEN_EXPIRY: {'設定済み' if token_expiry else '未設定'}")
    if token_expiry:
        print(f"  値: {token_expiry}")
        try:
            expiry_date = datetime.fromisoformat(token_expiry.replace('Z', '+00:00'))
            now = datetime.now(expiry_date.tzinfo)
            is_valid = now < expiry_date
            print(f"  有効期限: {expiry_date}")
            print(f"  現在時刻: {now}")
            print(f"  有効: {'はい' if is_valid else 'いいえ'}")
        except Exception as e:
            print(f"  エラー: 日付解析失敗 - {e}")
    
    print(f"EBAY_ENVIRONMENT: {environment or 'SANDBOX (デフォルト)'}")
    
    # 必要な設定が揃っているかチェック
    print("\n設定チェック:")
    if app_id and cert_id and client_secret:
        print("✅ Client Credentials認証に必要な設定が揃っています")
    else:
        print("❌ Client Credentials認証に必要な設定が不足しています")
    
    if user_token:
        print("✅ User Tokenが設定されています")
        if token_expiry:
            try:
                expiry_date = datetime.fromisoformat(token_expiry.replace('Z', '+00:00'))
                now = datetime.now(expiry_date.tzinfo)
                if now < expiry_date:
                    print("✅ User Tokenは有効です")
                else:
                    print("⚠️  User Tokenの有効期限が切れています")
            except:
                print("⚠️  User Tokenの有効期限の形式が不正です")
        else:
            print("⚠️  User Tokenの有効期限が設定されていません")
    else:
        print("❌ User Tokenが設定されていません")

def test_ebay_client():
    """eBayクライアントの初期化をテストします"""
    print("\neBayクライアント初期化テスト")
    print("="*50)
    
    try:
        from src.collectors.ebay import EbayClient
        client = EbayClient()
        
        print(f"App ID: {'設定済み' if client.app_id else '未設定'}")
        print(f"Cert ID: {'設定済み' if client.cert_id else '未設定'}")
        print(f"Client Secret: {'設定済み' if client.client_secret else '未設定'}")
        print(f"User Token: {'設定済み' if client.user_token else '未設定'}")
        print(f"Token Expiry: {'設定済み' if client.token_expiry else '未設定'}")
        print(f"Environment: {client.environment}")
        
        # トークン取得テスト
        print("\nトークン取得テスト:")
        try:
            token = client._get_access_token()
            print(f"✅ トークン取得成功: {token[:20]}...")
        except Exception as e:
            print(f"❌ トークン取得失敗: {str(e)}")
        
    except Exception as e:
        print(f"❌ クライアント初期化失敗: {str(e)}")

if __name__ == "__main__":
    debug_ebay_config()
    test_ebay_client()
