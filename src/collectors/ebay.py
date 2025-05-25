"""
eBay APIクライアント
eBay APIから販売履歴データと現在の出品情報を取得します。
"""

import time
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import base64
from ..utils.config import get_config

class EbayClient:
    """eBay APIと通信するクライアントクラス"""
    
    def __init__(self):
        """
        EbayClientを初期化します。
        環境変数から認証情報を読み込みます。
        """
        self.app_id = get_config("EBAY_APP_ID")
        self.cert_id = get_config("EBAY_CERT_ID")
        self.client_secret = get_config("EBAY_CLIENT_SECRET")
        self.user_token = get_config("EBAY_USER_TOKEN")
        self.token_expiry_str = get_config("EBAY_TOKEN_EXPIRY")
        self.environment = get_config("EBAY_ENVIRONMENT", "PRODUCTION")
        
        # 環境に応じたエンドポイント設定
        if self.environment == "PRODUCTION":
            self.auth_url = "https://api.ebay.com/identity/v1/oauth2/token"
            self.api_url = "https://api.ebay.com"
        else:
            self.auth_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            self.api_url = "https://api.sandbox.ebay.com"
        
        # User Tokenの有効期限をチェック
        self.token_expiry = None
        if self.token_expiry_str:
            try:
                from datetime import datetime
                self.token_expiry = datetime.fromisoformat(self.token_expiry_str.replace('Z', '+00:00'))
            except:
                print(f"Warning: Invalid token expiry format: {self.token_expiry_str}")
        
        self.access_token = None
        self.delay = float(get_config("REQUEST_DELAY", "1.0"))
    
    def _get_access_token(self) -> str:
        """
        User Tokenまたは新しいアクセストークンを取得します。
        
        Returns:
            str: アクセストークン
        """
        # User Tokenが設定されている場合は常にそれを使用
        if self.user_token:
            print("Using User Token")
            return self.user_token
        
        # User Tokenがない場合はClient Credentialsフローを使用
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        print("Getting new access token using Client Credentials flow")
        
        # クライアント認証情報
        credentials = f"{self.app_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }
        
        payload = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        
        try:
            response = requests.post(self.auth_url, headers=headers, data=payload)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            # トークン有効期限を設定（少し余裕を持たせる）
            expires_in = token_data["expires_in"] - 60  # 1分早めに期限切れとする
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            print(f"Successfully obtained new access token, expires in {expires_in} seconds")
            return self.access_token
        except Exception as e:
            print(f"Failed to get access token: {str(e)}")
            # User Tokenがある場合はフォールバックとして使用
            if self.user_token:
                print("Falling back to User Token despite expiry")
                return self.user_token
            raise
    
    def _make_request(self, endpoint: str, params: Dict = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        リトライ機能付きでAPIリクエストを実行します。
        
        Args:
            endpoint: APIエンドポイント
            params: リクエストパラメータ
            max_retries: 最大リトライ回数
            
        Returns:
            Dict[str, Any]: APIレスポンス
        """
        for attempt in range(max_retries + 1):
            try:
                token = self._get_access_token()
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"  # 米国マーケットプレイス
                }
                
                url = f"{self.api_url}{endpoint}"
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 429:  # Too Many Requests
                    retry_after = int(response.headers.get("Retry-After", self.delay * 2))
                    print(f"Rate limit hit. Waiting for {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue  # リトライ
                
                if response.status_code == 401:  # Unauthorized
                    print(f"Authentication error on attempt {attempt + 1}. Refreshing token...")
                    self.access_token = None  # トークンをリセット
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)  # 指数バックオフ
                        continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                print(f"Request timeout on attempt {attempt + 1}/{max_retries + 1}")
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * self.delay
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
                    
            except requests.exceptions.ConnectionError:
                print(f"Connection error on attempt {attempt + 1}/{max_retries + 1}")
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * self.delay
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
                    
            except requests.exceptions.RequestException as e:
                print(f"Request error on attempt {attempt + 1}/{max_retries + 1}: {e}")
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * self.delay
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
        
        # すべてのリトライが失敗した場合
        raise Exception(f"Failed to make request after {max_retries + 1} attempts")
    
    def search_sold_items(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        キーワードで過去に売却された商品を検索します。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 売却済み商品のリスト
        """
        # Marketplace Insights APIを使用
        endpoint = "/buy/marketplace_insights/v1_beta/item_sales/search"
        params = {
            "q": keyword,
            "limit": limit,
            "filter": "soldWithin:DAYS_90"  # 過去90日間の売却データ
        }
        
        try:
            response = self._make_request(endpoint, params)
            items = response.get("itemSales", [])
            
            # 必要なデータを抽出
            results = []
            for item in items:
                result = {
                    "search_term": keyword,
                    "item_id": item.get("itemId", ""),
                    "title": item.get("title", ""),
                    "sold_price": self._extract_price(item.get("price", {})),
                    "currency": item.get("price", {}).get("currency", "USD"),
                    "sold_date": item.get("soldDate", ""),
                    "sold_quantity": item.get("quantity", 1),
                    "condition": self._extract_condition(item.get("condition", "")),
                    "url": item.get("itemWebUrl", ""),
                    "image_url": self._extract_image(item.get("image", {})),
                    "seller": item.get("seller", {}).get("username", "")
                }
                results.append(result)
            
            return results
        except Exception as e:
            print(f"Error searching sold items for '{keyword}': {str(e)}")
            return []
    
    def search_active_items(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        キーワードで現在出品中の商品を検索します（詳細情報付き）。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 出品中商品のリスト
        """
        # Browse APIを使用
        endpoint = "/buy/browse/v1/item_summary/search"
        params = {
            "q": keyword,
            "limit": limit,
            "filter": "conditionIds:{1000|1500|2000|2500|3000|4000|5000|6000}",  # 全コンディション
            "sort": "price"  # 価格順でソート
        }
        
        try:
            response = self._make_request(endpoint, params)
            items = response.get("itemSummaries", [])
            
            # 必要なデータを抽出
            results = []
            for item in items:
                price = self._extract_price(item.get("price", {}))
                
                result = {
                    "search_term": keyword,
                    "item_id": item.get("itemId", ""),
                    "title": item.get("title", ""),
                    "name": item.get("title", ""),  # 互換性のため
                    "price": price,
                    "currency": item.get("price", {}).get("currency", "USD"),
                    "status": "active",
                    "sold_date": None,
                    "condition": self._extract_condition_from_summary(item),
                    "url": item.get("itemWebUrl", ""),
                    "image_url": self._extract_image_from_summary(item),
                    "seller": item.get("seller", {}).get("username", ""),
                    "thumbnails": [{"url": self._extract_image_from_summary(item)}] if self._extract_image_from_summary(item) else []
                }
                results.append(result)
            
            return results[:limit]
        except Exception as e:
            print(f"Error searching active items for '{keyword}': {str(e)}")
            return []

    def get_current_listings(self, keyword: str, limit: int = 50) -> Dict[str, Any]:
        """
        キーワードで現在出品中の商品を検索します。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            Dict[str, Any]: 現在の出品情報の要約
        """
        # Browse APIを使用
        endpoint = "/buy/browse/v1/item_summary/search"
        params = {
            "q": keyword,
            "limit": limit,
            "filter": "conditionIds:{1000|1500|2000|2500|3000|4000|5000|6000}"  # 全コンディション
        }
        
        try:
            response = self._make_request(endpoint, params)
            items = response.get("itemSummaries", [])
            
            if not items:
                return {
                    "search_term": keyword,
                    "lowest_current_price": 0,
                    "current_listings_count": 0
                }
            
            # 価格でソート
            items_with_price = [item for item in items if "price" in item]
            items_with_price.sort(key=lambda x: float(x["price"]["value"]))
            
            # 最安値を取得
            lowest_price = 0
            if items_with_price:
                lowest_price = float(items_with_price[0]["price"]["value"])
            
            return {
                "search_term": keyword,
                "lowest_current_price": lowest_price,
                "current_listings_count": len(items)
            }
        except Exception as e:
            print(f"Error getting current listings for '{keyword}': {str(e)}")
            return {
                "search_term": keyword,
                "lowest_current_price": 0,
                "current_listings_count": 0
            }
    
    def get_sales_summary(self, keyword: str) -> Dict[str, Any]:
        """
        キーワードの売却データサマリーを取得します。
        
        Args:
            keyword: 検索キーワード
            
        Returns:
            Dict[str, Any]: 売却データサマリー
        """
        sold_items = self.search_sold_items(keyword)
        
        if not sold_items:
            return {
                "search_term": keyword,
                "avg_sold_price_90days": 0,
                "median_sold_price_90days": 0,
                "sold_count_90days": 0
            }
        
        # 価格リストを抽出
        prices = [item["sold_price"] for item in sold_items if item["sold_price"] > 0]
        
        if not prices:
            return {
                "search_term": keyword,
                "avg_sold_price_90days": 0,
                "median_sold_price_90days": 0,
                "sold_count_90days": 0
            }
        
        # 平均値と中央値を計算
        avg_price = sum(prices) / len(prices)
        prices.sort()
        median_price = prices[len(prices) // 2]
        if len(prices) % 2 == 0 and len(prices) > 1:
            median_price = (prices[len(prices) // 2 - 1] + prices[len(prices) // 2]) / 2
        
        return {
            "search_term": keyword,
            "avg_sold_price_90days": round(avg_price, 2),
            "median_sold_price_90days": round(median_price, 2),
            "sold_count_90days": len(sold_items)
        }
    
    def get_complete_data(self, keyword: str) -> List[Dict[str, Any]]:
        """
        キーワードの完全なデータ（売却履歴と現在の出品情報）を取得します。
        
        Args:
            keyword: 検索キーワード
            
        Returns:
            List[Dict[str, Any]]: 完全なデータのリスト
        """
        # 売却データを取得
        sold_items = self.search_sold_items(keyword)
        
        # 現在の出品情報を取得
        current_listings = self.get_current_listings(keyword)
        
        # 売却サマリーを取得
        sales_summary = self.get_sales_summary(keyword)
        
        # データを統合
        results = []
        for item in sold_items:
            item.update({
                "lowest_current_price": current_listings["lowest_current_price"],
                "current_listings_count": current_listings["current_listings_count"],
                "avg_sold_price_90days": sales_summary["avg_sold_price_90days"],
                "median_sold_price_90days": sales_summary["median_sold_price_90days"],
                "sold_count_90days": sales_summary["sold_count_90days"]
            })
            results.append(item)
        
        # 売却データがない場合は、サマリー情報だけのレコードを作成
        if not results:
            results.append({
                "search_term": keyword,
                "item_id": "",
                "title": f"{keyword} (No sold items found)",
                "sold_price": 0,
                "currency": "USD",
                "sold_date": "",
                "sold_quantity": 0,
                "condition": "",
                "url": "",
                "image_url": "",
                "seller": "",
                "lowest_current_price": current_listings["lowest_current_price"],
                "current_listings_count": current_listings["current_listings_count"],
                "avg_sold_price_90days": 0,
                "median_sold_price_90days": 0,
                "sold_count_90days": 0
            })
        
        return results
    
    def _extract_price(self, price_obj: Dict) -> float:
        """価格オブジェクトから価格を抽出"""
        if not price_obj or "value" not in price_obj:
            return 0
        try:
            return float(price_obj["value"])
        except (ValueError, TypeError):
            return 0
    
    def _extract_condition(self, condition_obj: Dict) -> str:
        """コンディションオブジェクトからコンディション名を抽出"""
        if not condition_obj:
            return ""
        return condition_obj.get("conditionDisplayName", "")
    
    
    def _extract_image(self, image_obj: Dict) -> str:
        """画像オブジェクトから画像URLを抽出"""
        if not image_obj:
            return ""
        return image_obj.get("imageUrl", "")
    
    def _extract_condition_from_summary(self, item: Dict) -> str:
        """商品サマリーからコンディション情報を抽出"""
        if "condition" in item:
            return item["condition"]
        elif "conditionId" in item:
            # コンディションIDから名前を推定
            condition_map = {
                "1000": "New",
                "1500": "New other",
                "2000": "Manufacturer refurbished",
                "2500": "Seller refurbished",
                "3000": "Used",
                "4000": "Very Good",
                "5000": "Good",
                "6000": "Acceptable"
            }
            return condition_map.get(item["conditionId"], "Unknown")
        return ""
    
    def _extract_image_from_summary(self, item: Dict) -> str:
        """商品サマリーから画像URLを抽出"""
        if "image" in item:
            return item["image"].get("imageUrl", "")
        elif "thumbnailImages" in item and item["thumbnailImages"]:
            return item["thumbnailImages"][0].get("imageUrl", "")
        return ""
