#!/usr/bin/env python3
"""
メルカリシンプルスクレイピング検索スクリプト
requestsとBeautifulSoupを使用してメルカリから商品データを取得します。
"""

import sys
import json
import requests
import time
import re
from urllib.parse import quote
from typing import List, Dict, Any
import random
from datetime import datetime

class MercariSimpleScrapingClient:
    """シンプルなメルカリスクレイピングクライアント"""
    
    def __init__(self):
        self.base_url = "https://jp.mercari.com"
        
        # 実際のブラウザのヘッダーを模倣
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        })
    
    def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        メルカリから商品データを検索
        """
        try:
            print(f"メルカリシンプルスクレイピング開始: {keyword}", file=sys.stderr)
            
            # ランダムなユーザーエージェントを選択
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # 検索URL
            search_url = f"{self.base_url}/search?keyword={quote(keyword)}&status=on_sale&sort=price&order=asc"
            
            print(f"検索URL: {search_url}", file=sys.stderr)
            
            # リクエスト前に少し待機
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(search_url, timeout=300)
            
            if response.status_code != 200:
                print(f"HTTPエラー: {response.status_code}", file=sys.stderr)
                return []
            
            print(f"レスポンス取得成功: {len(response.text)} bytes", file=sys.stderr)
            
            # HTMLから商品データを抽出
            items = self._extract_items_from_html(response.text, keyword, limit)
            
            if not items:
                print("商品データが見つかりませんでした", file=sys.stderr)
                # デバッグ用: HTMLの一部を出力
                print(f"HTML冒頭: {response.text[:500]}", file=sys.stderr)
            
            return items
            
        except Exception as e:
            print(f"検索エラー: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_items_from_html(self, html: str, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """HTMLから商品データを抽出"""
        items = []
        
        try:
            # Next.jsのデータを探す
            data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
            
            if data_match:
                print("Next.jsデータを発見", file=sys.stderr)
                json_str = data_match.group(1)
                
                try:
                    data = json.loads(json_str)
                    
                    # 商品データを探す
                    items_data = self._find_items_in_json(data)
                    
                    if items_data:
                        print(f"商品データ発見: {len(items_data)}件", file=sys.stderr)
                        
                        for idx, item_data in enumerate(items_data[:limit]):
                            try:
                                # 商品情報を抽出
                                item_id = item_data.get('id', '')
                                title = item_data.get('name', '') or item_data.get('itemName', '')
                                price = item_data.get('price', 0)
                                thumbnail = item_data.get('thumbnailUrl', '') or item_data.get('thumbnail', '')
                                
                                if not (item_id and title and price > 0):
                                    continue
                                
                                formatted_item = {
                                    "search_term": keyword,
                                    "item_id": item_id,
                                    "title": title,
                                    "price": int(price),
                                    "currency": "JPY",
                                    "status": "active",
                                    "sold_date": None,
                                    "condition": item_data.get('itemCondition', {}).get('name', '中古'),
                                    "url": f"{self.base_url}/item/{item_id}",
                                    "image_url": thumbnail,
                                    "seller": item_data.get('seller', {}).get('name', 'メルカリ出品者')
                                }
                                
                                items.append(formatted_item)
                                print(f"商品{idx+1}: {title[:30]}... - ¥{price}", file=sys.stderr)
                                
                            except Exception as e:
                                print(f"商品データ解析エラー: {str(e)}", file=sys.stderr)
                                continue
                    
                except json.JSONDecodeError as e:
                    print(f"JSON解析エラー: {str(e)}", file=sys.stderr)
            
            # 別の方法: 正規表現で商品情報を抽出
            if not items:
                print("正規表現で商品を検索", file=sys.stderr)
                
                # 商品パターンを検索
                item_pattern = r'href="/item/(m\d+)".*?<span[^>]*>([^<]+)</span>.*?<span[^>]*>¥\s*([0-9,]+)</span>'
                matches = re.findall(item_pattern, html, re.DOTALL)
                
                for idx, (item_id, title, price_str) in enumerate(matches[:limit]):
                    try:
                        price = int(price_str.replace(',', ''))
                        
                        formatted_item = {
                            "search_term": keyword,
                            "item_id": item_id,
                            "title": title.strip(),
                            "price": price,
                            "currency": "JPY",
                            "status": "active",
                            "sold_date": None,
                            "condition": "中古",
                            "url": f"{self.base_url}/item/{item_id}",
                            "image_url": "",
                            "seller": "メルカリ出品者"
                        }
                        
                        items.append(formatted_item)
                        print(f"商品{idx+1}: {title[:30]}... - ¥{price}", file=sys.stderr)
                        
                    except Exception as e:
                        continue
            
        except Exception as e:
            print(f"HTML解析エラー: {str(e)}", file=sys.stderr)
        
        return items
    
    def _find_items_in_json(self, data: dict, path: str = "") -> list:
        """JSONデータから商品リストを再帰的に検索"""
        if isinstance(data, dict):
            # itemsやitemsDataなどのキーを探す
            for key in ['items', 'itemsData', 'searchResult', 'results', 'products']:
                if key in data and isinstance(data[key], list):
                    print(f"商品リスト発見: {path}.{key}", file=sys.stderr)
                    return data[key]
            
            # 再帰的に探索
            for key, value in data.items():
                result = self._find_items_in_json(value, f"{path}.{key}")
                if result:
                    return result
        
        elif isinstance(data, list) and len(data) > 0:
            # リストの要素が商品データっぽいかチェック
            if isinstance(data[0], dict) and ('id' in data[0] or 'itemId' in data[0]):
                if 'price' in data[0] or 'itemPrice' in data[0]:
                    print(f"商品リスト発見: {path}[]", file=sys.stderr)
                    return data
        
        return []

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_mercari_simple_scraper.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    client = MercariSimpleScrapingClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()