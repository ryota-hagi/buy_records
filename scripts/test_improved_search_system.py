#!/usr/bin/env python3
"""
改良された検索システムのテスト
- 各プラットフォームから20個ずつ取得
- ExchangeRate-API統合
- 最終的に20個のリストに統合
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.jan.search_engine import JANSearchEngine
from src.utils.exchange_rate import get_usd_to_jpy_rate
import json
from datetime import datetime

def test_improved_search_system():
    """改良された検索システムのテスト"""
    print("=" * 60)
    print("改良された検索システム動作確認テスト")
    print("=" * 60)
    
    # テスト用JANコード
    jan_code = "4902370548501"  # Nintendo Switch
    
    print(f"\n=== JANコード: {jan_code} ===")
    
    # 1. 為替レート確認
    print("\n1. 為替レート確認:")
    try:
        rate = get_usd_to_jpy_rate()
        print(f"   現在のUSD to JPYレート: {rate}")
    except Exception as e:
        print(f"   為替レート取得エラー: {e}")
    
    # 2. 検索エンジン初期化
    print("\n2. 検索エンジン初期化:")
    try:
        engine = JANSearchEngine()
        print(f"   利用可能プラットフォーム: {engine.get_available_platforms()}")
        print(f"   デフォルト検索対象: {engine.default_platforms}")
    except Exception as e:
        print(f"   初期化エラー: {e}")
        return
    
    # 3. 検索実行
    print("\n3. 検索実行（各プラットフォームから20個ずつ取得）:")
    try:
        results = engine.search_by_jan(jan_code, limit=20)
        print(f"   最終結果件数: {len(results)}件")
        
        if results:
            # プラットフォーム別集計
            platform_counts = {}
            for result in results:
                platform = result.get('platform', 'Unknown')
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            print(f"   プラットフォーム別内訳: {platform_counts}")
            
            # 価格範囲
            prices = [r['total_price'] for r in results if r['total_price'] > 0]
            if prices:
                print(f"   価格範囲: ¥{min(prices):,} - ¥{max(prices):,}")
                print(f"   平均価格: ¥{sum(prices) // len(prices):,}")
        
    except Exception as e:
        print(f"   検索エラー: {e}")
        return
    
    # 4. 結果詳細表示
    print("\n4. 検索結果詳細（TOP20）:")
    print("-" * 80)
    print(f"{'順位':<4} {'プラットフォーム':<15} {'価格':<10} {'商品名':<40}")
    print("-" * 80)
    
    for i, item in enumerate(results[:20], 1):
        platform = item.get('platform', '')[:14]
        price = f"¥{item.get('total_price', 0):,}"
        title = item.get('item_title', '')[:39]
        print(f"{i:<4} {platform:<15} {price:<10} {title:<40}")
    
    # 5. eBay価格変換確認
    print("\n5. eBay価格変換確認:")
    ebay_items = [r for r in results if r.get('platform') == 'eBay']
    if ebay_items:
        print(f"   eBay商品数: {len(ebay_items)}件")
        for item in ebay_items[:3]:
            print(f"   - {item.get('item_title', '')[:50]}")
            print(f"     価格: ¥{item.get('total_price', 0):,} (ExchangeRate-API使用)")
    else:
        print("   eBay商品なし")
    
    # 6. 統計情報
    print("\n6. 統計情報:")
    summary = engine.get_search_summary(results)
    print(f"   総件数: {summary['total_count']}件")
    print(f"   最安値: ¥{summary['lowest_price']:,}")
    print(f"   最高値: ¥{summary['highest_price']:,}")
    print(f"   平均価格: ¥{summary['average_price']:,}")
    print(f"   中央値: ¥{summary['median_price']:,}")
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    test_improved_search_system()
