#!/usr/bin/env python3
"""
eBay Browse API検索スクリプト
正しいeBay APIエンドポイントを使用
"""

import sys
import json
import requests
import os
import subprocess
from typing import List, Dict, Any

class EbayBrowseClient:
    """eBay Browse APIクライアント"""
    
    def __init__(self):
        self.base_url = "https://api.ebay.com"
        # .envファイルを読み込む
        from dotenv import load_dotenv
        load_dotenv()
        
        self.app_id = os.getenv('EBAY_APP_ID', 'ariGaT-records-PRD-1a6ee1171-104bfaa4')
        self.cert_id = os.getenv('EBAY_CERT_ID', 'PRD-a6ee117176f2-7ca7-4f11-aa34-b24d')
        self.exchange_rate = 142.73
        self.access_token = None
    
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
    
    def get_client_credentials_token(self) -> str:
        """Client Credentials Grantでアクセストークンを取得"""
        try:
            print("Client Credentialsトークン取得中...", file=sys.stderr)
            
            # OAuth2エンドポイント
            token_url = "https://api.ebay.com/identity/v1/oauth2/token"
            
            # Basic認証用のヘッダー
            import base64
            credentials = f"{self.app_id}:{self.cert_id}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {encoded_credentials}'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope'
            }
            
            response = requests.post(token_url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                print("アクセストークン取得成功", file=sys.stderr)
                return access_token
            else:
                print(f"トークン取得失敗: {response.status_code} - {response.text}", file=sys.stderr)
                return None
                
        except Exception as e:
            print(f"トークン取得例外: {str(e)}", file=sys.stderr)
            return None
    
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
        eBay Browse APIで商品データを検索
        """
        try:
            print(f"eBay Browse API検索開始: {keyword}", file=sys.stderr)
            
            # 為替レートを取得
            exchange_rate = self.get_exchange_rate()
            
            # アクセストークンを取得
            if not self.access_token:
                self.access_token = self.get_client_credentials_token()
                if not self.access_token:
                    print("アクセストークンが取得できませんでした", file=sys.stderr)
                    return []
            
            # 日本語キーワードの場合は英語に翻訳
            search_keyword = keyword
            if self._contains_japanese(keyword):
                search_keyword = self.translate_to_english(keyword)
            
            print(f"検索キーワード: {search_keyword}", file=sys.stderr)
            
            # Browse APIで検索
            results = self._search_with_browse_api(search_keyword, limit, exchange_rate)
            
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
    
    def _search_with_browse_api(self, keyword: str, limit: int, exchange_rate: float) -> List[Dict[str, Any]]:
        """eBay Browse APIで検索"""
        try:
            print(f"Browse API検索: {keyword}", file=sys.stderr)
            
            # Browse API エンドポイント
            search_url = f"{self.base_url}/buy/browse/v1/item_summary/search"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
            }
            
            params = {
                'q': keyword,
                'limit': min(limit, 50),
                'sort': 'price',
                'filter': 'conditionIds:{3000|4000|5000}',  # Used, Very Good, Good
                'fieldgroups': 'MATCHING_ITEMS,EXTENDED'
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('itemSummaries', [])
                
                if items:
                    print(f"Browse API成功: {len(items)}件取得", file=sys.stderr)
                    return self._format_browse_results(items, exchange_rate)
                else:
                    print("Browse API: 検索結果が空", file=sys.stderr)
                    return []
            else:
                print(f"Browse API HTTPエラー: {response.status_code} - {response.text}", file=sys.stderr)
                return []
                
        except Exception as e:
            print(f"Browse API例外: {str(e)}", file=sys.stderr)
            return []
    
    def _format_browse_results(self, items: List[Dict], exchange_rate: float) -> List[Dict[str, Any]]:
        """Browse API結果をフォーマット"""
        formatted_results = []
        
        for item in items:
            try:
                # 価格情報を取得
                price_info = item.get('price', {})
                price_value = float(price_info.get('value', 0))
                currency = price_info.get('currency', 'USD')
                
                # 送料情報
                shipping_info = item.get('shippingOptions', [{}])[0] if item.get('shippingOptions') else {}
                shipping_cost = 0
                if shipping_info.get('shippingCost'):
                    shipping_cost = float(shipping_info['shippingCost'].get('value', 0))
                
                # 基本情報を取得
                title = item.get('title', '')
                item_web_url = item.get('itemWebUrl', '')
                image_url = item.get('image', {}).get('imageUrl', '')
                condition = item.get('condition', 'Used')
                seller_info = item.get('seller', {})
                seller_name = seller_info.get('username', 'eBay Seller')
                
                # JPY変換
                if currency == 'USD':
                    price_jpy = int(price_value * exchange_rate)
                    shipping_jpy = int(shipping_cost * exchange_rate)
                else:
                    price_jpy = int(price_value)
                    shipping_jpy = int(shipping_cost)
                
                formatted_item = {
                    "title": title,
                    "name": title,
                    "price": price_jpy,
                    "url": item_web_url,
                    "image_url": image_url,
                    "condition": condition,
                    "seller": seller_name,
                    "status": "active",
                    "sold_date": None,
                    "currency": "JPY",
                    "exchange_rate": exchange_rate,
                    "shipping_fee": shipping_jpy,
                    "total_price": price_jpy + shipping_jpy,
                    "item_id": item.get('itemId', '')
                }
                
                # 基本的な検証
                if self._validate_item(formatted_item):
                    formatted_results.append(formatted_item)
                    
            except Exception as e:
                print(f"アイテムフォーマットエラー: {str(e)}", file=sys.stderr)
                continue
        
        return formatted_results
    
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
        print("Usage: python search_ebay_browse_api.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"eBay Browse API検索開始: {keyword}, limit: {limit}", file=sys.stderr)
    
    client = EbayBrowseClient()
    results = client.search_items(keyword, limit)
    
    print(f"検索完了: {len(results)}件取得", file=sys.stderr)
    
    # JSON形式で結果を出力（マーカー付き）
    print("JSON_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("JSON_END")

if __name__ == "__main__":
    main()
