#!/usr/bin/env python3
"""
メルカリ実働検索スクリプト
実際のメルカリ内部APIを使用して商品データを取得します。
"""

import sys
import json
import requests
import time
import re
from urllib.parse import quote
from typing import List, Dict, Any
import random

class MercariWorkingClient:
    """実働するメルカリクライアント"""
    
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
            "X-Requested-With": "XMLHttpRequest",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        メルカリから実際の商品データを検索
        """
        try:
            print(f"メルカリ実働検索開始: {keyword}", file=sys.stderr)
            
            # 複数の検索方法を試行
            results = []
            
            # 方法1: 内部API検索
            results = self._try_internal_api(keyword, limit)
            if results:
                print(f"内部API成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 方法2: 検索ページからのデータ抽出
            results = self._try_page_extraction(keyword, limit)
            if results:
                print(f"ページ抽出成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 方法3: 異なるエンドポイント
            results = self._try_alternative_endpoints(keyword, limit)
            if results:
                print(f"代替エンドポイント成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            print(f"全ての検索方法が失敗しました", file=sys.stderr)
            return []
                
        except Exception as e:
            print(f"メルカリ検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_internal_api(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """内部APIを試行"""
        try:
            print(f"内部API試行: {keyword}", file=sys.stderr)
            
            # メルカリの実際のAPIパラメータ
            params = {
                "keyword": keyword,
                "limit": min(limit, 120),
                "offset": 0,
                "sort": "created_time",
                "order": "desc",
                "status": "on_sale",
                "category_root": "",
                "category_child": "",
                "category_id": "",
                "brand_name": "",
                "brand_id": "",
                "size_id": "",
                "price_min": "",
                "price_max": "",
                "item_condition_id": "",
                "shipping_payer_id": "",
                "exclude_keyword": ""
            }
            
            response = self.session.get(self.search_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if items:
                    return self._format_api_results(items, limit)
            
            print(f"内部API失敗: {response.status_code}", file=sys.stderr)
            return []
            
        except Exception as e:
            print(f"内部API例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_page_extraction(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """検索ページからデータを抽出"""
        try:
            print(f"ページ抽出試行: {keyword}", file=sys.stderr)
            
            # 検索ページにアクセス
            search_url = f"https://jp.mercari.com/search?keyword={quote(keyword)}&status=on_sale"
            
            # ランダムな遅延を追加
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                return self._extract_from_page(response.text, keyword, limit)
            
            return []
            
        except Exception as e:
            print(f"ページ抽出例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_alternative_endpoints(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """代替エンドポイントを試行"""
        try:
            print(f"代替エンドポイント試行: {keyword}", file=sys.stderr)
            
            # 異なるAPIエンドポイントを試行
            endpoints = [
                "https://api.mercari.jp/search/items",
                "https://api.mercari.jp/items/search",
                "https://jp.mercari.com/api/search"
            ]
            
            for endpoint in endpoints:
                try:
                    params = {
                        "q": keyword,
                        "keyword": keyword,
                        "limit": limit,
                        "status": "on_sale"
                    }
                    
                    response = self.session.get(endpoint, params=params, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and isinstance(data, dict):
                            items = data.get("items", data.get("data", []))
                            if items:
                                return self._format_api_results(items, limit)
                
                except Exception:
                    continue
            
            return []
            
        except Exception as e:
            print(f"代替エンドポイント例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_from_page(self, html: str, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """HTMLページから商品データを抽出"""
        try:
            items = []
            
            # Next.jsのデータを探す
            patterns = [
                r'window\.__NEXT_DATA__\s*=\s*({.*?});',
                r'window\.__NUXT__\s*=\s*({.*?});',
                r'"props":\s*({.*?"pageProps".*?})',
                r'"items":\s*(\[.*?\])'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        extracted_items = self._extract_items_from_data(data, keyword, limit)
                        if extracted_items:
                            items.extend(extracted_items)
                            if len(items) >= limit:
                                break
                    except json.JSONDecodeError:
                        continue
                
                if items:
                    break
            
            return items[:limit]
            
        except Exception as e:
            print(f"ページ抽出処理例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_items_from_data(self, data: dict, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """データ構造から商品情報を抽出"""
        items = []
        
        def search_recursive(obj, path=""):
            if isinstance(obj, dict):
                # 商品データらしいオブジェクトを探す
                if "id" in obj and "name" in obj and "price" in obj:
                    formatted_item = self._format_item_data(obj, keyword)
                    if formatted_item and self._validate_item(formatted_item):
                        items.append(formatted_item)
                        if len(items) >= limit:
                            return
                
                # 再帰的に探索
                for key, value in obj.items():
                    if key in ["items", "data", "results", "products"]:
                        search_recursive(value, f"{path}.{key}")
                    elif isinstance(value, (dict, list)):
                        search_recursive(value, f"{path}.{key}")
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_recursive(item, f"{path}[{i}]")
                    if len(items) >= limit:
                        break
        
        search_recursive(data)
        return items
    
    def _format_api_results(self, items: List[Dict], limit: int) -> List[Dict[str, Any]]:
        """API結果をフォーマット"""
        formatted_results = []
        
        for item in items[:limit]:
            formatted_item = self._format_item_data(item, "")
            if formatted_item and self._validate_item(formatted_item):
                formatted_results.append(formatted_item)
        
        return formatted_results
    
    def _format_item_data(self, item: dict, keyword: str) -> Dict[str, Any]:
        """商品データを統一フォーマットに変換"""
        try:
            # 価格の取得
            price = 0
            if "price" in item:
                price = int(item["price"])
            elif "selling_price" in item:
                price = int(item["selling_price"])
            
            # IDの取得
            item_id = item.get("id", "")
            if not item_id:
                item_id = item.get("item_id", "")
            
            # URLの構築
            url = ""
            if item_id:
                url = f"https://jp.mercari.com/item/{item_id}"
            elif "url" in item:
                url = item["url"]
            
            # 画像URLの取得
            image_url = ""
            if "thumbnails" in item and item["thumbnails"]:
                image_url = item["thumbnails"][0].get("url", "")
            elif "image" in item:
                image_url = item["image"]
            elif "photo" in item:
                image_url = item["photo"]
            
            # 商品名の取得
            title = item.get("name", item.get("title", ""))
            
            # 状態の取得
            condition = self._get_condition_name(item.get("item_condition_id", 1))
            
            return {
                "title": title,
                "name": title,
                "price": price,
                "url": url,
                "image_url": image_url,
                "condition": condition,
                "seller": item.get("seller", {}).get("name", "メルカリ出品者") if isinstance(item.get("seller"), dict) else "メルカリ出品者",
                "status": "active",
                "sold_date": None,
                "currency": "JPY",
                "item_id": item_id,
                "shipping_fee": 0,
                "total_price": price
            }
        except Exception as e:
            print(f"データフォーマットエラー: {str(e)}", file=sys.stderr)
            return None
    
    def _validate_item(self, item: dict) -> bool:
        """実際のアイテムかどうかを検証"""
        # 必須フィールドの存在確認
        required_fields = ["title", "price", "item_id"]
        for field in required_fields:
            if not item.get(field):
                return False
        
        # 価格が0以上であることを確認
        if item.get("price", 0) <= 0:
            return False
        
        # タイトルが実際の商品名らしいことを確認
        title = item.get("title", "")
        if len(title) < 3:
            return False
        
        # アイテムIDが実際の形式であることを確認
        item_id = item.get("item_id", "")
        if not item_id or len(item_id) < 5:
            return False
        
        return True
    
    def _get_condition_name(self, condition_id: int) -> str:
        """商品状態IDから状態名を取得"""
        conditions = {
            1: "新品、未使用",
            2: "未使用に近い",
            3: "目立った傷や汚れなし",
            4: "やや傷や汚れあり",
            5: "傷や汚れあり",
            6: "全体的に状態が悪い"
        }
        return conditions.get(condition_id, "中古")

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_mercari_working.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"メルカリ実働検索開始: {keyword}, limit: {limit}", file=sys.stderr)
    
    client = MercariWorkingClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()
