#!/usr/bin/env python3
"""
メルカリ実データ専用検索スクリプト
サンプルデータやモックデータは一切生成せず、実際のデータのみを取得します。
"""

import sys
import json
import requests
import time
import re
from urllib.parse import quote
from typing import List, Dict, Any
import os

class MercariRealOnlyClient:
    """実データのみを取得するメルカリクライアント"""
    
    def __init__(self):
        self.base_url = "https://jp.mercari.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        メルカリから実際の商品データのみを検索
        
        Args:
            keyword: 検索キーワード
            limit: 取得する商品数
            
        Returns:
            List[Dict[str, Any]]: 実際の商品データのリスト（空の場合もある）
        """
        try:
            print(f"メルカリ実データ検索開始: {keyword}", file=sys.stderr)
            
            # 複数の検索方法を試行
            results = []
            
            # 方法1: 直接検索ページアクセス
            results = self._try_direct_search(keyword, limit)
            if results:
                print(f"直接検索成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 方法2: モバイル版検索
            results = self._try_mobile_search(keyword, limit)
            if results:
                print(f"モバイル検索成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 方法3: カテゴリ検索
            results = self._try_category_search(keyword, limit)
            if results:
                print(f"カテゴリ検索成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 全ての方法が失敗した場合は空のリストを返す（サンプルデータは生成しない）
            print(f"全ての検索方法が失敗しました。実データが取得できませんでした。", file=sys.stderr)
            return []
                
        except Exception as e:
            print(f"メルカリ検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_direct_search(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """直接検索ページにアクセスして実データを取得"""
        try:
            print(f"直接検索試行: {keyword}", file=sys.stderr)
            
            search_url = f"https://jp.mercari.com/search?keyword={quote(keyword)}&status=on_sale"
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code != 200:
                print(f"直接検索失敗: {response.status_code}", file=sys.stderr)
                return []
            
            return self._extract_real_data_from_html(response.text, keyword, limit)
            
        except Exception as e:
            print(f"直接検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_mobile_search(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """モバイル版で検索を試行"""
        try:
            print(f"モバイル検索試行: {keyword}", file=sys.stderr)
            
            # モバイル用ヘッダー
            mobile_headers = self.headers.copy()
            mobile_headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
            
            search_url = f"https://jp.mercari.com/search?keyword={quote(keyword)}"
            response = self.session.get(search_url, headers=mobile_headers, timeout=30)
            
            if response.status_code != 200:
                print(f"モバイル検索失敗: {response.status_code}", file=sys.stderr)
                return []
            
            return self._extract_real_data_from_html(response.text, keyword, limit)
            
        except Exception as e:
            print(f"モバイル検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_category_search(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """カテゴリ検索を試行"""
        try:
            print(f"カテゴリ検索試行: {keyword}", file=sys.stderr)
            
            # 一般的なカテゴリで検索
            categories = ["1", "2", "3"]  # 実際のカテゴリID
            
            for category in categories:
                search_url = f"https://jp.mercari.com/search?keyword={quote(keyword)}&category_root={category}"
                response = self.session.get(search_url, timeout=30)
                
                if response.status_code == 200:
                    results = self._extract_real_data_from_html(response.text, keyword, limit)
                    if results:
                        return results
            
            return []
            
        except Exception as e:
            print(f"カテゴリ検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_real_data_from_html(self, html: str, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """HTMLから実際の商品データを抽出"""
        try:
            items = []
            
            # 実際のメルカリページから商品データを抽出
            # JSONデータを探す
            json_pattern = r'<script[^>]*>.*?window\.__NUXT__\s*=\s*({.*?});.*?</script>'
            json_matches = re.findall(json_pattern, html, re.DOTALL)
            
            for json_str in json_matches:
                try:
                    data = json.loads(json_str)
                    # データ構造を探索して商品情報を抽出
                    items.extend(self._parse_nuxt_data(data, keyword, limit))
                    if len(items) >= limit:
                        break
                except json.JSONDecodeError:
                    continue
            
            # JSONが見つからない場合は、HTMLパターンマッチングを試行
            if not items:
                items = self._extract_from_html_patterns(html, keyword, limit)
            
            # 実際のデータのみを返す（URLが実在するもののみ）
            real_items = []
            for item in items[:limit]:
                if self._validate_real_item(item):
                    real_items.append(item)
            
            return real_items
            
        except Exception as e:
            print(f"データ抽出例外: {str(e)}", file=sys.stderr)
            return []
    
    def _parse_nuxt_data(self, data: dict, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """Nuxtデータから商品情報を抽出"""
        items = []
        
        def extract_items_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "items" and isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and "id" in item and "name" in item:
                                formatted_item = self._format_item_data(item, keyword)
                                if formatted_item:
                                    items.append(formatted_item)
                                    if len(items) >= limit:
                                        return
                    else:
                        extract_items_recursive(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_items_recursive(item, f"{path}[{i}]")
        
        extract_items_recursive(data)
        return items
    
    def _extract_from_html_patterns(self, html: str, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """HTMLパターンマッチングで商品データを抽出"""
        items = []
        
        # 商品リンクパターン
        link_pattern = r'<a[^>]*href="(/item/[^"]+)"[^>]*>'
        links = re.findall(link_pattern, html)
        
        # 商品名パターン
        name_pattern = r'<[^>]*data-testid="item-name"[^>]*>([^<]+)</[^>]*>'
        names = re.findall(name_pattern, html)
        
        # 価格パターン
        price_pattern = r'<[^>]*data-testid="item-price"[^>]*>[^0-9]*([0-9,]+)[^<]*</[^>]*>'
        prices = re.findall(price_pattern, html)
        
        # データを組み合わせ
        min_length = min(len(links), len(names), len(prices), limit)
        
        for i in range(min_length):
            try:
                price_str = prices[i].replace(",", "")
                if price_str.isdigit():
                    item = {
                        "title": names[i].strip(),
                        "name": names[i].strip(),
                        "price": int(price_str),
                        "url": f"https://jp.mercari.com{links[i]}",
                        "image_url": "",
                        "condition": "中古",
                        "seller": "メルカリ出品者",
                        "status": "active",
                        "sold_date": None,
                        "currency": "JPY",
                        "item_id": links[i].split("/")[-1],
                        "shipping_fee": 0,
                        "total_price": int(price_str)
                    }
                    items.append(item)
            except (ValueError, IndexError):
                continue
        
        return items
    
    def _format_item_data(self, item: dict, keyword: str) -> Dict[str, Any]:
        """商品データを統一フォーマットに変換"""
        try:
            return {
                "title": item.get("name", ""),
                "name": item.get("name", ""),
                "price": int(item.get("price", 0)),
                "url": f"https://jp.mercari.com/item/{item.get('id', '')}",
                "image_url": item.get("thumbnails", [{}])[0].get("url", "") if item.get("thumbnails") else "",
                "condition": self._get_condition_name(item.get("item_condition_id", 1)),
                "seller": item.get("seller", {}).get("name", "メルカリ出品者") if isinstance(item.get("seller"), dict) else "メルカリ出品者",
                "status": "active",
                "sold_date": None,
                "currency": "JPY",
                "item_id": item.get("id", ""),
                "shipping_fee": 0,
                "total_price": int(item.get("price", 0))
            }
        except Exception:
            return None
    
    def _validate_real_item(self, item: dict) -> bool:
        """実際のアイテムかどうかを検証"""
        # 必須フィールドの存在確認
        required_fields = ["title", "price", "url", "item_id"]
        for field in required_fields:
            if not item.get(field):
                return False
        
        # 価格が0以上であることを確認
        if item.get("price", 0) <= 0:
            return False
        
        # URLが実際のメルカリURLであることを確認
        url = item.get("url", "")
        if not url.startswith("https://jp.mercari.com/item/"):
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
        print("Usage: python search_mercari_real_only.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"メルカリ実データ専用検索開始: {keyword}, limit: {limit}", file=sys.stderr)
    
    client = MercariRealOnlyClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()
