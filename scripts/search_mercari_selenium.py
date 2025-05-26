#!/usr/bin/env python3
"""
メルカリSelenium検索スクリプト
既存のSeleniumベースのメルカリスクレイピングコードを使用します。
"""

import sys
import json
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from collectors.mercari import MercariClient

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_mercari_selenium.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"メルカリSelenium検索開始: {keyword}, limit: {limit}", file=sys.stderr)
    
    try:
        client = MercariClient()
        
        # 出品中のアイテムを検索
        results = client.search_active_items(keyword, limit)
        
        print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
        
        # JSON形式で結果を出力（マーカー付き）
        print("JSON_START")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        print("JSON_END")
        
    except Exception as e:
        print(f"メルカリSelenium検索エラー: {str(e)}", file=sys.stderr)
        print("JSON_START")
        print("[]")
        print("JSON_END")

if __name__ == "__main__":
    main()
