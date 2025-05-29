#!/usr/bin/env python3
"""楽天APIのテストスクリプト"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_rakuten_api():
    """楽天APIを直接テスト"""
    app_id = os.getenv('RAKUTEN_APP_ID')
    if not app_id:
        print("❌ 楽天APIキーが設定されていません")
        return
    
    # テスト検索
    base_url = 'https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601'
    params = {
        'applicationId': app_id,
        'keyword': 'Nintendo Switch',
        'hits': '5',
        'sort': '+itemPrice',
        'imageFlag': '1',
        'availability': '1',
        'formatVersion': '2'
    }
    
    print("🔍 楽天API検索テスト開始...")
    print(f"検索キーワード: {params['keyword']}")
    
    try:
        response = requests.get(base_url, params=params)
        print(f"ステータスコード: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"✅ 検索成功: {data.get('hits', 0)}件のヒット")
            
            # 最初のアイテムの構造を確認
            if data.get('Items') and len(data['Items']) > 0:
                first_item = data['Items'][0]
                print("\n📦 最初のアイテムの構造:")
                print(json.dumps(first_item, indent=2, ensure_ascii=False))
                
                # アイテムプロパティの確認（直接アクセス）
                print("\n🔍 アイテムプロパティの確認:")
                for key in ['itemName', 'itemPrice', 'itemUrl', 'mediumImageUrls']:
                    if key in first_item:
                        value = first_item.get(key)
                        if isinstance(value, str):
                            print(f"  ✅ {key}: 存在 (値: {value[:50]}...)")
                        else:
                            print(f"  ✅ {key}: 存在 (値: {value})")
                    else:
                        print(f"  ❌ {key}: 存在しない")
            else:
                print("❌ 検索結果が0件です")
                
        else:
            print(f"❌ APIエラー: {response.status_code}")
            print(f"エラー内容: {response.text}")
            
    except Exception as e:
        print(f"❌ エラー発生: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rakuten_api()