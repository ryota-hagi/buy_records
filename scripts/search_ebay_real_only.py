#!/usr/bin/env python3
"""
eBay実データ専用検索スクリプト
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

class EbayRealOnlyClient:
    """実データのみを取得するeBayクライアント"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com"
        self.api_url = "https://svcs.ebay.com/services/search/FindingService/v1"
        
        # 環境変数からAPIキーを取得
        self.app_id = os.getenv('EBAY_APP_ID', 'ariGaT-records-PRD-1a6ee1171-104bfaa4')
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 為替レート（デフォルト）
        self.exchange_rate = 150.0
    
    def get_exchange_rate(self) -> float:
        """為替レートを取得"""
        try:
            # 簡単な為替レートAPI
            response = self.session.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
            if response.status_code == 200:
                data = response.json()
                rate = data.get('rates', {}).get('JPY', 150.0)
                print(f"為替レート取得成功: 1 USD = {rate} JPY", file=sys.stderr)
                return float(rate)
        except Exception as e:
            print(f"為替レート取得失敗: {str(e)}", file=sys.stderr)
        
        print(f"デフォルト為替レートを使用: 1 USD = {self.exchange_rate} JPY", file=sys.stderr)
        return self.exchange_rate
    
    def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        eBayから実際の商品データのみを検索
        
        Args:
            keyword: 検索キーワード
            limit: 取得する商品数
            
        Returns:
            List[Dict[str, Any]]: 実際の商品データのリスト（空の場合もある）
        """
        try:
            print(f"eBay実データ検索開始: {keyword}", file=sys.stderr)
            
            # 為替レートを取得
            exchange_rate = self.get_exchange_rate()
            
            # 複数の検索方法を試行
            results = []
            
            # 方法1: Finding APIを使用
            results = self._try_finding_api(keyword, limit, exchange_rate)
            if results:
                print(f"Finding API成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 方法2: Webスクレイピング
            results = self._try_web_scraping(keyword, limit, exchange_rate)
            if results:
                print(f"Webスクレイピング成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 方法3: モバイル版検索
            results = self._try_mobile_search(keyword, limit, exchange_rate)
            if results:
                print(f"モバイル検索成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 全ての方法が失敗した場合は空のリストを返す（サンプルデータは生成しない）
            print(f"全ての検索方法が失敗しました。実データが取得できませんでした。", file=sys.stderr)
            return []
                
        except Exception as e:
            print(f"eBay検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_finding_api(self, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """Finding APIを試行"""
        try:
            print(f"Finding API試行: {keyword}", file=sys.stderr)
            
            params = {
                'OPERATION-NAME': 'findItemsByKeywords',
                'SERVICE-VERSION': '1.0.0',
                'SECURITY-APPNAME': self.app_id,
                'RESPONSE-DATA-FORMAT': 'JSON',
                'keywords': keyword,
                'paginationInput.entriesPerPage': min(limit, 20),
                'sortOrder': 'PricePlusShipping',
                'itemFilter(0).name': 'ListingType',
                'itemFilter(0).value': 'FixedPrice',
                'itemFilter(1).name': 'Condition',
                'itemFilter(1).value': 'Used'
            }
            
            response = self.session.get(self.api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                search_result = data.get('findItemsByKeywordsResponse', [{}])[0].get('searchResult', [{}])[0]
                items = search_result.get('item', [])
                
                if items:
                    print(f"Finding API成功: {len(items)}件取得", file=sys.stderr)
                    return self._format_finding_results(items, exchange_rate)
            
            return []
            
        except Exception as e:
            print(f"Finding API例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_web_scraping(self, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """Webスクレイピングを試行"""
        try:
            print(f"Webスクレイピング試行: {keyword}", file=sys.stderr)
            
            # eBay検索ページにアクセス
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}&_sacat=0&_sop=15"
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code != 200:
                print(f"検索ページアクセス失敗: {response.status_code}", file=sys.stderr)
                return []
            
            return self._extract_real_data_from_html(response.text, keyword, limit, exchange_rate)
            
        except Exception as e:
            print(f"Webスクレイピング例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_mobile_search(self, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """モバイル版検索を試行"""
        try:
            print(f"モバイル検索試行: {keyword}", file=sys.stderr)
            
            # モバイル用ヘッダー
            mobile_headers = self.headers.copy()
            mobile_headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
            
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}"
            response = self.session.get(search_url, headers=mobile_headers, timeout=15)
            
            if response.status_code != 200:
                print(f"モバイル検索失敗: {response.status_code}", file=sys.stderr)
                return []
            
            return self._extract_real_data_from_html(response.text, keyword, limit, exchange_rate)
            
        except Exception as e:
            print(f"モバイル検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_real_data_from_html(self, html: str, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """HTMLから実際の商品データを抽出"""
        try:
            items = []
            
            # 商品タイトルパターン
            title_pattern = r'<h3[^>]*class="[^"]*s-item__title[^"]*"[^>]*>([^<]+)</h3>'
            titles = re.findall(title_pattern, html, re.IGNORECASE)
            
            # 価格パターン
            price_pattern = r'<span[^>]*class="[^"]*s-item__price[^"]*"[^>]*>\$([0-9,]+\.?[0-9]*)</span>'
            prices = re.findall(price_pattern, html, re.IGNORECASE)
            
            # URLパターン
            url_pattern = r'<a[^>]*href="([^"]*)" class="[^"]*s-item__link[^"]*"'
            urls = re.findall(url_pattern, html, re.IGNORECASE)
            
            # 画像パターン
            img_pattern = r'<img[^>]*src="([^"]*)"[^>]*class="[^"]*s-item__image[^"]*"'
            images = re.findall(img_pattern, html, re.IGNORECASE)
            
            # データを組み合わせ
            min_length = min(len(titles), len(prices), len(urls), limit)
            
            for i in range(min_length):
                try:
                    price_usd = float(prices[i].replace(',', ''))
                    price_jpy = int(price_usd * exchange_rate)
                    
                    item = {
                        "title": titles[i].strip(),
                        "name": titles[i].strip(),
                        "price": price_jpy,
                        "url": urls[i] if urls[i].startswith('http') else f"https://www.ebay.com{urls[i]}",
                        "image_url": images[i] if i < len(images) else "",
                        "condition": "Used",
                        "seller": "eBay Seller",
                        "status": "active",
                        "sold_date": None,
                        "currency": "JPY",
                        "exchange_rate": exchange_rate,
                        "shipping_fee": 0,
                        "total_price": price_jpy,
                        "item_id": self._extract_item_id_from_url(urls[i])
                    }
                    
                    # 実際のアイテムかどうかを検証
                    if self._validate_real_item(item):
                        items.append(item)
                        
                except Exception as e:
                    print(f"商品データ作成エラー: {str(e)}", file=sys.stderr)
                    continue
            
            return items
            
        except Exception as e:
            print(f"データ抽出例外: {str(e)}", file=sys.stderr)
            return []
    
    def _format_finding_results(self, items: List[Dict], exchange_rate: float) -> List[Dict[str, Any]]:
        """Finding API結果をフォーマット"""
        formatted_results = []
        
        for item in items:
            try:
                current_price = float(item.get('sellingStatus', [{}])[0].get('currentPrice', [{}])[0].get('__value__', 0))
                shipping_cost = float(item.get('shippingInfo', [{}])[0].get('shippingServiceCost', [{}])[0].get('__value__', 0))
                title = item.get('title', [''])[0]
                url = item.get('viewItemURL', [''])[0]
                image_url = item.get('galleryURL', [''])[0]
                condition = item.get('condition', [{}])[0].get('conditionDisplayName', ['Used'])[0]
                seller = item.get('sellerInfo', [{}])[0].get('sellerUserName', ['eBay Seller'])[0]
                
                price_jpy = int(current_price * exchange_rate)
                shipping_jpy = int(shipping_cost * exchange_rate)
                
                formatted_item = {
                    "title": title,
                    "name": title,
                    "price": price_jpy,
                    "url": url,
                    "image_url": image_url,
                    "condition": condition,
                    "seller": seller,
                    "status": "active",
                    "sold_date": None,
                    "currency": "JPY",
                    "exchange_rate": exchange_rate,
                    "shipping_fee": shipping_jpy,
                    "total_price": price_jpy + shipping_jpy,
                    "item_id": self._extract_item_id_from_url(url)
                }
                
                # 実際のアイテムかどうかを検証
                if self._validate_real_item(formatted_item):
                    formatted_results.append(formatted_item)
                    
            except Exception as e:
                print(f"Finding結果フォーマットエラー: {str(e)}", file=sys.stderr)
                continue
        
        return formatted_results
    
    def _extract_item_id_from_url(self, url: str) -> str:
        """URLからアイテムIDを抽出"""
        try:
            # eBayのアイテムIDパターンを抽出
            match = re.search(r'/itm/[^/]*?(\d{12,})', url)
            if match:
                return match.group(1)
            
            # フォールバック: URLの最後の数字部分
            match = re.search(r'(\d{10,})(?:\?|$)', url)
            if match:
                return match.group(1)
            
            return ""
        except Exception:
            return ""
    
    def _validate_real_item(self, item: dict) -> bool:
        """実際のアイテムかどうかを検証"""
        # 必須フィールドの存在確認
        required_fields = ["title", "price", "url"]
        for field in required_fields:
            if not item.get(field):
                return False
        
        # 価格が0以上であることを確認
        if item.get("price", 0) <= 0:
            return False
        
        # URLが実際のeBayURLであることを確認
        url = item.get("url", "")
        if not (url.startswith("https://www.ebay.com") or url.startswith("http://www.ebay.com")):
            return False
        
        # タイトルが実際の商品名らしいことを確認
        title = item.get("title", "")
        if len(title) < 5 or "sample" in title.lower() or "test" in title.lower():
            return False
        
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_ebay_real_only.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"eBay実データ専用検索開始: {keyword}, limit: {limit}", file=sys.stderr)
    
    client = EbayRealOnlyClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()
