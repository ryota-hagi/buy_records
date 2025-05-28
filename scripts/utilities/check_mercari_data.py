#!/usr/bin/env python
"""
Supabaseに保存されたメルカリデータを確認するスクリプト
"""

import sys
import os
import argparse
import json
from typing import List, Dict, Any

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.supabase_client import get_supabase_client

def get_mercari_data(limit: int = 10, keyword: str = None) -> List[Dict[str, Any]]:
    """
    Supabaseからメルカリデータを取得します。
    
    Args:
        limit: 取得する結果の最大数
        keyword: 検索キーワード（省略可）
        
    Returns:
        List[Dict[str, Any]]: メルカリデータのリスト
    """
    try:
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        # クエリを構築
        query = supabase.table("mercari_data").select("*").limit(limit)
        
        # キーワードでフィルタリング（指定された場合）
        if keyword:
            query = query.ilike("search_term", f"%{keyword}%")
        
        # データを取得
        response = query.execute()
        
        # レスポンスからデータを抽出
        data = response.data
        
        return data
    except Exception as e:
        print(f"Error getting mercari data: {str(e)}")
        return []

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='Check Mercari data in Supabase')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of records to fetch')
    parser.add_argument('--keyword', type=str, help='Filter by search keyword')
    parser.add_argument('--output', type=str, help='Save fetched data to JSON file')
    args = parser.parse_args()
    
    # メルカリデータを取得
    mercari_data = get_mercari_data(args.limit, args.keyword)
    
    if not mercari_data:
        print("No data found")
        return
    
    print(f"Fetched {len(mercari_data)} records from Supabase")
    
    # データの概要を表示
    active_items = [item for item in mercari_data if item.get("status") == "active"]
    sold_items = [item for item in mercari_data if item.get("status") == "sold_out"]
    
    print(f"Active items: {len(active_items)}")
    print(f"Sold items: {len(sold_items)}")
    
    # 価格の統計情報を表示
    active_prices = [item.get("price", 0) for item in active_items]
    sold_prices = [item.get("price", 0) for item in sold_items]
    
    if active_prices:
        print(f"Active items price range: {min(active_prices)} - {max(active_prices)} JPY")
        print(f"Average active price: {sum(active_prices) / len(active_prices):.2f} JPY")
    
    if sold_prices:
        print(f"Sold items price range: {min(sold_prices)} - {max(sold_prices)} JPY")
        print(f"Average sold price: {sum(sold_prices) / len(sold_prices):.2f} JPY")
    
    # 最初の数件のデータを表示
    print("\nSample data:")
    for i, item in enumerate(mercari_data[:3]):
        print(f"{i+1}. {item.get('title')} - {item.get('price')} JPY ({item.get('status')})")
        print(f"   URL: {item.get('url')}")
        print(f"   Image: {item.get('image_url')}")
        print()
    
    # データをJSONファイルに保存（オプション）
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(mercari_data, f, ensure_ascii=False, indent=2)
        print(f"Saved data to {args.output}")

if __name__ == "__main__":
    main()
