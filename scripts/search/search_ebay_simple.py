#!/usr/bin/env python3
"""
シンプルなeBay検索スクリプト
翻訳 → eBay Finding API → 結果フォーマット
"""

import sys
import json
import requests
import os
import subprocess
from typing import List, Dict, Any

class EbaySimpleClient:
    """シンプルなeBayクライアント"""
    
    def __init__(self):
        self.api_url = "https://svcs.ebay.com/services/search/FindingService/v1"
        self.app_id = os.getenv('EBAY_APP_ID', 'ariGaT-records-PRD-1a6ee1171-104bfaa4')
        self.exchange_rate = 142.73
    
    def get_exchange_rate(self) -> float:
        """為替レートを取得"""
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
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
        eBayから商品データを検索
        """
        try:
            print(f"eBayシンプル検索開始: {keyword}", file=sys.stderr)
            
            # 為替レートを取得
            exchange_rate = self.get_exchange_rate()
            
            # 日本語キーワードの場合は英語に翻訳
            search_keyword = keyword
            if self._contains_japanese(keyword):
                search_keyword = self.translate_to_english(keyword)
            
            print(f"検索キーワード: {search_keyword}", file=sys.stderr)
            
            # eBay Finding APIで検索
            results = self._search_with_finding_api(search_keyword, limit, exchange_rate)
            
            if results:
                print(f"検索成功: {len(results)}件取得", file=sys.stderr)
                return results
            else:
                print("検索結果が空です", file=sys.stderr)
                return []
                
        except Exception as e:
            print(f"eBay検索例外: {str(e)}", file=sys.stderr)
            return []
    
    def _contains_japanese(self, text: str) -> bool:
        """日本語文字が含まれているかチェック"""
        import re
        japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
        return bool(japanese_pattern.search(text))
    
    def _search_with_finding_api(self, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """eBay Finding APIで検索"""
        try:
            print(f"Finding API検索: {keyword}", file=sys.stderr)
            
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
            
            response = requests.get(self.api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # エラーチェック
                if 'errorMessage' in data.get('findItemsByKeywordsResponse', [{}])[0]:
                    error = data['findItemsByKeywordsResponse'][0]['errorMessage']
                    print(f"eBay APIエラー: {error}", file=sys.stderr)
                    return []
                
                # 検索結果を取得
                search_result = data.get('findItemsByKeywordsResponse', [{}])[0].get('searchResult', [{}])[0]
                items = search_result.get('item', [])
                
                if items:
                    print(f"Finding API成功: {len(items)}件取得", file=sys.stderr)
                    return self._format_results(items, exchange_rate)
                else:
                    print("Finding API: 検索結果が空", file=sys.stderr)
                    return []
            else:
                print(f"Finding API HTTPエラー: {response.status_code}", file=sys.stderr)
                return []
                
        except Exception as e:
            print(f"Finding API例外: {str(e)}", file=sys.stderr)
            return []
    
    def _format_results(self, items: List[Dict], exchange_rate: float) -> List[Dict[str, Any]]:
        """検索結果をフォーマット"""
        formatted_results = []
        
        for item in items:
            try:
                # 価格情報を取得
                current_price = float(item.get('sellingStatus', [{}])[0].get('currentPrice', [{}])[0].get('__value__', 0))
                shipping_cost = float(item.get('shippingInfo', [{}])[0].get('shippingServiceCost', [{}])[0].get('__value__', 0))
                
                # 基本情報を取得
                title = item.get('title', [''])[0]
                url = item.get('viewItemURL', [''])[0]
                image_url = item.get('galleryURL', [''])[0]
                condition = item.get('condition', [{}])[0].get('conditionDisplayName', ['Used'])[0]
                seller = item.get('sellerInfo', [{}])[0].get('sellerUserName', ['eBay Seller'])[0]
                
                # JPY変換
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
                
                # 基本的な検証
                if self._validate_item(formatted_item):
                    formatted_results.append(formatted_item)
                    
            except Exception as e:
                print(f"アイテムフォーマットエラー: {str(e)}", file=sys.stderr)
                continue
        
        return formatted_results
    
    def _extract_item_id_from_url(self, url: str) -> str:
        """URLからアイテムIDを抽出"""
        try:
            import re
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
        
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_ebay_simple.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"eBayシンプル検索開始: {keyword}, limit: {limit}", file=sys.stderr)
    
    client = EbaySimpleClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()
