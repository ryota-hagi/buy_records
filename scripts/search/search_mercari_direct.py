#!/usr/bin/env python3
"""
メルカリ直接スクレイピング検索スクリプト
HTMLから直接商品データを抽出します。
"""

import sys
import json
import requests
import time
import re
from urllib.parse import quote
from typing import List, Dict, Any
import random
from dotenv import load_dotenv
import os

# .envファイルを読み込む
load_dotenv()

class MercariDirectClient:
    """直接HTMLスクレイピングを行うメルカリクライアント"""
    
    def __init__(self):
        self.base_url = "https://jp.mercari.com"
        
        # 実際のブラウザのヘッダーを模倣
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        メルカリから商品データを検索
        """
        try:
            print(f"メルカリ直接スクレイピング開始: {keyword}", file=sys.stderr)
            
            # 検索URL（価格の安い順）
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
            
            return items
            
        except Exception as e:
            print(f"検索エラー: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_items_from_html(self, html: str, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """HTMLから商品データを抽出"""
        items = []
        
        try:
            # __NEXT_DATA__を探す
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
            
            if match:
                print("__NEXT_DATA__を発見", file=sys.stderr)
                try:
                    data = json.loads(match.group(1))
                    
                    # デバッグ用: データ構造を確認
                    self._debug_data_structure(data)
                    
                    # 商品データを探す
                    items_data = self._find_items_recursively(data)
                    
                    if items_data:
                        print(f"商品データ発見: {len(items_data)}件", file=sys.stderr)
                        
                        for idx, item_data in enumerate(items_data[:limit]):
                            formatted_item = self._format_item_data(item_data)
                            if formatted_item:
                                items.append(formatted_item)
                                print(f"商品{idx+1}: {formatted_item['title'][:30]}... - ¥{formatted_item['price']:,}", file=sys.stderr)
                    else:
                        print("__NEXT_DATA__内に商品データが見つかりません", file=sys.stderr)
                    
                except json.JSONDecodeError as e:
                    print(f"JSON解析エラー: {str(e)}", file=sys.stderr)
            else:
                print("__NEXT_DATA__が見つかりません", file=sys.stderr)
            
            # 別の方法: 簡単なパターンマッチング
            if not items:
                print("パターンマッチングで商品を検索", file=sys.stderr)
                items = self._extract_by_pattern(html, limit)
            
        except Exception as e:
            print(f"HTML抽出エラー: {str(e)}", file=sys.stderr)
        
        return items
    
    def _debug_data_structure(self, data: Any, level: int = 0, max_level: int = 3):
        """データ構造をデバッグ出力"""
        if level > max_level:
            return
        
        indent = "  " * level
        
        if isinstance(data, dict):
            for key in list(data.keys())[:10]:  # 最初の10キーのみ
                value = data[key]
                if isinstance(value, (dict, list)):
                    print(f"{indent}{key}: {type(value).__name__}", file=sys.stderr)
                    if key in ['props', 'pageProps', 'initialState', '__APOLLO_STATE__', 'search']:
                        self._debug_data_structure(value, level + 1, max_level)
                else:
                    print(f"{indent}{key}: {type(value).__name__}", file=sys.stderr)
        elif isinstance(data, list) and len(data) > 0:
            print(f"{indent}List[{len(data)}]", file=sys.stderr)
            if isinstance(data[0], dict):
                print(f"{indent}  First item keys: {list(data[0].keys())[:10]}", file=sys.stderr)
    
    def _find_items_recursively(self, data: Any, path: str = "", visited: set = None) -> List[Dict[str, Any]]:
        """データから商品リストを再帰的に検索"""
        if visited is None:
            visited = set()
        
        # 循環参照を避ける
        if id(data) in visited:
            return []
        visited.add(id(data))
        
        items = []
        
        if isinstance(data, dict):
            # 商品っぽいデータの判定
            if 'id' in data and 'name' in data and 'price' in data:
                print(f"商品候補発見 at {path}: {data.get('name', '')[:30]}", file=sys.stderr)
                return [data]
            
            # 商品リストっぽいキーを探す
            for key in ['items', 'itemList', 'searchResult', 'products', 'results', 'data']:
                if key in data:
                    value = data[key]
                    if isinstance(value, list) and len(value) > 0:
                        if isinstance(value[0], dict) and any(k in value[0] for k in ['id', 'itemId', 'productId']):
                            print(f"商品リスト発見 at {path}.{key}: {len(value)}件", file=sys.stderr)
                            return value
            
            # 再帰的に探索
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    result = self._find_items_recursively(value, f"{path}.{key}", visited)
                    if result:
                        return result
        
        elif isinstance(data, list):
            # リストの要素が商品データっぽいかチェック
            if len(data) > 0 and isinstance(data[0], dict):
                if any(k in data[0] for k in ['id', 'itemId']) and any(k in data[0] for k in ['price', 'itemPrice']):
                    print(f"商品リスト発見 at {path}[]: {len(data)}件", file=sys.stderr)
                    return data
            
            # 各要素を再帰的に探索
            for i, item in enumerate(data[:10]):  # 最初の10要素のみ
                if isinstance(item, (dict, list)):
                    result = self._find_items_recursively(item, f"{path}[{i}]", visited)
                    if result:
                        return result
        
        return []
    
    def _extract_by_pattern(self, html: str, limit: int) -> List[Dict[str, Any]]:
        """パターンマッチングで商品を抽出"""
        items = []
        
        # 商品リンクのパターン（複数試行）
        patterns = [
            r'<a[^>]*href="(/item/m\d+)"[^>]*>.*?<img[^>]*alt="([^"]+)".*?</a>',
            r'href="/item/(m\d+)"[^>]*>[^<]*<[^>]*>([^<]+)<.*?¥\s*([0-9,]+)',
            r'<a[^>]*data-testid="item-cell"[^>]*href="(/item/m\d+)"[^>]*>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            if matches:
                print(f"パターンマッチ成功: {len(matches)}件", file=sys.stderr)
                break
        
        # より緩いパターンで商品IDを探す
        if not matches:
            item_ids = re.findall(r'/item/(m\d+)', html)
            if item_ids:
                print(f"商品ID発見: {len(set(item_ids))}個", file=sys.stderr)
                # 最初の数個だけ処理
                for item_id in list(set(item_ids))[:limit]:
                    items.append({
                        "item_id": item_id,
                        "title": f"メルカリ商品 {item_id}",
                        "name": f"メルカリ商品 {item_id}",
                        "price": 0,  # 価格は不明
                        "url": f"https://jp.mercari.com/item/{item_id}",
                        "image_url": "",
                        "condition": "中古",
                        "seller": "メルカリ出品者",
                        "status": "active",
                        "sold_date": None,
                        "currency": "JPY",
                        "shipping_fee": 0,
                        "total_price": 0
                    })
        
        return items
    
    def _format_item_data(self, item_data: dict) -> Dict[str, Any]:
        """商品データを統一フォーマットに変換"""
        try:
            # 様々なキー名に対応
            item_id = item_data.get('id') or item_data.get('itemId') or item_data.get('productId', '')
            title = item_data.get('name') or item_data.get('itemName') or item_data.get('title', '')
            price = item_data.get('price') or item_data.get('itemPrice') or 0
            
            # 価格が文字列の場合
            if isinstance(price, str):
                price = int(re.sub(r'[^0-9]', '', price))
            else:
                price = int(price)
            
            # 画像URL
            image_url = ""
            if 'thumbnails' in item_data and item_data['thumbnails']:
                if isinstance(item_data['thumbnails'][0], dict):
                    image_url = item_data['thumbnails'][0].get('url', '')
                else:
                    image_url = item_data['thumbnails'][0]
            elif 'thumbnail' in item_data:
                image_url = item_data['thumbnail']
            elif 'imageUrl' in item_data:
                image_url = item_data['imageUrl']
            elif 'photos' in item_data and item_data['photos']:
                image_url = item_data['photos'][0] if isinstance(item_data['photos'][0], str) else item_data['photos'][0].get('url', '')
            
            return {
                "item_id": str(item_id),
                "title": title,
                "name": title,
                "price": price,
                "url": f"https://jp.mercari.com/item/{item_id}",
                "image_url": image_url,
                "condition": item_data.get('itemCondition', {}).get('name', '中古') if isinstance(item_data.get('itemCondition'), dict) else '中古',
                "seller": item_data.get('seller', {}).get('name', 'メルカリ出品者') if isinstance(item_data.get('seller'), dict) else 'メルカリ出品者',
                "status": "active",
                "sold_date": None,
                "currency": "JPY",
                "shipping_fee": 0,
                "total_price": price
            }
            
        except Exception as e:
            print(f"フォーマットエラー: {str(e)}", file=sys.stderr)
            return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_mercari_direct.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    client = MercariDirectClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()