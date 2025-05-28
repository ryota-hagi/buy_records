#!/usr/bin/env python3
"""
改善されたeBay検索スクリプト
Finding APIの制限を回避し、Webスクレイピングを強化
"""

import sys
import json
import requests
import time
import re
import os
from urllib.parse import quote
from typing import List, Dict, Any
from bs4 import BeautifulSoup

class EbayImprovedClient:
    """改善されたeBayクライアント"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com"
        
        # より効果的なヘッダー設定
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 為替レート（デフォルト）
        self.exchange_rate = 142.73
    
    def get_exchange_rate(self) -> float:
        """為替レートを取得"""
        try:
            response = self.session.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
            if response.status_code == 200:
                data = response.json()
                rate = data.get('rates', {}).get('JPY', 142.73)
                print(f"為替レート取得成功: 1 USD = {rate} JPY", file=sys.stderr)
                return float(rate)
        except Exception as e:
            print(f"為替レート取得失敗: {str(e)}", file=sys.stderr)
        
        print(f"デフォルト為替レートを使用: 1 USD = {self.exchange_rate} JPY", file=sys.stderr)
        return self.exchange_rate
    
    def translate_to_english(self, japanese_text: str) -> str:
        """日本語を英語に翻訳"""
        try:
            # Google翻訳APIを使用
            import subprocess
            result = subprocess.run([
                'python', 'scripts/translate_for_ebay.py', japanese_text
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                translated = result.stdout.strip()
                print(f"翻訳成功: {japanese_text} -> {translated}", file=sys.stderr)
                return translated
            else:
                print(f"翻訳失敗: {result.stderr}", file=sys.stderr)
                
        except Exception as e:
            print(f"翻訳例外: {str(e)}", file=sys.stderr)
        
        # フォールバック: 基本的な単語置換
        fallback_translations = {
            'サントリー': 'Suntory',
            '緑茶': 'Green Tea',
            '伊右衛門': 'Iyemon',
            'ペット': 'PET bottle',
            'ボトル': 'bottle',
            'ml': 'ml',
            'Nintendo': 'Nintendo',
            'Switch': 'Switch',
            'iPhone': 'iPhone',
            'Sony': 'Sony',
            'PlayStation': 'PlayStation'
        }
        
        translated = japanese_text
        for jp, en in fallback_translations.items():
            translated = translated.replace(jp, en)
        
        print(f"フォールバック翻訳: {japanese_text} -> {translated}", file=sys.stderr)
        return translated
    
    def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        eBayから商品データを検索（改善版）
        """
        try:
            print(f"eBay改善検索開始: {keyword}", file=sys.stderr)
            
            # 為替レートを取得
            exchange_rate = self.get_exchange_rate()
            
            # 日本語キーワードの場合は英語に翻訳
            search_keyword = keyword
            if self._contains_japanese(keyword):
                search_keyword = self.translate_to_english(keyword)
            
            # 複数の検索戦略を試行
            results = []
            
            # 戦略1: 基本検索
            results = self._search_basic(search_keyword, limit, exchange_rate)
            if len(results) >= 5:
                print(f"基本検索成功: {len(results)}件取得", file=sys.stderr)
                return results[:limit]
            
            # 戦略2: カテゴリ指定検索
            category_results = self._search_with_category(search_keyword, limit, exchange_rate)
            results.extend(category_results)
            if len(results) >= 5:
                print(f"カテゴリ検索成功: {len(results)}件取得", file=sys.stderr)
                return results[:limit]
            
            # 戦略3: 異なるソート順での検索
            sort_results = self._search_with_different_sort(search_keyword, limit, exchange_rate)
            results.extend(sort_results)
            if len(results) >= 5:
                print(f"ソート検索成功: {len(results)}件取得", file=sys.stderr)
                return results[:limit]
            
            # 戦略4: キーワード変更検索
            if len(results) < 5:
                alternative_keywords = self._generate_alternative_keywords(search_keyword)
                for alt_keyword in alternative_keywords:
                    alt_results = self._search_basic(alt_keyword, limit, exchange_rate)
                    results.extend(alt_results)
                    if len(results) >= 5:
                        break
            
            # 重複除去
            unique_results = self._remove_duplicates(results)
            
            print(f"最終検索結果: {len(unique_results)}件取得", file=sys.stderr)
            return unique_results[:limit]
                
        except Exception as e:
            print(f"eBay検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _contains_japanese(self, text: str) -> bool:
        """日本語文字が含まれているかチェック"""
        japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
        return bool(japanese_pattern.search(text))
    
    def _search_basic(self, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """基本検索"""
        try:
            print(f"基本検索実行: {keyword}", file=sys.stderr)
            
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}&_sacat=0&_sop=15&LH_BIN=1"
            response = self.session.get(search_url, timeout=20)
            
            if response.status_code == 200:
                return self._extract_items_from_html(response.text, keyword, limit, exchange_rate)
            
            return []
            
        except Exception as e:
            print(f"基本検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _search_with_category(self, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """カテゴリ指定検索"""
        try:
            print(f"カテゴリ検索実行: {keyword}", file=sys.stderr)
            
            # 人気カテゴリでの検索
            categories = [
                "293",   # Consumer Electronics
                "58058", # Cell Phones & Smartphones
                "139973" # Video Games & Consoles
            ]
            
            results = []
            for category in categories:
                search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}&_sacat={category}&_sop=15&LH_BIN=1"
                response = self.session.get(search_url, timeout=20)
                
                if response.status_code == 200:
                    category_results = self._extract_items_from_html(response.text, keyword, limit//3, exchange_rate)
                    results.extend(category_results)
                    
                time.sleep(1)  # レート制限対策
            
            return results
            
        except Exception as e:
            print(f"カテゴリ検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _search_with_different_sort(self, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """異なるソート順での検索"""
        try:
            print(f"ソート検索実行: {keyword}", file=sys.stderr)
            
            # 異なるソート順
            sort_orders = [
                "12",  # Time: ending soonest
                "1",   # Time: newly listed
                "16"   # Distance: nearest first
            ]
            
            results = []
            for sort_order in sort_orders:
                search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}&_sacat=0&_sop={sort_order}&LH_BIN=1"
                response = self.session.get(search_url, timeout=20)
                
                if response.status_code == 200:
                    sort_results = self._extract_items_from_html(response.text, keyword, limit//3, exchange_rate)
                    results.extend(sort_results)
                    
                time.sleep(1)  # レート制限対策
            
            return results
            
        except Exception as e:
            print(f"ソート検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _generate_alternative_keywords(self, keyword: str) -> List[str]:
        """代替キーワードを生成"""
        alternatives = []
        
        # 基本的な変形
        alternatives.append(keyword.replace(" ", "+"))
        alternatives.append(keyword.replace(" ", "-"))
        
        # ブランド名の抽出と検索
        brands = ["Nintendo", "Sony", "Apple", "Samsung", "Suntory"]
        for brand in brands:
            if brand.lower() in keyword.lower():
                alternatives.append(brand)
        
        # 商品タイプの抽出
        product_types = ["Switch", "iPhone", "PlayStation", "Green Tea"]
        for product_type in product_types:
            if product_type.lower() in keyword.lower():
                alternatives.append(product_type)
        
        return alternatives[:3]  # 最大3つの代替キーワード
    
    def _extract_items_from_html(self, html: str, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """HTMLから商品データを抽出（BeautifulSoup使用）"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            items = []
            
            # 商品アイテムを検索
            item_containers = soup.find_all('div', class_=re.compile(r's-item__wrapper'))
            
            if not item_containers:
                # 別のセレクタを試行
                item_containers = soup.find_all('div', class_=re.compile(r'srp-results'))
                if item_containers:
                    item_containers = item_containers[0].find_all('div', class_=re.compile(r's-item'))
            
            print(f"見つかったアイテムコンテナ数: {len(item_containers)}", file=sys.stderr)
            
            for container in item_containers[:limit]:
                try:
                    item = self._extract_single_item(container, exchange_rate)
                    if item and self._validate_item(item):
                        items.append(item)
                        
                except Exception as e:
                    print(f"アイテム抽出エラー: {str(e)}", file=sys.stderr)
                    continue
            
            print(f"抽出成功アイテム数: {len(items)}", file=sys.stderr)
            return items
            
        except Exception as e:
            print(f"HTML解析例外: {str(e)}", file=sys.stderr)
            return []
    
    def _extract_single_item(self, container, exchange_rate: float) -> Dict[str, Any]:
        """単一アイテムの抽出"""
        # タイトル抽出（複数のセレクタを試行）
        title = ""
        title_selectors = [
            'h3.s-item__title',
            '.s-item__title',
            'h3[role="heading"]',
            '.it-ttl',
            'a.s-item__link'
        ]
        
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                # 不要なテキストを除去
                title = title.replace("Opens in a new window or tab", "").strip()
                title = title.replace("Shop on eBay", "").strip()
                if title and len(title) > 5:
                    break
        
        # URL抽出
        url = ""
        link_elem = container.find('a', class_=re.compile(r's-item__link'))
        if link_elem:
            url = link_elem.get('href', '')
        
        # 価格抽出（複数のセレクタを試行）
        price_usd = 0.0
        price_selectors = [
            '.s-item__price .notranslate',
            '.s-item__price',
            '.u-flL.condText',
            '.it-price'
        ]
        
        for selector in price_selectors:
            price_elem = container.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_usd = self._extract_price_from_text(price_text)
                if price_usd > 0:
                    break
        
        # 画像URL抽出
        image_url = ""
        img_elem = container.find('img')
        if img_elem:
            image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
        
        # 送料抽出
        shipping_usd = 0.0
        shipping_selectors = [
            '.s-item__shipping',
            '.s-item__logisticsCost',
            '.vi-price .u-flL.condText'
        ]
        
        for selector in shipping_selectors:
            shipping_elem = container.select_one(selector)
            if shipping_elem:
                shipping_text = shipping_elem.get_text(strip=True)
                shipping_usd = self._extract_shipping_from_text(shipping_text)
                break
        
        # JPY変換
        price_jpy = int(price_usd * exchange_rate) if price_usd > 0 else 0
        shipping_jpy = int(shipping_usd * exchange_rate) if shipping_usd > 0 else 0
        
        return {
            "title": title,
            "name": title,
            "price": price_jpy,
            "url": url if url.startswith('http') else f"https://www.ebay.com{url}",
            "image_url": image_url,
            "condition": "Used",
            "seller": "eBay Seller",
            "status": "active",
            "sold_date": None,
            "currency": "JPY",
            "exchange_rate": exchange_rate,
            "shipping_fee": shipping_jpy,
            "total_price": price_jpy + shipping_jpy,
            "item_id": self._extract_item_id_from_url(url)
        }
    
    def _extract_price_from_text(self, price_text: str) -> float:
        """価格テキストから数値を抽出"""
        try:
            # $記号と数字を抽出
            price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', price_text)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                return float(price_str)
            return 0.0
        except Exception:
            return 0.0
    
    def _extract_shipping_from_text(self, shipping_text: str) -> float:
        """送料テキストから数値を抽出"""
        try:
            if 'free' in shipping_text.lower():
                return 0.0
            
            shipping_match = re.search(r'\$([0-9,]+\.?[0-9]*)', shipping_text)
            if shipping_match:
                shipping_str = shipping_match.group(1).replace(',', '')
                return float(shipping_str)
            return 0.0
        except Exception:
            return 0.0
    
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
    
    def _validate_item(self, item: dict) -> bool:
        """アイテムの妥当性をチェック"""
        # 必須フィールドの確認
        if not item.get("title") or len(item["title"]) < 3:
            return False
        
        if not item.get("url") or not item["url"].startswith("http"):
            return False
        
        if item.get("price", 0) <= 0:
            return False
        
        # 広告・スパムフィルタ
        title_lower = item["title"].lower()
        
        # eBay広告をフィルタリング
        ad_keywords = [
            "shop on ebay",
            "opens in a new window",
            "new window or tab",
            "advertisement",
            "sponsored",
            "test", 
            "sample", 
            "dummy", 
            "fake"
        ]
        
        for ad_keyword in ad_keywords:
            if ad_keyword in title_lower:
                return False
        
        # 空のタイトルや短すぎるタイトルをフィルタリング
        if len(item["title"].strip()) < 10:
            return False
        
        # URLが実際の商品ページかチェック
        url = item.get("url", "")
        if "/itm/" not in url and "item" not in url:
            return False
        
        return True
    
    def _remove_duplicates(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複アイテムを除去"""
        seen = set()
        unique_items = []
        
        for item in items:
            # タイトルと価格の組み合わせで重複判定
            key = f"{item.get('title', '').lower()}-{item.get('price', 0)}"
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        return unique_items

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_ebay_improved.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"eBay改善検索開始: {keyword}, limit: {limit}", file=sys.stderr)
    
    client = EbayImprovedClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()
