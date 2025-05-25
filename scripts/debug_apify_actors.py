#!/usr/bin/env python3
"""
Apify Actorの調査とデバッグスクリプト
利用可能なMercari関連Actorを検索し、代替案を提案
"""

import requests
import json
import os
import sys

def check_apify_token():
    """Apify APIトークンの確認"""
    token = os.getenv('APIFY_API_TOKEN')
    if not token:
        print("❌ APIFY_API_TOKENが設定されていません")
        return None
    
    print(f"✅ APIFY_API_TOKEN: {token[:20]}...")
    return token

def search_mercari_actors(token):
    """Mercari関連のActorを検索"""
    print("\n=== Mercari関連Actorの検索 ===")
    
    try:
        # Apify Storeで検索
        search_url = "https://api.apify.com/v2/store"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Mercariで検索
        params = {
            "search": "mercari",
            "limit": 20
        }
        
        response = requests.get(search_url, headers=headers, params=params)
        print(f"検索リクエスト: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            actors = data.get("data", {}).get("items", [])
            
            print(f"見つかったActor数: {len(actors)}")
            
            for actor in actors:
                print(f"\n📦 Actor: {actor.get('username', 'N/A')}/{actor.get('name', 'N/A')}")
                print(f"   タイトル: {actor.get('title', 'N/A')}")
                print(f"   説明: {actor.get('description', 'N/A')[:100]}...")
                print(f"   最終更新: {actor.get('modifiedAt', 'N/A')}")
                print(f"   実行回数: {actor.get('stats', {}).get('totalRuns', 0)}")
        else:
            print(f"検索エラー: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"検索中にエラー: {str(e)}")

def test_specific_actor(token, actor_id):
    """特定のActorの存在確認"""
    print(f"\n=== Actor存在確認: {actor_id} ===")
    
    try:
        url = f"https://api.apify.com/v2/acts/{actor_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()["data"]
            print(f"✅ Actor存在: {data.get('name')}")
            print(f"   タイトル: {data.get('title')}")
            print(f"   説明: {data.get('description', '')[:100]}...")
            return True
        elif response.status_code == 404:
            print(f"❌ Actor不存在: {actor_id}")
            return False
        else:
            print(f"⚠️  エラー: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"確認中にエラー: {str(e)}")
        return False

def search_web_scraping_actors(token):
    """一般的なWebスクレイピングActorを検索"""
    print("\n=== Webスクレイピング関連Actorの検索 ===")
    
    search_terms = ["web-scraper", "scraper", "puppeteer", "playwright"]
    
    for term in search_terms:
        try:
            search_url = "https://api.apify.com/v2/store"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "search": term,
                "limit": 5
            }
            
            response = requests.get(search_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                actors = data.get("data", {}).get("items", [])
                
                print(f"\n🔍 '{term}'の検索結果: {len(actors)}件")
                
                for actor in actors[:3]:  # 上位3件のみ表示
                    print(f"   📦 {actor.get('username', 'N/A')}/{actor.get('name', 'N/A')}")
                    print(f"      実行回数: {actor.get('stats', {}).get('totalRuns', 0)}")
                    
        except Exception as e:
            print(f"'{term}'検索中にエラー: {str(e)}")

def check_account_info(token):
    """アカウント情報の確認"""
    print("\n=== Apifyアカウント情報 ===")
    
    try:
        url = "https://api.apify.com/v2/users/me"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()["data"]
            print(f"✅ ユーザー: {data.get('username', 'N/A')}")
            print(f"   プラン: {data.get('plan', 'N/A')}")
            print(f"   月間実行数: {data.get('usageStats', {}).get('monthlyActorComputeUnits', 0)}")
        else:
            print(f"❌ アカウント情報取得エラー: {response.status_code}")
            
    except Exception as e:
        print(f"アカウント情報確認中にエラー: {str(e)}")

def main():
    print("🔍 Apify Actor調査とデバッグを開始します...")
    
    # APIトークン確認
    token = check_apify_token()
    if not token:
        sys.exit(1)
    
    # アカウント情報確認
    check_account_info(token)
    
    # 問題のActorの存在確認
    test_specific_actor(token, "apify/mercari-scraper")
    
    # Mercari関連Actorの検索
    search_mercari_actors(token)
    
    # 一般的なWebスクレイピングActorの検索
    search_web_scraping_actors(token)
    
    print("\n=== 推奨事項 ===")
    print("1. 'apify/mercari-scraper'は存在しないため、代替Actorを使用する")
    print("2. カスタムActorを作成する（src/collectors/mercari_apify.pyの実装を使用）")
    print("3. 直接スクレイピング機能を改善する")

if __name__ == "__main__":
    main()
