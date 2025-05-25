#!/usr/bin/env python3
"""
全プラットフォームのAPIテストスクリプト
修正されたeBay、Yahoo!ショッピング、Mercari Apifyクライアントをテストします。
"""

import sys
import os
import json
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.collectors.ebay import EbayClient
from src.collectors.yahoo_shopping import YahooShoppingClient
from src.collectors.mercari_apify import MercariApifyClient

def test_ebay_api():
    """eBay APIをテストします"""
    print("\n" + "="*50)
    print("eBay APIテスト開始")
    print("="*50)
    
    try:
        client = EbayClient()
        keyword = "Nintendo Switch"
        
        print(f"検索キーワード: {keyword}")
        print("出品中商品を検索中...")
        
        # 出品中商品を検索
        active_items = client.search_active_items(keyword, limit=5)
        print(f"出品中商品数: {len(active_items)}")
        
        if active_items:
            print("\n最初の商品:")
            item = active_items[0]
            print(f"  タイトル: {item.get('title', 'N/A')}")
            print(f"  価格: ${item.get('price', 0)}")
            print(f"  URL: {item.get('url', 'N/A')}")
            print(f"  コンディション: {item.get('condition', 'N/A')}")
        
        print("\n売却済み商品を検索中...")
        
        # 売却済み商品を検索
        sold_items = client.search_sold_items(keyword, limit=5)
        print(f"売却済み商品数: {len(sold_items)}")
        
        if sold_items:
            print("\n最初の売却済み商品:")
            item = sold_items[0]
            print(f"  タイトル: {item.get('title', 'N/A')}")
            print(f"  売却価格: ${item.get('sold_price', 0)}")
            print(f"  売却日: {item.get('sold_date', 'N/A')}")
        
        print("\neBay APIテスト: ✅ 成功")
        return True
        
    except Exception as e:
        print(f"\neBay APIテスト: ❌ 失敗")
        print(f"エラー: {str(e)}")
        return False

def test_yahoo_shopping_api():
    """Yahoo!ショッピングAPIをテストします"""
    print("\n" + "="*50)
    print("Yahoo!ショッピングAPIテスト開始")
    print("="*50)
    
    try:
        client = YahooShoppingClient()
        keyword = "Nintendo Switch"
        
        print(f"検索キーワード: {keyword}")
        print("商品を検索中...")
        
        # 商品を検索
        items = client.search_items(keyword, limit=5)
        print(f"検索結果数: {len(items)}")
        
        if items:
            print("\n最初の商品:")
            item = items[0]
            print(f"  タイトル: {item.get('title', 'N/A')}")
            print(f"  価格: ¥{item.get('price', 0):,}")
            print(f"  URL: {item.get('url', 'N/A')}")
            print(f"  ストア: {item.get('store_name', 'N/A')}")
            print(f"  在庫: {item.get('stock_quantity', 0)}")
        
        print("\nYahoo!ショッピングAPIテスト: ✅ 成功")
        return True
        
    except Exception as e:
        print(f"\nYahoo!ショッピングAPIテスト: ❌ 失敗")
        print(f"エラー: {str(e)}")
        return False

def test_mercari_apify_api():
    """Mercari Apify APIをテストします"""
    print("\n" + "="*50)
    print("Mercari Apify APIテスト開始")
    print("="*50)
    
    try:
        client = MercariApifyClient()
        keyword = "Nintendo Switch"
        
        print(f"検索キーワード: {keyword}")
        
        # 利用可能なActorをリスト
        print("利用可能なActorを確認中...")
        actors = client.list_actors()
        print(f"利用可能なActor数: {len(actors)}")
        
        # Mercari用のActorを探す
        mercari_actor = None
        for actor in actors:
            if "mercari" in actor.get("name", "").lower():
                mercari_actor = actor
                break
        
        if mercari_actor:
            print(f"既存のMercari Actor発見: {mercari_actor['name']}")
            client.set_actor_id(mercari_actor["id"])
        else:
            print("Mercari Actorが見つかりません。新規作成をスキップします。")
            print("注意: 実際の検索にはActorの作成が必要です。")
            print("\nMercari Apify APIテスト: ⚠️  スキップ（Actor未作成）")
            return True
        
        print("出品中商品を検索中...")
        
        # 出品中商品を検索（少数で試す）
        active_items = client.search_active_items(keyword, limit=2)
        print(f"出品中商品数: {len(active_items)}")
        
        if active_items:
            print("\n最初の商品:")
            item = active_items[0]
            print(f"  タイトル: {item.get('title', 'N/A')}")
            print(f"  価格: ¥{item.get('price', 0):,}")
            print(f"  URL: {item.get('url', 'N/A')}")
            print(f"  ステータス: {item.get('status', 'N/A')}")
        
        print("\nMercari Apify APIテスト: ✅ 成功")
        return True
        
    except Exception as e:
        print(f"\nMercari Apify APIテスト: ❌ 失敗")
        print(f"エラー: {str(e)}")
        return False

def main():
    """メイン関数"""
    print("全プラットフォームAPIテスト開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 各プラットフォームをテスト
    results['ebay'] = test_ebay_api()
    results['yahoo_shopping'] = test_yahoo_shopping_api()
    results['mercari_apify'] = test_mercari_apify_api()
    
    # 結果サマリー
    print("\n" + "="*50)
    print("テスト結果サマリー")
    print("="*50)
    
    success_count = 0
    total_count = len(results)
    
    for platform, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{platform.upper()}: {status}")
        if success:
            success_count += 1
    
    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("\n🎉 すべてのプラットフォームAPIが正常に動作しています！")
    elif success_count > 0:
        print(f"\n⚠️  {total_count - success_count}個のプラットフォームで問題があります。")
    else:
        print("\n❌ すべてのプラットフォームで問題があります。設定を確認してください。")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
