#!/usr/bin/env python3
"""
ラクマSelenium検索スクリプト
Seleniumを使用してラクマから商品情報を取得
"""

import sys
import os
import json

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.rakuma_selenium import RakumaSeleniumScraper

def main():
    if len(sys.argv) < 2:
        print("使用方法: python search_rakuma_selenium.py <検索キーワード> [取得数]")
        sys.exit(1)
    
    search_query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    try:
        # ラクマスクレイパーを初期化
        selenium_url = os.environ.get('SELENIUM_HUB_URL', 'http://localhost:4444')
        scraper = RakumaSeleniumScraper(selenium_url)
        
        # 検索実行
        print(f"ラクマで「{search_query}」を検索中...")
        results = scraper.search(search_query)
        
        # 結果を制限
        limited_results = results[:limit]
        
        # 結果を出力
        print(f"\n検索結果: {len(limited_results)}件")
        
        # JSON形式で出力（マーカー付き）
        print("JSON_START")
        print(json.dumps({
            "results": limited_results,
            "metadata": {
                "search_query": search_query,
                "requested_limit": limit,
                "actual_results": len(limited_results),
                "platform": "rakuma"
            },
            "method": "selenium"
        }, ensure_ascii=False, indent=2))
        print("JSON_END")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        # エラーでも空の結果を返す
        print("JSON_START")
        print(json.dumps({
            "results": [],
            "metadata": {
                "search_query": search_query,
                "requested_limit": limit,
                "actual_results": 0,
                "platform": "rakuma",
                "error": str(e)
            },
            "method": "selenium_error"
        }, ensure_ascii=False))
        print("JSON_END")
        sys.exit(1)

if __name__ == "__main__":
    main()