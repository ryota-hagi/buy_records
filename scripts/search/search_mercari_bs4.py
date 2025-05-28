#!/usr/bin/env python3
"""
メルカリBeautifulSoupスクレイピング検索スクリプト
BeautifulSoupとrequestsを使用してメルカリから商品データを取得します。
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
from dotenv import load_dotenv
import os

# .envファイルを読み込む
load_dotenv()

class MercariBS4ScrapingClient:
    """BeautifulSoupを使用したメルカリスクレイピングクライアント"""
    
    def __init__(self):
        self.base_url = "https://jp.mercari.com"
        self.session = requests.Session()
        
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
        
        self.session.headers.update(self.headers)
    
    def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        メルカリから商品データを検索
        """
        try:
            print(f"メルカリBS4スクレイピング開始: {keyword}", file=sys.stderr)
            
            # 検索URL（価格の安い順）
            search_url = f"{self.base_url}/search?keyword={quote(keyword)}&status=on_sale&sort=price&order=asc"
            
            print(f"検索URL: {search_url}", file=sys.stderr)
            
            # リクエスト前に少し待機
            time.sleep(random.uniform(1, 3))
            
            # クッキーをセッションに保持
            response = self.session.get(search_url, timeout=300)
            
            if response.status_code != 200:
                print(f"HTTPエラー: {response.status_code}", file=sys.stderr)
                return []
            
            print(f"レスポンス取得成功: {len(response.text)} bytes", file=sys.stderr)
            
            # BeautifulSoupでHTMLを解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Next.jsのデータを探す
            items = self._extract_from_nextjs_data(soup, keyword, limit)
            
            if not items:
                # 別の方法で商品データを抽出
                items = self._extract_from_html_structure(soup, keyword, limit)
            
            if not items:
                print("商品データが見つかりませんでした", file=sys.stderr)
                # HTMLの構造を確認
                self._debug_html_structure(soup)
            
            return items
            
        except Exception as e:
            print(f"検索エラー: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_from_nextjs_data(self, soup: BeautifulSoup, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """Next.jsのデータから商品を抽出"""
        items = []
        
        try:
            # __NEXT_DATA__スクリプトタグを探す
            script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
            
            for script in script_tags:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        
                        # データを再帰的に探索
                        items_data = self._find_items_in_json(data)
                        
                        if items_data:
                            print(f"Next.jsデータから{len(items_data)}件の商品を発見", file=sys.stderr)
                            
                            for idx, item_data in enumerate(items_data[:limit]):
                                try:
                                    formatted_item = self._format_item_data(item_data, keyword)
                                    if formatted_item and self._validate_item(formatted_item):
                                        items.append(formatted_item)
                                        print(f"商品{idx+1}: {formatted_item['title'][:30]}... - ¥{formatted_item['price']:,}", file=sys.stderr)
                                except Exception as e:
                                    print(f"商品データ変換エラー: {str(e)}", file=sys.stderr)
                                    continue
                            
                            break
                    
                    except json.JSONDecodeError as e:
                        print(f"JSON解析エラー: {str(e)}", file=sys.stderr)
                        continue
        
        except Exception as e:
            print(f"Next.jsデータ抽出エラー: {str(e)}", file=sys.stderr)
        
        return items
    
    def _extract_from_html_structure(self, soup: BeautifulSoup, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """HTML構造から商品を抽出"""
        items = []
        
        try:
            # 様々なセレクタで商品要素を探す
            selectors = [
                'a[data-testid="item-cell"]',
                'a[data-location="item_list:item"]',
                'article[data-testid="item-cell"]',
                'div[data-testid="item-cell"]',
                'mer-item-thumbnail',
                '.merItemThumbnail',
                'a[href^="/item/m"]',
                '[class*="ItemThumbnail"]',
                '[class*="itemCard"]',
                '[class*="item-cell"]'
            ]
            
            item_elements = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"セレクタ '{selector}' で{len(elements)}個の要素を発見", file=sys.stderr)
                    item_elements = elements
                    break
            
            if not item_elements:
                # リンクタグから商品を探す
                all_links = soup.find_all('a', href=re.compile(r'/item/m\d+'))
                if all_links:
                    print(f"リンクタグから{len(all_links)}個の商品リンクを発見", file=sys.stderr)
                    item_elements = all_links
            
            # 商品データを抽出
            for idx, element in enumerate(item_elements[:limit]):
                try:
                    item_data = self._extract_item_from_element(element)
                    if item_data:
                        items.append(item_data)
                        print(f"商品{idx+1}: {item_data['title'][:30]}... - ¥{item_data['price']:,}", file=sys.stderr)
                except Exception as e:
                    print(f"要素抽出エラー: {str(e)}", file=sys.stderr)
                    continue
        
        except Exception as e:
            print(f"HTML構造抽出エラー: {str(e)}", file=sys.stderr)
        
        return items
    
    def _extract_item_from_element(self, element) -> Dict[str, Any]:
        """HTML要素から商品データを抽出"""
        try:
            # URLを取得
            if element.name == 'a':
                url_path = element.get('href', '')
            else:
                link = element.find('a')
                url_path = link.get('href', '') if link else ''
            
            if not url_path or not url_path.startswith('/item/'):
                return None
            
            # 商品IDを抽出
            item_id_match = re.search(r'/item/(m\d+)', url_path)
            if not item_id_match:
                return None
            
            item_id = item_id_match.group(1)
            url = f"https://jp.mercari.com{url_path}"
            
            # タイトルを探す
            title = ""
            title_selectors = [
                'span[data-testid="item-name"]',
                'p[data-testid="item-name"]',
                'div[class*="itemName"]',
                'span[class*="name"]',
                'p[class*="name"]'
            ]
            
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    break
            
            # aria-labelから取得を試みる
            if not title:
                aria_label = element.get('aria-label', '')
                if aria_label:
                    title = aria_label.split('¥')[0].strip()
            
            # 価格を探す
            price = 0
            price_selectors = [
                'span[data-testid="item-price"]',
                'p[data-testid="item-price"]',
                'div[class*="price"]',
                'span[class*="price"]'
            ]
            
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem and price_elem.text:
                    price_text = price_elem.text.strip()
                    price_match = re.search(r'([0-9,]+)', price_text)
                    if price_match:
                        price = int(price_match.group(1).replace(',', ''))
                        break
            
            # aria-labelから価格を取得
            if price == 0 and aria_label:
                price_match = re.search(r'¥([0-9,]+)', aria_label)
                if price_match:
                    price = int(price_match.group(1).replace(',', ''))
            
            # 画像URLを探す
            image_url = ""
            img_elem = element.find('img')
            if img_elem:
                image_url = img_elem.get('src', '')
                if not image_url:
                    image_url = img_elem.get('data-src', '')
            
            if title and price > 0:
                return {
                    "title": title,
                    "name": title,
                    "price": price,
                    "url": url,
                    "image_url": image_url,
                    "condition": "中古",
                    "seller": "メルカリ出品者",
                    "status": "active",
                    "sold_date": None,
                    "currency": "JPY",
                    "item_id": item_id,
                    "shipping_fee": 0,
                    "total_price": price
                }
            
            return None
            
        except Exception as e:
            print(f"要素データ抽出エラー: {str(e)}", file=sys.stderr)
            return None
    
    def _find_items_in_json(self, data: dict, path: str = "") -> list:
        """JSONデータから商品リストを再帰的に検索"""
        if isinstance(data, dict):
            # 商品リストのキーを探す
            for key in ['items', 'itemsData', 'searchResult', 'results', 'products', 'itemList', 'productList']:
                if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                    # 商品データっぽいかチェック
                    first_item = data[key][0]
                    if isinstance(first_item, dict) and any(k in first_item for k in ['id', 'itemId', 'productId']):
                        print(f"商品リスト発見: {path}.{key} ({len(data[key])}件)", file=sys.stderr)
                        return data[key]
            
            # 再帰的に探索
            for key, value in data.items():
                result = self._find_items_in_json(value, f"{path}.{key}")
                if result:
                    return result
        
        elif isinstance(data, list) and len(data) > 0:
            # リストの要素が商品データっぽいかチェック
            if isinstance(data[0], dict) and any(k in data[0] for k in ['id', 'itemId', 'productId']):
                if any(k in data[0] for k in ['price', 'itemPrice', 'productPrice']):
                    print(f"商品リスト発見: {path}[] ({len(data)}件)", file=sys.stderr)
                    return data
        
        return []
    
    def _format_item_data(self, item_data: dict, keyword: str) -> Dict[str, Any]:
        """商品データを統一フォーマットに変換"""
        try:
            # ID取得
            item_id = item_data.get('id') or item_data.get('itemId') or item_data.get('productId', '')
            
            # タイトル取得
            title = item_data.get('name') or item_data.get('itemName') or item_data.get('title', '')
            
            # 価格取得
            price = item_data.get('price') or item_data.get('itemPrice') or item_data.get('productPrice', 0)
            if isinstance(price, str):
                price = int(re.sub(r'[^0-9]', '', price))
            else:
                price = int(price)
            
            # URL構築
            url = item_data.get('url', '')
            if not url and item_id:
                url = f"https://jp.mercari.com/item/{item_id}"
            
            # 画像URL取得
            image_url = ""
            if 'thumbnails' in item_data and isinstance(item_data['thumbnails'], list) and item_data['thumbnails']:
                image_url = item_data['thumbnails'][0].get('url', '')
            elif 'thumbnail' in item_data:
                image_url = item_data['thumbnail']
            elif 'image' in item_data:
                image_url = item_data['image']
            elif 'imageUrl' in item_data:
                image_url = item_data['imageUrl']
            
            return {
                "search_term": keyword,
                "item_id": item_id,
                "title": title,
                "name": title,
                "price": price,
                "currency": "JPY",
                "status": "active",
                "sold_date": None,
                "condition": item_data.get('itemCondition', {}).get('name', '中古') if isinstance(item_data.get('itemCondition'), dict) else '中古',
                "url": url,
                "image_url": image_url,
                "seller": item_data.get('seller', {}).get('name', 'メルカリ出品者') if isinstance(item_data.get('seller'), dict) else 'メルカリ出品者',
                "shipping_fee": 0,
                "total_price": price
            }
            
        except Exception as e:
            print(f"商品データ変換エラー: {str(e)}", file=sys.stderr)
            return None
    
    def _validate_item(self, item: dict) -> bool:
        """商品データの妥当性をチェック"""
        if not item:
            return False
        
        # 必須フィールドの確認
        if not item.get("title") or len(item["title"]) < 3:
            return False
        
        if not item.get("url") or not item["url"].startswith("http"):
            return False
        
        if item.get("price", 0) <= 0:
            return False
        
        # モックデータのパターンをチェック
        mock_patterns = [
            "商品1", "商品2", "test", "mock", "sample", "dummy",
            "placeholder", "example"
        ]
        
        title_lower = item.get("title", "").lower()
        for pattern in mock_patterns:
            if pattern in title_lower:
                return False
        
        return True
    
    def _debug_html_structure(self, soup: BeautifulSoup):
        """HTMLの構造をデバッグ出力"""
        print("\n=== HTMLデバッグ情報 ===", file=sys.stderr)
        
        # title要素の内容
        title = soup.find('title')
        if title:
            print(f"ページタイトル: {title.text}", file=sys.stderr)
        
        # 主要なdiv要素のクラス名
        main_divs = soup.find_all('div', attrs={'class': True}, limit=20)
        unique_classes = set()
        for div in main_divs:
            classes = div.get('class', [])
            for cls in classes:
                if cls and not cls.startswith('sc-'):  # styled-componentsのクラスを除外
                    unique_classes.add(cls)
        
        print(f"主要なクラス名: {', '.join(list(unique_classes)[:20])}", file=sys.stderr)
        
        # data-testid属性を持つ要素
        testid_elements = soup.find_all(attrs={'data-testid': True}, limit=10)
        if testid_elements:
            print(f"data-testid要素: {[elem.get('data-testid') for elem in testid_elements]}", file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_mercari_bs4.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    client = MercariBS4ScrapingClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()