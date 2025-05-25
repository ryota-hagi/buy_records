#!/usr/bin/env python3
"""
残存APIエラー診断スクリプト
eBayAPIとMercari Apifyの現在の状況を詳細に診断します。
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

# プロジェクトルートを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_env_vars():
    """環境変数を読み込み"""
    env_vars = {}
    env_files = ['.env.local', '.env']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
    
    return env_vars

def test_ebay_api():
    """eBay APIの詳細テスト"""
    print("=" * 60)
    print("eBay API診断開始")
    print("=" * 60)
    
    env_vars = load_env_vars()
    app_id = env_vars.get('EBAY_APP_ID')
    
    if not app_id:
        print("❌ EBAY_APP_IDが設定されていません")
        return False
    
    print(f"✅ EBAY_APP_ID: {app_id[:10]}...")
    
    # Finding API テスト
    test_queries = ['Nintendo Switch', 'iPhone', 'MacBook']
    
    for query in test_queries:
        print(f"\n🔍 テストクエリ: {query}")
        
        try:
            # eBay Finding API呼び出し
            response = requests.get(
                'https://svcs.ebay.com/services/search/FindingService/v1',
                params={
                    'OPERATION-NAME': 'findItemsByKeywords',
                    'SERVICE-VERSION': '1.0.0',
                    'SECURITY-APPNAME': app_id,
                    'RESPONSE-DATA-FORMAT': 'JSON',
                    'REST-PAYLOAD': '',
                    'keywords': query,
                    'paginationInput.entriesPerPage': 5,
                    'itemFilter(0).name': 'ListingType',
                    'itemFilter(0).value': 'FixedPrice',
                    'sortOrder': 'PricePlusShippingLowest'
                },
                timeout=15
            )
            
            print(f"   ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # レスポンス構造を確認
                if 'findItemsByKeywordsResponse' in data:
                    search_result = data['findItemsByKeywordsResponse'][0].get('searchResult', [{}])[0]
                    items = search_result.get('item', [])
                    
                    print(f"   ✅ 成功: {len(items)}件の結果")
                    
                    if items:
                        # 最初のアイテムの詳細を表示
                        first_item = items[0]
                        title = first_item.get('title', [''])[0]
                        price = first_item.get('sellingStatus', [{}])[0].get('currentPrice', [{}])[0].get('__value__', 'N/A')
                        print(f"   サンプル商品: {title[:50]}...")
                        print(f"   価格: ${price}")
                    else:
                        print("   ⚠️ 検索結果が空です")
                else:
                    print(f"   ❌ 予期しないレスポンス構造: {list(data.keys())}")
                    
            else:
                print(f"   ❌ HTTPエラー: {response.status_code}")
                print(f"   レスポンス: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("   ❌ タイムアウトエラー")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ リクエストエラー: {str(e)}")
        except Exception as e:
            print(f"   ❌ 予期しないエラー: {str(e)}")
        
        time.sleep(1)  # レート制限対応
    
    return True

def test_apify_api():
    """Apify APIの詳細テスト"""
    print("\n" + "=" * 60)
    print("Apify API診断開始")
    print("=" * 60)
    
    env_vars = load_env_vars()
    api_token = env_vars.get('APIFY_API_TOKEN')
    
    if not api_token:
        print("❌ APIFY_API_TOKENが設定されていません")
        return False
    
    print(f"✅ APIFY_API_TOKEN: {api_token[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Actorリストを取得
        print("\n🔍 既存Actorリストを確認中...")
        response = requests.get(
            "https://api.apify.com/v2/acts",
            headers=headers,
            timeout=10
        )
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            actors = data.get('data', {}).get('items', [])
            
            print(f"✅ 成功: {len(actors)}個のActorが見つかりました")
            
            # Mercari関連のActorを検索
            mercari_actors = [actor for actor in actors if 'mercari' in actor.get('name', '').lower()]
            
            if mercari_actors:
                print(f"🎯 Mercari関連Actor: {len(mercari_actors)}個")
                for actor in mercari_actors:
                    print(f"   - {actor.get('name')} (ID: {actor.get('id')})")
            else:
                print("⚠️ Mercari関連Actorが見つかりません")
                
            # 一般的なActorを表示
            print("\n📋 既存Actorの例:")
            for actor in actors[:5]:
                print(f"   - {actor.get('name')} (ID: {actor.get('id')})")
                
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("❌ タイムアウトエラー")
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {str(e)}")
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")
    
    return True

def test_yahoo_api_status():
    """Yahoo!ショッピングAPIの現在の状況確認"""
    print("\n" + "=" * 60)
    print("Yahoo!ショッピングAPI状況確認")
    print("=" * 60)
    
    env_vars = load_env_vars()
    app_id = env_vars.get('YAHOO_SHOPPING_APP_ID')
    
    if not app_id:
        print("❌ YAHOO_SHOPPING_APP_IDが設定されていません")
        return False
    
    print(f"✅ YAHOO_SHOPPING_APP_ID: {app_id[:10]}...")
    
    try:
        # Yahoo!ショッピングAPI テスト
        response = requests.get(
            'https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch',
            params={
                'appid': app_id,
                'query': 'Nintendo Switch',
                'results': 5
            },
            timeout=10
        )
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get('hits', [])
            print(f"✅ 成功: {len(hits)}件の結果")
            
            if hits:
                first_item = hits[0]
                print(f"サンプル商品: {first_item.get('name', '')[:50]}...")
                print(f"価格: ¥{first_item.get('price', 'N/A')}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
    
    return True

def test_next_js_api_endpoints():
    """Next.js APIエンドポイントのテスト"""
    print("\n" + "=" * 60)
    print("Next.js APIエンドポイント診断")
    print("=" * 60)
    
    base_url = "http://localhost:3000"
    endpoints = [
        "/api/search/yahoo",
        "/api/search/ebay"
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 テスト: {endpoint}")
        
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                params={'query': 'Nintendo Switch', 'limit': 5},
                timeout=10
            )
            
            print(f"   ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    results = data.get('results', [])
                    print(f"   ✅ 成功: {len(results)}件の結果")
                else:
                    print(f"   ❌ APIエラー: {data.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTPエラー: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️ サーバーが起動していません")
        except Exception as e:
            print(f"   ❌ エラー: {str(e)}")

def main():
    """メイン診断処理"""
    print("🔍 残存APIエラー診断スクリプト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 各APIの診断を実行
    test_yahoo_api_status()
    test_ebay_api()
    test_apify_api()
    test_next_js_api_endpoints()
    
    print("\n" + "=" * 60)
    print("診断完了")
    print("=" * 60)
    print("📋 次のステップ:")
    print("1. eBayAPIエラーの詳細分析")
    print("2. Mercari Apify Actorの作成")
    print("3. 統合テストの実行")

if __name__ == "__main__":
    main()
