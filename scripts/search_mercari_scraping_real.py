#!/usr/bin/env python3
"""
メルカリ実際のWebスクレイピング検索スクリプト
実際のメルカリWebサイトから商品データを取得します。
"""

import sys
import json
import requests
import time
import re
from urllib.parse import quote
from typing import List, Dict, Any
import random
from bs4 import BeautifulSoup

class MercariScrapingClient:
    """メルカリWebスクレイピングクライアント"""
    
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
        メルカリから実際の商品データを検索
        """
        try:
            print(f"メルカリWebスクレイピング検索開始: {keyword}", file=sys.stderr)
            
            # 複数の検索方法を試行
            results = []
            
            # 方法1: 通常の検索ページ
            results = self._try_normal_search(keyword, limit)
            if results:
                print(f"通常検索成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 方法2: カテゴリ検索
            results = self._try_category_search(keyword, limit)
            if results:
                print(f"カテゴリ検索成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            # 方法3: 売り切れ商品も含む検索
            results = self._try_sold_search(keyword, limit)
            if results:
                print(f"売り切れ含む検索成功: {len(results)}件取得", file=sys.stderr)
                return results
            
            print(f"全ての検索方法が失敗しました", file=sys.stderr)
            return []
                
        except Exception as e:
            print(f"メルカリ検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_normal_search(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """通常の検索を試行"""
        try:
            print(f"通常検索試行: {keyword}", file=sys.stderr)
            
            # 検索URLを構築
            search_url = f"{self.base_url}/search?keyword={quote(keyword)}&status=on_sale"
            
            # ランダムな遅延を追加
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                return self._extract_from_html(response.text, keyword, limit)
            
            print(f"通常検索失敗: {response.status_code}", file=sys.stderr)
            return []
            
        except Exception as e:
            print(f"通常検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_category_search(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """カテゴリ検索を試行"""
        try:
            print(f"カテゴリ検索試行: {keyword}", file=sys.stderr)
            
            # ゲーム関連のカテゴリIDを使用
            category_ids = ["5", "685", "1328"]  # ゲーム関連カテゴリ
            
            for category_id in category_ids:
                search_url = f"{self.base_url}/search?keyword={quote(keyword)}&category_root={category_id}&status=on_sale"
                
                time.sleep(random.uniform(1, 2))
                response = self.session.get(search_url, timeout=20)
                
                if response.status_code == 200:
                    results = self._extract_from_html(response.text, keyword, limit)
                    if results:
                        return results
            
            return []
            
        except Exception as e:
            print(f"カテゴリ検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _try_sold_search(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """売り切れ商品も含む検索を試行"""
        try:
            print(f"売り切れ含む検索試行: {keyword}", file=sys.stderr)
            
            # 売り切れ商品も含む検索
            search_url = f"{self.base_url}/search?keyword={quote(keyword)}&status=sold_out"
            
            time.sleep(random.uniform(1, 3))
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                return self._extract_from_html(response.text, keyword, limit, sold=True)
            
            return []
            
        except Exception as e:
            print(f"売り切れ含む検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_from_html(self, html: str, keyword: str, limit: int, sold: bool = False) -> List[Dict[str, Any]]:
        """HTMLから商品データを抽出"""
        try:
            items = []
            
            # BeautifulSoupを使用してHTMLを解析
            soup = BeautifulSoup(html, 'html.parser')
            
            # 商品アイテムを探す
            item_selectors = [
                'mer-item-thumbnail',
                '[data-testid="item-cell"]',
                '.item-cell',
                '.item-box',
                'article'
            ]
            
            for selector in item_selectors:
                item_elements = soup.select(selector)
                if item_elements:
                    print(f"商品要素発見: {len(item_elements)}件 (セレクタ: {selector})", file=sys.stderr)
                    break
            
            if not item_elements:
                # Next.jsのデータを探す
                return self._extract_from_nextjs_data(html, keyword, limit, sold)
            
            for element in item_elements[:limit]:
                try:
                    item_data = self._extract_item_from_element(element, sold)
                    if item_data and self._validate_item(item_data):
                        items.append(item_data)
                        
                except Exception as e:
                    print(f"商品要素解析エラー: {str(e)}", file=sys.stderr)
                    continue
            
            return items
            
        except Exception as e:
            print(f"HTML抽出例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_from_nextjs_data(self, html: str, keyword: str, limit: int, sold: bool = False) -> List[Dict[str, Any]]:
        """Next.jsのデータから商品情報を抽出"""
        try:
            items = []
            
            # Next.jsのデータを探す
            patterns = [
                r'window\.__NEXT_DATA__\s*=\s*({.*?});',
                r'"props":\s*({.*?"pageProps".*?})',
                r'"items":\s*(\[.*?\])',
                r'"searchResult":\s*({.*?})'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        extracted_items = self._extract_items_from_data(data, keyword, limit, sold)
                        if extracted_items:
                            items.extend(extracted_items)
                            if len(items) >= limit:
                                break
                    except json.JSONDecodeError:
                        continue
                
                if items:
                    break
            
            # 正規表現でも商品データを探す
            if not items:
                items = self._extract_with_regex(html, keyword, limit, sold)
            
            return items[:limit]
            
        except Exception as e:
            print(f"Next.jsデータ抽出例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_with_regex(self, html: str, keyword: str, limit: int, sold: bool = False) -> List[Dict[str, Any]]:
        """正規表現で商品データを抽出"""
        try:
            items = []
            
            # 商品名のパターン
            title_patterns = [
                r'<h3[^>]*>([^<]*' + re.escape(keyword.split()[0]) + r'[^<]*)</h3>',
                r'title="([^"]*' + re.escape(keyword.split()[0]) + r'[^"]*)"',
                r'alt="([^"]*' + re.escape(keyword.split()[0]) + r'[^"]*)"'
            ]
            
            # 価格のパターン
            price_patterns = [
                r'¥([0-9,]+)',
                r'￥([0-9,]+)',
                r'"price":([0-9]+)',
                r'data-price="([0-9]+)"'
            ]
            
            # URLのパターン
            url_patterns = [
                r'href="(/item/[^"]+)"',
                r'"itemUrl":"([^"]+)"',
                r'data-href="([^"]+)"'
            ]
            
            # 各パターンを試行
            titles = []
            prices = []
            urls = []
            
            for pattern in title_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                if matches:
                    titles = matches
                    break
            
            for pattern in price_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    prices = [m.replace(',', '') for m in matches]
                    break
            
            for pattern in url_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    urls = matches
                    break
            
            # データを組み合わせて商品を作成
            min_length = min(len(titles), len(prices), limit)
            
            for i in range(min_length):
                try:
                    price = int(prices[i]) if i < len(prices) else 0
                    url = urls[i] if i < len(urls) else ""
                    
                    if url and not url.startswith('http'):
                        url = f"{self.base_url}{url}"
                    
                    item = {
                        "title": titles[i].strip(),
                        "name": titles[i].strip(),
                        "price": price,
                        "url": url,
                        "image_url": "",
                        "condition": "中古",
                        "seller": "メルカリ出品者",
                        "status": "sold" if sold else "active",
                        "sold_date": None,
                        "currency": "JPY",
                        "shipping_fee": 0,
                        "total_price": price,
                        "item_id": self._extract_item_id_from_url(url)
                    }
                    
                    if self._validate_item(item):
                        items.append(item)
                        
                except Exception:
                    continue
            
            return items
            
        except Exception as e:
            print(f"正規表現抽出例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_item_from_element(self, element, sold: bool = False) -> Dict[str, Any]:
        """HTML要素から商品データを抽出"""
        try:
            # タイトルを取得
            title_selectors = ['h3', '[data-testid="item-name"]', '.item-name', 'img[alt]']
            title = ""
            
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True) or title_elem.get('alt', '')
                    if title:
                        break
            
            # 価格を取得
            price_selectors = ['[data-testid="item-price"]', '.price', '.item-price']
            price = 0
            
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'([0-9,]+)', price_text)
                    if price_match:
                        price = int(price_match.group(1).replace(',', ''))
                        break
            
            # URLを取得
            url = ""
            link_elem = element.select_one('a[href]')
            if link_elem:
                url = link_elem.get('href', '')
                if url and not url.startswith('http'):
                    url = f"{self.base_url}{url}"
            
            # 画像URLを取得
            image_url = ""
            img_elem = element.select_one('img[src]')
            if img_elem:
                image_url = img_elem.get('src', '')
            
            return {
                "title": title,
                "name": title,
                "price": price,
                "url": url,
                "image_url": image_url,
                "condition": "中古",
                "seller": "メルカリ出品者",
                "status": "sold" if sold else "active",
                "sold_date": None,
                "currency": "JPY",
                "shipping_fee": 0,
                "total_price": price,
                "item_id": self._extract_item_id_from_url(url)
            }
            
        except Exception as e:
            print(f"要素抽出エラー: {str(e)}", file=sys.stderr)
            return None
    
    def _extract_items_from_data(self, data: dict, keyword: str, limit: int, sold: bool = False) -> List[Dict[str, Any]]:
        """データ構造から商品情報を抽出"""
        items = []
        
        def search_recursive(obj, path=""):
            if isinstance(obj, dict):
                # 商品データらしいオブジェクトを探す
                if "id" in obj and "name" in obj and "price" in obj:
                    formatted_item = self._format_item_data(obj, sold)
                    if formatted_item and self._validate_item(formatted_item):
                        items.append(formatted_item)
                        if len(items) >= limit:
                            return
                
                # 再帰的に探索
                for key, value in obj.items():
                    if key in ["items", "data", "results", "products", "searchResult"]:
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
    
    def _format_item_data(self, item: dict, sold: bool = False) -> Dict[str, Any]:
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
                url = f"{self.base_url}/item/{item_id}"
            elif "url" in item:
                url = item["url"]
            
            # 商品名の取得
            title = item.get("name", item.get("title", ""))
            
            return {
                "title": title,
                "name": title,
                "price": price,
                "url": url,
                "image_url": item.get("thumbnails", [{}])[0].get("url", "") if item.get("thumbnails") else "",
                "condition": "中古",
                "seller": "メルカリ出品者",
                "status": "sold" if sold else "active",
                "sold_date": None,
                "currency": "JPY",
                "item_id": str(item_id),
                "shipping_fee": 0,
                "total_price": price
            }
        except Exception as e:
            print(f"データフォーマットエラー: {str(e)}", file=sys.stderr)
            return None
    
    def _extract_item_id_from_url(self, url: str) -> str:
        """URLからアイテムIDを抽出"""
        try:
            match = re.search(r'/item/([^/?]+)', url)
            if match:
                return match.group(1)
            return ""
        except Exception:
            return ""
    
    def _validate_item(self, item: dict) -> bool:
        """実際のアイテムかどうかを検証"""
        # 必須フィールドの存在確認
        if not item.get("title") or not item.get("price"):
            return False
        
        # 価格が0以上であることを確認
        if item.get("price", 0) <= 0:
            return False
        
        # タイトルが実際の商品名らしいことを確認
        title = item.get("title", "")
        if len(title) < 3:
            return False
        
        # サンプルデータでないことを確認
        if "sample" in title.lower() or "test" in title.lower():
            return False
        
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_mercari_scraping_real.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"メルカリWebスクレイピング検索開始: {keyword}, limit: {limit}", file=sys.stderr)
    
    client = MercariScrapingClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()
