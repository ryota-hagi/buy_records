#!/usr/bin/env python3
"""
Google Cloud Translation API翻訳機能のテストスクリプト
"""

import sys
import os
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.utils.translator import translator, translate_for_platform

# 環境変数を読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_google_translator():
    """Google Cloud Translation API翻訳機能をテストします"""
    print("\n=== Google Cloud Translation API翻訳機能テスト ===")
    
    # テストケース
    test_cases = [
        "テスト商品A",
        "テスト商品B 500ml",
        "Nintendo Switch",  # 英語テキスト
        "123456789",  # 数字のみ
    ]
    
    print("\n--- 基本翻訳テスト ---")
    for product_name in test_cases:
        try:
            translated = translator.translate_product_name(product_name)
            is_japanese = translator.is_japanese_text(product_name)
            print(f"日本語: {product_name}")
            print(f"英語: {translated}")
            print(f"日本語テキスト: {is_japanese}")
            print("-" * 50)
        except Exception as e:
            print(f"エラー: {product_name} -> {e}")
            print("-" * 50)
    
    print("\n--- プラットフォーム別翻訳テスト ---")
    test_product = "テスト商品A"
    platforms = ['ebay', 'discogs', 'mercari', 'yahoo_shopping']
    
    for platform in platforms:
        try:
            query = translate_for_platform(test_product, platform)
            print(f"{platform}: {query}")
        except Exception as e:
            print(f"{platform}: エラー - {e}")
    
    print("\n--- 翻訳クライアント状態確認 ---")
    if translator.client:
        print("✅ Google Cloud Translation APIクライアントが正常に初期化されています")
    else:
        print("❌ Google Cloud Translation APIクライアントの初期化に失敗しています")
        print("環境変数GOOGLE_CLOUD_CREDENTIALS_JSONを確認してください")

if __name__ == "__main__":
    test_google_translator()
