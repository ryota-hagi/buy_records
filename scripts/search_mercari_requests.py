#!/usr/bin/env python3
"""
メルカリrequestsベース検索スクリプト
実際のメルカリAPIエンドポイントを使用して商品データを取得します。
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

class MercariRequestsClient:
    """requestsを使用したメルカリクライアント"""
    
    def __init__(self):
        self.base_url = "https://api.mercari.jp"
        self.search_url = "https://api.mercari.jp/v2/entities:search"
        
        # 実際のブラウザのヘッダーを模倣
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://jp.mercari.com/",
            "Origin": "https://jp.mercari.com",
            "X-Platform": "web",
            "DPoP": "",  # 必要に応じて設定
            "Authorization": "",  # 必要に応じて設定
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        メルカリから商品データを検索
        """
        try:
            print(f"メルカリrequests検索開始: {keyword}", file=sys.stderr)
            
            # 方法1: 内部APIを試す
            results = self._try_internal_api(keyword, limit)
            if results:
                return results
            
            # 方法2: 検索ページから情報を取得
            results = self._try_search_page(keyword, limit)
            if results:
                return results
            
            print("すべての方法が失敗しました", file=sys.stderr)
            return []
            
        except Exception as e:
            print(f"検索エラー: {str(e)}", file=sys.stderr)
            return []
    
    def _try_internal_api(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """内部APIを使用した検索"""
        try:
            print(f"内部API検索試行: {keyword}", file=sys.stderr)
            
            # パラメータ
            params = {
                "userId": "",
                "pageToken": "",
                "searchSessionId": "",
                "indexName": "item_search_query",
                "searchCondition": {
                    "keyword": keyword,
                    "excludeKeyword": "",
                    "sort": "SORT_SCORE",
                    "order": "ORDER_DESC",
                    "status": ["STATUS_ON_SALE"],
                    "sizeId": [],
                    "categoryId": [],
                    "brandId": [],
                    "sellerId": [],
                    "priceMin": 0,
                    "priceMax": 0,
                    "itemConditionId": [],
                    "shippingPayerId": [],
                    "shippingFromArea": [],
                    "shippingMethod": [],
                    "colorId": [],
                    "hasCoupon": False,
                    "attributes": [],
                    "itemTypes": [],
                    "skuIds": []
                },
                "defaultDatasets": ["DATASET_TYPE_MERCARI"],
                "serviceFrom": "suruga",
                "size": limit,
                "withItemBrand": True,
                "withItemSize": True,
                "withItemPromotions": True,
                "withItemSizes": True,
                "withShippingPayer": True
            }
            
            # APIリクエスト
            response = self.session.post(
                self.search_url,
                json=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if items:
                    print(f"内部API成功: {len(items)}件取得", file=sys.stderr)
                    return self._format_api_results(items[:limit])
                else:
                    print("内部API: 結果が空", file=sys.stderr)
            else:
                print(f"内部APIエラー: {response.status_code}", file=sys.stderr)
                
        except Exception as e:
            print(f"内部API例外: {str(e)}", file=sys.stderr)
        
        return []
    
    def _try_search_page(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """検索ページからデータを抽出"""
        try:
            print(f"検索ページ試行: {keyword}", file=sys.stderr)
            
            # 検索URL（価格の安い順）
            search_url = f"https://jp.mercari.com/search?keyword={quote(keyword)}&status=on_sale&sort=price&order=asc"
            
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                # HTMLからNext.jsのデータを抽出
                import re
                
                # __NEXT_DATA__を探す
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text, re.DOTALL)
                
                if match:
                    try:
                        data = json.loads(match.group(1))
                        
                        # プロップスから商品データを探す
                        props = data.get("props", {})
                        page_props = props.get("pageProps", {})
                        
                        # 様々な場所から商品データを探す
                        items = self._find_items_in_data(page_props)
                        
                        if items:
                            print(f"検索ページ成功: {len(items)}件取得", file=sys.stderr)
                            return self._format_page_results(items[:limit])
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON解析エラー: {str(e)}", file=sys.stderr)
                
                # 別の方法: 正規表現で商品情報を抽出
                items = self._extract_items_from_html(response.text, limit)
                if items:
                    return items
                    
            else:
                print(f"検索ページエラー: {response.status_code}", file=sys.stderr)
                
        except Exception as e:
            print(f"検索ページ例外: {str(e)}", file=sys.stderr)
        
        return []
    
    def _find_items_in_data(self, data: Any) -> List[Dict[str, Any]]:
        """データから商品リストを再帰的に検索"""
        if isinstance(data, dict):
            # 商品リストのキーを探す
            for key in ['items', 'itemList', 'searchResult', 'products']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            
            # 再帰的に探索
            for value in data.values():
                result = self._find_items_in_data(value)
                if result:
                    return result
        
        elif isinstance(data, list) and len(data) > 0:
            # リストの要素が商品データっぽいかチェック
            if isinstance(data[0], dict) and 'id' in data[0]:
                return data
        
        return []
    
    def _extract_items_from_html(self, html: str, limit: int) -> List[Dict[str, Any]]:
        """HTMLから正規表現で商品情報を抽出"""
        items = []
        
        try:
            # 商品リンクのパターン
            pattern = r'href="/item/(m\d+)"[^>]*>.*?<img[^>]*alt="([^"]+)"[^>]*src="([^"]+)".*?¥\s*([0-9,]+)'
            matches = re.findall(pattern, html, re.DOTALL)
            
            for match in matches[:limit]:
                item_id, title, image_url, price_str = match
                price = int(price_str.replace(',', ''))
                
                items.append({
                    "item_id": item_id,
                    "title": title,
                    "name": title,
                    "price": price,
                    "url": f"https://jp.mercari.com/item/{item_id}",
                    "image_url": image_url,
                    "condition": "中古",
                    "seller": "メルカリ出品者",
                    "status": "active",
                    "sold_date": None,
                    "currency": "JPY",
                    "shipping_fee": 0,
                    "total_price": price
                })
                
        except Exception as e:
            print(f"HTML抽出エラー: {str(e)}", file=sys.stderr)
        
        return items
    
    def _format_api_results(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """API結果を統一フォーマットに変換"""
        formatted = []
        
        for item in items:
            try:
                formatted.append({
                    "item_id": item.get("id", ""),
                    "title": item.get("name", ""),
                    "name": item.get("name", ""),
                    "price": int(item.get("price", 0)),
                    "url": f"https://jp.mercari.com/item/{item.get('id', '')}",
                    "image_url": item.get("thumbnails", [{}])[0].get("url", "") if item.get("thumbnails") else "",
                    "condition": item.get("itemCondition", {}).get("name", "中古"),
                    "seller": item.get("seller", {}).get("name", "メルカリ出品者"),
                    "status": "active",
                    "sold_date": None,
                    "currency": "JPY",
                    "shipping_fee": 0,
                    "total_price": int(item.get("price", 0))
                })
            except Exception as e:
                print(f"フォーマットエラー: {str(e)}", file=sys.stderr)
                continue
        
        return formatted
    
    def _format_page_results(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ページ結果を統一フォーマットに変換"""
        formatted = []
        
        for item in items:
            try:
                # 様々なキー名に対応
                item_id = item.get("id") or item.get("itemId") or ""
                title = item.get("name") or item.get("itemName") or item.get("title") or ""
                price = item.get("price") or item.get("itemPrice") or 0
                
                # 画像URL
                image_url = ""
                if "thumbnails" in item and item["thumbnails"]:
                    image_url = item["thumbnails"][0].get("url", "")
                elif "thumbnail" in item:
                    image_url = item["thumbnail"]
                elif "imageUrl" in item:
                    image_url = item["imageUrl"]
                
                formatted.append({
                    "item_id": item_id,
                    "title": title,
                    "name": title,
                    "price": int(price),
                    "url": f"https://jp.mercari.com/item/{item_id}",
                    "image_url": image_url,
                    "condition": "中古",
                    "seller": "メルカリ出品者",
                    "status": "active",
                    "sold_date": None,
                    "currency": "JPY",
                    "shipping_fee": 0,
                    "total_price": int(price)
                })
            except Exception as e:
                print(f"フォーマットエラー: {str(e)}", file=sys.stderr)
                continue
        
        return formatted

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_mercari_requests.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    client = MercariRequestsClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()