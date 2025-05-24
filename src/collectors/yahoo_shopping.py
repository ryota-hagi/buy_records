"""
Yahoo!ショッピングAPIクライアント
Yahoo!ショッピングAPIから商品情報を取得します。
"""

import time
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..utils.config import get_config, get_optional_config

class YahooShoppingClient:
    """Yahoo!ショッピングAPIと通信するクライアントクラス"""
    
    def __init__(self):
        """
        YahooShoppingClientを初期化します。
        環境変数から認証情報を読み込みます。
        """
        self.app_id = get_optional_config("YAHOO_SHOPPING_APP_ID")
        self.base_url = "https://shopping.yahooapis.jp/ShoppingWebService/V3"
        self.headers = {
            "User-Agent": get_optional_config("USER_AGENT", "RecordCollector/1.0")
        }
        self.delay = float(get_optional_config("YAHOO_SHOPPING_REQUEST_DELAY", "1.0"))
        
        # YAHOO_SHOPPING_APP_IDが設定されていない場合の警告
        if not self.app_id:
            print("警告: YAHOO_SHOPPING_APP_IDが設定されていません。Yahoo!ショッピングAPIは利用できません。")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        APIリクエストを実行します。
        
        Args:
            endpoint: APIエンドポイント
            params: リクエストパラメータ
            
        Returns:
            Dict[str, Any]: APIレスポンス
        """
        # YAHOO_SHOPPING_APP_IDが設定されていない場合はエラーを発生させる
        if not self.app_id:
            raise ValueError("YAHOO_SHOPPING_APP_IDが設定されていません。Yahoo!ショッピングAPIを使用するには有効なApp IDが必要です。")
        
        # アプリケーションIDをパラメータに追加
        params["appid"] = self.app_id
        
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params, headers=self.headers)
        
        if response.status_code == 429:  # Too Many Requests
            retry_after = int(response.headers.get("Retry-After", self.delay * 2))
            print(f"Rate limit hit. Waiting for {retry_after} seconds...")
            time.sleep(retry_after)
            return self._make_request(endpoint, params)  # 再試行
        
        response.raise_for_status()
        
        # JSONレスポンスをパース
        return response.json()
    
    def search_items(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        キーワードで商品を検索します。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 商品のリスト
        """
        # YAHOO_SHOPPING_APP_IDが設定されていない場合は空のリストを返す
        if not self.app_id:
            print(f"Yahoo!ショッピング検索をスキップしました（App ID未設定）: {keyword}")
            return []
        
        endpoint = "itemSearch"
        params = {
            "query": keyword,
            "results": min(limit, 50),  # Yahoo!ショッピングAPIの最大取得数は50件
            "sort": "+price"  # 価格昇順
        }
        
        try:
            response = self._make_request(endpoint, params)
            
            # レスポンス構造を確認
            if "hits" not in response:
                print(f"Unexpected response structure: {response}")
                return []
            
            items = response["hits"]
            
            # 必要なデータを抽出
            results = []
            for item in items:
                # 価格情報を統一フォーマットに変換
                price = int(float(item.get("price", 0)))
                
                # 在庫情報
                stock_quantity = item.get("availability", {}).get("inStock", 0)
                if isinstance(stock_quantity, bool):
                    stock_quantity = 1 if stock_quantity else 0
                
                # レビュー情報
                review_info = item.get("review", {})
                review_score = float(review_info.get("rate", 0)) if review_info.get("rate") else 0
                review_count = int(review_info.get("count", 0)) if review_info.get("count") else 0
                
                # 配送情報
                shipping_info = {
                    "free_shipping": item.get("shipping", {}).get("code") == 1,
                    "shipping_cost": item.get("shipping", {}).get("price", 0)
                }
                
                result = {
                    "search_term": keyword,
                    "item_id": item.get("code", ""),
                    "title": item.get("name", ""),
                    "name": item.get("name", ""),  # 互換性のため
                    "price": price,  # 統一された価格フィールド
                    "regular_price": price,  # 通常価格
                    "sale_price": None,  # セール価格（基本的にはprice）
                    "currency": "JPY",
                    "status": "available",
                    "stock_quantity": stock_quantity,
                    "condition": "new",  # Yahoo!ショッピングは基本的に新品
                    "url": item.get("url", ""),
                    "image_url": item.get("image", {}).get("medium", ""),
                    "store_name": item.get("seller", {}).get("name", ""),
                    "store_id": item.get("seller", {}).get("sellerId", ""),
                    "review_score": review_score,
                    "review_count": review_count,
                    "shipping_info": shipping_info,
                    "category_id": item.get("categoryId", ""),
                    "brand": item.get("brand", {}).get("name", ""),
                    "jan_code": item.get("janCode", ""),
                    "description": item.get("description", ""),
                    "thumbnails": [{"url": item.get("image", {}).get("medium", "")}] if item.get("image", {}).get("medium") else []
                }
                results.append(result)
            
            return results[:limit]
        except Exception as e:
            print(f"Error searching items for '{keyword}': {str(e)}")
            return []
    
    def search_by_jan_code(self, jan_code: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        JANコードで商品を検索します。
        
        Args:
            jan_code: JANコード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 商品のリスト
        """
        # YAHOO_SHOPPING_APP_IDが設定されていない場合は空のリストを返す
        if not self.app_id:
            print(f"Yahoo!ショッピングJAN検索をスキップしました（App ID未設定）: {jan_code}")
            return []
        
        endpoint = "itemSearch"
        params = {
            "jan_code": jan_code,
            "results": min(limit, 50),
            "sort": "+price"
        }
        
        try:
            response = self._make_request(endpoint, params)
            
            if "hits" not in response:
                print(f"Unexpected response structure: {response}")
                return []
            
            items = response["hits"]
            
            # 必要なデータを抽出（search_itemsと同じ処理）
            results = []
            for item in items:
                price = int(float(item.get("price", 0)))
                
                stock_quantity = item.get("availability", {}).get("inStock", 0)
                if isinstance(stock_quantity, bool):
                    stock_quantity = 1 if stock_quantity else 0
                
                review_info = item.get("review", {})
                review_score = float(review_info.get("rate", 0)) if review_info.get("rate") else 0
                review_count = int(review_info.get("count", 0)) if review_info.get("count") else 0
                
                shipping_info = {
                    "free_shipping": item.get("shipping", {}).get("code") == 1,
                    "shipping_cost": item.get("shipping", {}).get("price", 0)
                }
                
                result = {
                    "search_term": jan_code,
                    "item_id": item.get("code", ""),
                    "title": item.get("name", ""),
                    "price": price,
                    "regular_price": price,
                    "sale_price": None,
                    "currency": "JPY",
                    "status": "available",
                    "stock_quantity": stock_quantity,
                    "condition": "new",
                    "url": item.get("url", ""),
                    "image_url": item.get("image", {}).get("medium", ""),
                    "store_name": item.get("seller", {}).get("name", ""),
                    "store_id": item.get("seller", {}).get("sellerId", ""),
                    "review_score": review_score,
                    "review_count": review_count,
                    "shipping_info": shipping_info,
                    "category_id": item.get("categoryId", ""),
                    "brand": item.get("brand", {}).get("name", ""),
                    "jan_code": item.get("janCode", ""),
                    "description": item.get("description", "")
                }
                results.append(result)
            
            return results
        except Exception as e:
            print(f"Error searching by JAN code '{jan_code}': {str(e)}")
            return []
    
    def get_item_details(self, item_code: str) -> Dict[str, Any]:
        """
        商品コードから商品詳細を取得します。
        
        Args:
            item_code: 商品コード
            
        Returns:
            Dict[str, Any]: 商品詳細
        """
        # YAHOO_SHOPPING_APP_IDが設定されていない場合は空の辞書を返す
        if not self.app_id:
            print(f"Yahoo!ショッピング詳細取得をスキップしました（App ID未設定）: {item_code}")
            return {}
        
        endpoint = "itemLookup"
        params = {
            "itemcode": item_code
        }
        
        try:
            response = self._make_request(endpoint, params)
            
            if "hits" not in response or not response["hits"]:
                print(f"Item not found: {item_code}")
                return {}
            
            item = response["hits"][0]
            
            price = int(float(item.get("price", 0)))
            
            stock_quantity = item.get("availability", {}).get("inStock", 0)
            if isinstance(stock_quantity, bool):
                stock_quantity = 1 if stock_quantity else 0
            
            review_info = item.get("review", {})
            review_score = float(review_info.get("rate", 0)) if review_info.get("rate") else 0
            review_count = int(review_info.get("count", 0)) if review_info.get("count") else 0
            
            shipping_info = {
                "free_shipping": item.get("shipping", {}).get("code") == 1,
                "shipping_cost": item.get("shipping", {}).get("price", 0)
            }
            
            result = {
                "item_id": item.get("code", ""),
                "title": item.get("name", ""),
                "price": price,
                "regular_price": price,
                "sale_price": None,
                "currency": "JPY",
                "status": "available",
                "stock_quantity": stock_quantity,
                "condition": "new",
                "url": item.get("url", ""),
                "image_url": item.get("image", {}).get("medium", ""),
                "store_name": item.get("seller", {}).get("name", ""),
                "store_id": item.get("seller", {}).get("sellerId", ""),
                "review_score": review_score,
                "review_count": review_count,
                "shipping_info": shipping_info,
                "category_id": item.get("categoryId", ""),
                "brand": item.get("brand", {}).get("name", ""),
                "jan_code": item.get("janCode", ""),
                "description": item.get("description", "")
            }
            
            return result
        except Exception as e:
            print(f"Error getting item details for '{item_code}': {str(e)}")
            return {}
    
    def get_complete_data(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        キーワードの完全なデータを取得し、統計情報を追加します。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 統計情報付きの商品データ
        """
        # 商品を検索
        items = self.search_items(keyword, limit)
        
        if not items:
            return []
        
        # 統計情報を計算
        prices = [item["price"] for item in items if item["price"] > 0]
        
        if prices:
            lowest_price = min(prices)
            avg_price = sum(prices) / len(prices)
            
            # 中央値を計算
            prices.sort()
            mid = len(prices) // 2
            if len(prices) % 2 == 0 and len(prices) > 1:
                median_price = (prices[mid - 1] + prices[mid]) / 2
            else:
                median_price = prices[mid]
        else:
            lowest_price = 0
            avg_price = 0
            median_price = 0
        
        # 在庫ありの商品数
        in_stock_count = len([item for item in items if item["stock_quantity"] > 0])
        
        # 各アイテムに統計情報を追加
        for item in items:
            item.update({
                "lowest_price": lowest_price,
                "avg_price": round(avg_price, 2),
                "median_price": round(median_price, 2),
                "total_listings": len(items),
                "in_stock_count": in_stock_count
            })
        
        return items
