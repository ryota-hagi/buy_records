#!/usr/bin/env python3
"""
ExchangeRate-API機能のテストスクリプト
為替レート取得機能の動作確認を行います。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.exchange_rate import get_exchange_rate_client, get_usd_to_jpy_rate
import json

def test_exchange_rate_api():
    """ExchangeRate-API機能をテストします"""
    
    print("=== ExchangeRate-API テスト ===")
    print()
    
    # クライアントを取得
    client = get_exchange_rate_client()
    
    # キャッシュ情報を表示
    print("1. キャッシュ情報の確認:")
    cache_info = client.get_cache_info()
    print(json.dumps(cache_info, indent=2, ensure_ascii=False))
    print()
    
    # 為替レートを取得
    print("2. 為替レート取得テスト:")
    try:
        rate = get_usd_to_jpy_rate()
        print(f"USD to JPY レート: {rate}")
        print(f"例: $100 = ¥{int(100 * rate)}")
        print()
    except Exception as e:
        print(f"エラー: {e}")
        print()
    
    # キャッシュ情報を再確認
    print("3. 取得後のキャッシュ情報:")
    cache_info = client.get_cache_info()
    print(json.dumps(cache_info, indent=2, ensure_ascii=False))
    print()
    
    # 複数回取得してキャッシュが機能することを確認
    print("4. キャッシュ機能テスト（2回目の取得）:")
    try:
        rate2 = get_usd_to_jpy_rate()
        print(f"USD to JPY レート（2回目）: {rate2}")
        print("キャッシュから取得されました" if rate == rate2 else "新しいレートが取得されました")
        print()
    except Exception as e:
        print(f"エラー: {e}")
        print()
    
    # 価格変換のテスト
    print("5. 価格変換テスト:")
    test_prices = [10.99, 25.50, 99.99, 199.00]
    for usd_price in test_prices:
        try:
            jpy_price = int(usd_price * rate)
            print(f"${usd_price} → ¥{jpy_price}")
        except Exception as e:
            print(f"${usd_price} の変換でエラー: {e}")
    print()

def test_cache_operations():
    """キャッシュ操作のテスト"""
    
    print("=== キャッシュ操作テスト ===")
    print()
    
    client = get_exchange_rate_client()
    
    # キャッシュクリア前の状態
    print("1. キャッシュクリア前:")
    cache_info = client.get_cache_info()
    print(f"キャッシュ存在: {cache_info.get('exists', False)}")
    print()
    
    # キャッシュをクリア
    print("2. キャッシュクリア実行:")
    client.clear_cache()
    print("キャッシュをクリアしました")
    print()
    
    # キャッシュクリア後の状態
    print("3. キャッシュクリア後:")
    cache_info = client.get_cache_info()
    print(f"キャッシュ存在: {cache_info.get('exists', False)}")
    print()
    
    # 新しいレートを取得
    print("4. 新しいレート取得:")
    try:
        rate = get_usd_to_jpy_rate()
        print(f"新しく取得したレート: {rate}")
        print()
    except Exception as e:
        print(f"エラー: {e}")
        print()
    
    # 新しいキャッシュの確認
    print("5. 新しいキャッシュ情報:")
    cache_info = client.get_cache_info()
    print(json.dumps(cache_info, indent=2, ensure_ascii=False))
    print()

def main():
    """メイン関数"""
    
    print("ExchangeRate-API テストスクリプト")
    print("=" * 50)
    print()
    
    try:
        # 基本的な機能テスト
        test_exchange_rate_api()
        
        # キャッシュ操作テスト
        test_cache_operations()
        
        print("=" * 50)
        print("テスト完了")
        
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
