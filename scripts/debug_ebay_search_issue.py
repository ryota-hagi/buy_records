#!/usr/bin/env python3
"""
eBay検索問題のデバッグスクリプト
"""

import sys
import os
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.jan.jan_lookup import get_product_name_from_jan
from src.utils.translator import translator
from src.collectors.ebay import EbayClient

# 環境変数を読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_ebay_search():
    """eBay検索の問題をデバッグします"""
    print("\n=== eBay検索問題デバッグ ===")
    
    jan_code = '4549995433937'
    print(f'JANコード: {jan_code}')
    
    # 1. JANコードから商品名を取得
    try:
        product_name = get_product_name_from_jan(jan_code)
        print(f'商品名: {product_name}')
        
        if not product_name:
            print('❌ JANコードから商品名を取得できませんでした')
            return
            
    except Exception as e:
        print(f'❌ JANコード検索エラー: {e}')
        return
    
    # 2. 商品名を英語に翻訳
    try:
        english_name = translator.translate_product_name(product_name)
        print(f'英語翻訳: {english_name}')
        
        if not english_name or english_name == product_name:
            print('❌ 翻訳が正常に動作していません')
            return
            
    except Exception as e:
        print(f'❌ 翻訳エラー: {e}')
        return
    
    # 3. eBayクライアントの初期化
    try:
        ebay_client = EbayClient()
        print(f'✅ eBayクライアント初期化: 成功')
        
        # eBayクライアントの設定確認
        print(f'eBay API設定確認:')
        print(f'  - Base URL: {getattr(ebay_client, "base_url", "未設定")}')
        print(f'  - API Key: {"設定済み" if getattr(ebay_client, "api_key", None) else "未設定"}')
        
    except Exception as e:
        print(f'❌ eBayクライアント初期化エラー: {e}')
        import traceback
        traceback.print_exc()
        return
    
    # 4. eBay検索実行
    try:
        print(f'\n--- eBay検索実行 ---')
        print(f'検索クエリ: {english_name}')
        
        results = ebay_client.search_active_items(english_name, 5)
        print(f'✅ eBay検索結果: {len(results)}件')
        
        if len(results) == 0:
            print('⚠️  検索結果が0件です')
            
            # より一般的なクエリで再検索
            simple_query = "AirPods Pro"
            print(f'\n--- 簡単なクエリで再検索 ---')
            print(f'検索クエリ: {simple_query}')
            
            simple_results = ebay_client.search_active_items(simple_query, 5)
            print(f'簡単なクエリの検索結果: {len(simple_results)}件')
            
            if len(simple_results) > 0:
                print('✅ eBay APIは動作しています。翻訳されたクエリに問題がある可能性があります')
                for i, item in enumerate(simple_results[:3]):
                    print(f'  {i+1}. {item.get("title", "タイトルなし")}')
            else:
                print('❌ eBay API自体に問題がある可能性があります')
        else:
            print('✅ 検索成功！')
            for i, item in enumerate(results[:3]):
                print(f'  {i+1}. {item.get("title", "タイトルなし")}')
                
    except Exception as e:
        print(f'❌ eBay検索エラー: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ebay_search()
