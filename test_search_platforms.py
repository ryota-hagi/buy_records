#!/usr/bin/env python3
"""各プラットフォームの検索機能をテスト"""

import asyncio
import json
import os
import sys
from datetime import datetime

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.collectors.yahoo_shopping import YahooShoppingClient
from src.collectors.mercari_simple import MercariClient
from src.collectors.ebay import EbayClient

async def test_yahoo():
    """Yahoo!ショッピングの検索テスト"""
    print("\n=== Yahoo!ショッピング検索テスト ===")
    try:
        collector = YahooShoppingClient()
        results = await collector.search_by_jan("4988006763173")
        print(f"結果数: {len(results)}")
        if results:
            print(f"最初の商品: {results[0].get('title', 'タイトルなし')}")
            print(f"価格: {results[0].get('price', '価格なし')}")
        return len(results) > 0
    except Exception as e:
        print(f"エラー: {str(e)}")
        return False

async def test_mercari():
    """メルカリの検索テスト"""
    print("\n=== メルカリ検索テスト ===")
    try:
        collector = MercariClient()
        results = await collector.search("4988006763173")
        print(f"結果数: {len(results)}")
        if results:
            print(f"最初の商品: {results[0].get('title', 'タイトルなし')}")
            print(f"価格: {results[0].get('price', '価格なし')}")
        return len(results) > 0
    except Exception as e:
        print(f"エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_ebay():
    """eBayの検索テスト"""
    print("\n=== eBay検索テスト ===")
    try:
        collector = EbayClient()
        results = await collector.search_by_keyword("4988006763173")
        print(f"結果数: {len(results)}")
        if results:
            print(f"最初の商品: {results[0].get('title', 'タイトルなし')}")
            print(f"価格: {results[0].get('price', '価格なし')}")
        return len(results) > 0
    except Exception as e:
        print(f"エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メインテスト関数"""
    print(f"テスト開始: {datetime.now()}")
    
    # 環境変数の確認
    print("\n=== 環境変数確認 ===")
    print(f"YAHOO_SHOPPING_APP_ID: {'設定済み' if os.getenv('YAHOO_SHOPPING_APP_ID') else '未設定'}")
    print(f"EBAY_APP_ID: {'設定済み' if os.getenv('EBAY_APP_ID') else '未設定'}")
    print(f"GOOGLE_TRANSLATE_API_KEY: {'設定済み' if os.getenv('GOOGLE_TRANSLATE_API_KEY') and os.getenv('GOOGLE_TRANSLATE_API_KEY') != 'your_google_translate_api_key_here' else '未設定'}")
    print(f"OPENAI_API_KEY: {'設定済み' if os.getenv('OPENAI_API_KEY') else '未設定'}")
    
    # 各プラットフォームのテスト
    results = {
        'yahoo': await test_yahoo(),
        'mercari': await test_mercari(),
        'ebay': await test_ebay()
    }
    
    print("\n=== テスト結果まとめ ===")
    for platform, success in results.items():
        print(f"{platform}: {'✅ 成功' if success else '❌ 失敗'}")
    
    print(f"\nテスト完了: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())