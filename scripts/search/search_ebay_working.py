#!/usr/bin/env python3
"""
eBay実働検索スクリプト
実際のeBay APIとWebスクレイピングを使用して商品データを取得します。
"""

import sys
import json
import requests
import time
import re
from urllib.parse import quote
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

class EbayWorkingClient:
    """実働するeBayクライアント"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com"
        self.api_url = "https://svcs.ebay.com/services/search/FindingService/v1"
        
        # 環境変数からAPIキーを取得
        self.app_id = os.getenv('EBAY_APP_ID', 'ariGaT-records-PRD-1a6ee1171-104bfaa4')
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 為替レート
        self.exchange_rate = 150.0
    
    def get_exchange_rate(self) -> float:
        """為替レートを取得"""
        try:
            response = self.session.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
            if response.status_code == 200:
                data = response.json()
                rate = data.get('rates', {}).get('JPY', 150.0)
                print(f"為替レート取得成功: 1 USD = {rate} JPY", file=sys.stderr)
                return float(rate)
        except Exception as e:
            print(f"為替レート取得失敗: {str(e)}", file=sys.stderr)
        
        return self.exchange_rate
    
    def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        eBayから実際の商品データを検索
        """
        try:
            print(f"eBay実働検索開始: {keyword}", file=sys.stderr)
            
            # 為替レートを取得
            exchange_rate = self.get_exchange_rate()
            
            # 複数の検索方法を試行
            results = []
            
            # 方法1: Finding APIを使用
            results = self._try_finding_api(keyword, limit, exchange_rate)
            if results:
                print(f"Finding API成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 方法2: 改良されたWebスクレイピング
            results = self._try_improved_scraping(keyword, limit, exchange_rate)
            if results:
                print(f"改良スクレイピング成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 方法3: モバイル版API
            results = self._try_mobile_api(keyword, limit, exchange_rate)
            if results:
                print(f"モバイルAPI成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            print(f"全ての検索方法が失敗しました", file=sys.stderr)
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
                'itemFilter(1).value(0)': 'New',
                'itemFilter(1).value(1)': 'Used'
            }
            
            response = self.session.get(self.api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                search_result = data.get('findItemsByKeywordsResponse', [{}])[0].get('searchResult', [{}])[0]
                items = search_result.get('item', [])
                
                if items:
                    print(f"Finding API成功: {len(items)}件取得", file=sys.stderr)
                    return self._format_finding_results(items, exchange_rate)
            
            print(f"Finding API失敗: {response.status_code}", file=sys.stderr)
            return []
            
        except Exception as e:
            print(f"Finding API例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_improved_scraping(self, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """改良されたWebスクレイピング"""
        try:
            print(f"改良スクレイピング試行: {keyword}", file=sys.stderr)
            
            # 複数のeBay検索URLを試行
            search_urls = [
                f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}&_sacat=0&_sop=15&LH_BIN=1",
                f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}&_sacat=0&_sop=1",
                f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}&_sacat=0"
            ]
            
            for search_url in search_urls:
                try:
                    response = self.session.get(search_url, timeout=15)
                    
                    if response.status_code == 200:
                        results = self._extract_from_improved_html(response.text, keyword, limit, exchange_rate)
                        if results:
                            return results
                
                except Exception:
                    continue
            
            return []
            
        except Exception as e:
            print(f"改良スクレイピング例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_mobile_api(self, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """モバイル版APIを試行"""
        try:
            print(f"モバイルAPI試行: {keyword}", file=sys.stderr)
            
            # モバイル用ヘッダー
            mobile_headers = self.headers.copy()
            mobile_headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
            
            # モバイル版eBayにアクセス
            search_url = f"https://m.ebay.com/sch/i.html?_nkw={quote(keyword)}"
            response = self.session.get(search_url, headers=mobile_headers, timeout=15)
            
            if response.status_code == 200:
                return self._extract_from_mobile_html(response.text, keyword, limit, exchange_rate)
            
            return []
            
        except Exception as e:
            print(f"モバイルAPI例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_from_improved_html(self, html: str, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """改良されたHTMLからの商品データ抽出"""
        try:
            items = []
            
            # より詳細なパターンマッチング
            patterns = {
                'title': [
                    r'<h3[^>]*class="[^"]*s-item__title[^"]*"[^>]*>([^<]+)</h3>',
                    r'<a[^>]*class="[^"]*s-item__link[^"]*"[^>]*title="([^"]+)"',
                    r'data-testid="item-title"[^>]*>([^<]+)<'
                ],
                'price': [
                    r'<span[^>]*class="[^"]*s-item__price[^"]*"[^>]*>\$([0-9,]+\.?[0-9]*)</span>',
                    r'<span[^>]*class="[^"]*notranslate[^"]*"[^>]*>\$([0-9,]+\.?[0-9]*)</span>',
                    r'data-testid="item-price"[^>]*>[^$]*\$([0-9,]+\.?[0-9]*)'
                ],
                'url': [
                    r'<a[^>]*href="([^"]*)" class="[^"]*s-item__link[^"]*"',
                    r'<a[^>]*class="[^"]*s-item__link[^"]*"[^>]*href="([^"]*)"',
                    r'data-testid="item-link"[^>]*href="([^"]*)"'
                ],
                'image': [
                    r'<img[^>]*src="([^"]*)"[^>]*class="[^"]*s-item__image[^"]*"',
                    r'<img[^>]*class="[^"]*s-item__image[^"]*"[^>]*src="([^"]*)"'
                ]
            }
            
            # 各パターンを試行
            for pattern_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        if pattern_type == 'title':
                            titles = matches
                        elif pattern_type == 'price':
                            prices = matches
                        elif pattern_type == 'url':
                            urls = matches
                        elif pattern_type == 'image':
                            images = matches
                        break
            
            # データが見つからない場合は別のアプローチ
            if 'titles' not in locals():
                # JSONデータを探す
                json_pattern = r'<script[^>]*>.*?({.*?"items".*?}).*?</script>'
                json_matches = re.findall(json_pattern, html, re.DOTALL)
                
                for json_str in json_matches:
                    try:
                        data = json.loads(json_str)
                        extracted_items = self._extract_from_json_data(data, keyword, limit, exchange_rate)
                        if extracted_items:
                            return extracted_items
                    except json.JSONDecodeError:
                        continue
            
            # 通常のパターンマッチング結果を処理
            if 'titles' in locals() and 'prices' in locals():
                min_length = min(len(titles), len(prices), limit)
                
                for i in range(min_length):
                    try:
                        price_usd = float(prices[i].replace(',', ''))
                        price_jpy = int(price_usd * exchange_rate)
                        
                        url = urls[i] if i < len(urls) else ""
                        if url and not url.startswith('http'):
                            url = f"https://www.ebay.com{url}"
                        
                        item = {
                            "title": titles[i].strip(),
                            "name": titles[i].strip(),
                            "price": price_jpy,
                            "url": url,
                            "image_url": images[i] if i < len(images) else "",
                            "condition": "Used",
                            "seller": "eBay Seller",
                            "status": "active",
                            "sold_date": None,
                            "currency": "JPY",
                            "exchange_rate": exchange_rate,
                            "shipping_fee": 0,
                            "total_price": price_jpy,
                            "item_id": self._extract_item_id_from_url(url)
                        }
                        
                        if self._validate_real_item(item):
                            items.append(item)
                            
                    except Exception as e:
                        print(f"商品データ作成エラー: {str(e)}", file=sys.stderr)
                        continue
            
            return items
            
        except Exception as e:
            print(f"改良HTML抽出例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_from_mobile_html(self, html: str, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """モバイル版HTMLからの商品データ抽出"""
        try:
            items = []
            
            # モバイル版のパターン
            title_pattern = r'<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>'
            price_pattern = r'<span[^>]*class="[^"]*price[^"]*"[^>]*>\$([0-9,]+\.?[0-9]*)</span>'
            url_pattern = r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*item[^"]*"'
            
            titles = re.findall(title_pattern, html, re.IGNORECASE)
            prices = re.findall(price_pattern, html, re.IGNORECASE)
            urls = re.findall(url_pattern, html, re.IGNORECASE)
            
            min_length = min(len(titles), len(prices), len(urls), limit)
            
            for i in range(min_length):
                try:
                    price_usd = float(prices[i].replace(',', ''))
                    price_jpy = int(price_usd * exchange_rate)
                    
                    url = urls[i]
                    if not url.startswith('http'):
                        url = f"https://www.ebay.com{url}"
                    
                    item = {
                        "title": titles[i].strip(),
                        "name": titles[i].strip(),
                        "price": price_jpy,
                        "url": url,
                        "image_url": "",
                        "condition": "Used",
                        "seller": "eBay Seller",
                        "status": "active",
                        "sold_date": None,
                        "currency": "JPY",
                        "exchange_rate": exchange_rate,
                        "shipping_fee": 0,
                        "total_price": price_jpy,
                        "item_id": self._extract_item_id_from_url(url)
                    }
                    
                    if self._validate_real_item(item):
                        items.append(item)
                        
                except Exception:
                    continue
            
            return items
            
        except Exception as e:
            print(f"モバイルHTML抽出例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_from_json_data(self, data: dict, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """JSONデータから商品情報を抽出"""
        items = []
        
        def search_recursive(obj):
            if isinstance(obj, dict):
                # 商品データらしいオブジェクトを探す
                if "title" in obj and "price" in obj and "itemId" in obj:
                    formatted_item = self._format_json_item(obj, exchange_rate)
                    if formatted_item and self._validate_real_item(formatted_item):
                        items.append(formatted_item)
                        if len(items) >= limit:
                            return
                
                # 再帰的に探索
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        search_recursive(value)
                        if len(items) >= limit:
                            break
            
            elif isinstance(obj, list):
                for item in obj:
                    search_recursive(item)
                    if len(items) >= limit:
                        break
        
        search_recursive(data)
        return items
    
    def _format_json_item(self, item: dict, exchange_rate: float) -> Dict[str, Any]:
        """JSONアイテムをフォーマット"""
        try:
            price_usd = float(item.get("price", {}).get("value", 0))
            price_jpy = int(price_usd * exchange_rate)
            
            return {
                "title": item.get("title", ""),
                "name": item.get("title", ""),
                "price": price_jpy,
                "url": item.get("itemWebUrl", ""),
                "image_url": item.get("image", {}).get("imageUrl", ""),
                "condition": item.get("condition", "Used"),
                "seller": item.get("seller", {}).get("username", "eBay Seller"),
                "status": "active",
                "sold_date": None,
                "currency": "JPY",
                "exchange_rate": exchange_rate,
                "shipping_fee": 0,
                "total_price": price_jpy,
                "item_id": item.get("itemId", "")
            }
        except Exception:
            return None
    
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
                
                if self._validate_real_item(formatted_item):
                    formatted_results.append(formatted_item)
                    
            except Exception as e:
                print(f"Finding結果フォーマットエラー: {str(e)}", file=sys.stderr)
                continue
        
        return formatted_results
    
    def _extract_item_id_from_url(self, url: str) -> str:
        """URLからアイテムIDを抽出"""
        try:
            match = re.search(r'/itm/[^/]*?(\d{12,})', url)
            if match:
                return match.group(1)
            
            match = re.search(r'(\d{10,})(?:\?|$)', url)
            if match:
                return match.group(1)
            
            return ""
        except Exception:
            return ""
    
    def _validate_real_item(self, item: dict) -> bool:
        """実際のアイテムかどうかを検証"""
        required_fields = ["title", "price"]
        for field in required_fields:
            if not item.get(field):
                return False
        
        if item.get("price", 0) <= 0:
            return False
        
        title = item.get("title", "")
        if len(title) < 5 or "sample" in title.lower() or "test" in title.lower():
            return False
        
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_ebay_working.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"eBay実働検索開始: {keyword}, limit: {limit}", file=sys.stderr)
    
    client = EbayWorkingClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()
