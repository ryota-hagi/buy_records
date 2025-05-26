#!/usr/bin/env python3
"""
統合版Mercari視覚スクレイピングスクリプト
"""
import sys
import json
import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# プロジェクトのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.visual_scraper.mercari_visual_scraper import MercariVisualScraper
from src.visual_scraper.ai_analyzer import OpenAIVisionAnalyzer

def search_mercari_visual(query: str, limit: int = 20):
    """視覚的にMercariを検索"""
    
    # OpenAI Vision APIを初期化
    ai_analyzer = OpenAIVisionAnalyzer()
    
    # 視覚スクレイパーを初期化
    scraper = MercariVisualScraper(
        ai_analyzer=ai_analyzer,
        headless=True,  # ヘッドレスモード
        save_screenshots=True  # デバッグ用にスクリーンショット保存
    )
    
    # 検索を実行
    results = scraper.search(query, limit)
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: search_mercari_visual_integrated.py <query> [limit]", file=sys.stderr)
        sys.exit(1)
    
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print("JSON_START", file=sys.stderr)
    
    try:
        results = search_mercari_visual(query, limit)
        
        # 結果を整形
        formatted_results = []
        for item in results:
            formatted_item = {
                'id': item.get('id', ''),
                'title': item.get('title', ''),
                'price': item.get('price', 0),
                'url': item.get('url', ''),
                'image_url': item.get('image_url', ''),
                'platform': 'mercari',
                'method': item.get('method', 'visual')
            }
            formatted_results.append(formatted_item)
        
        output = {
            'success': len(formatted_results) > 0,
            'results': formatted_results,
            'platform': 'mercari',
            'query': query,
            'method': 'visual_ai_scraping'
        }
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        error_output = {
            'success': False,
            'results': [],
            'error': str(e),
            'platform': 'mercari',
            'method': 'visual_ai_scraping'
        }
        print(json.dumps(error_output, ensure_ascii=False, indent=2))
    
    print("JSON_END", file=sys.stderr)

if __name__ == "__main__":
    main()