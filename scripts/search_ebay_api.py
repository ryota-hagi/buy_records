#!/usr/bin/env python3
"""
eBay API検索スクリプト
JANコードでeBay APIから商品を検索し、JSON形式で結果を出力します。
"""

import sys
import json
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.ebay import EbayClient

def search_ebay_by_jan(jan_code, limit=10):
    """
    JANコードでeBay APIから商品を検索
    
    Args:
        jan_code: JANコード
        limit: 取得する商品数の上限
        
    Returns:
        List[Dict]: 商品データのリスト
    """
    try:
        client = EbayClient()
        
        # JANコードで検索
        results = client.search_active_items(jan_code, limit)
        
        # データを統一フォーマットに変換
        formatted_results = []
        for item in results:
            formatted_item = {
                "title": item.get("title", ""),
                "name": item.get("name", ""),
                "price": item.get("price", 0),
                "url": item.get("url", ""),
                "image_url": item.get("image_url", ""),
                "condition": item.get("condition", ""),
                "seller": item.get("seller", ""),
                "currency": item.get("currency", "USD")
            }
            formatted_results.append(formatted_item)
        
        return formatted_results
        
    except Exception as e:
        print(f"Error in eBay search: {str(e)}", file=sys.stderr)
        return []

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_ebay_api.py <jan_code> [limit]", file=sys.stderr)
        sys.exit(1)
    
    jan_code = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    print(f"Searching eBay for JAN code: {jan_code}, limit: {limit}", file=sys.stderr)
    
    results = search_ebay_by_jan(jan_code, limit)
    
    print(f"Found {len(results)} items from eBay", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()
