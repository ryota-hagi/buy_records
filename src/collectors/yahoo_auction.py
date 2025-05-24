"""
Yahoo!オークションAPIクライアント
Yahoo!オークションAPIから出品情報と落札情報を取得します。
"""

import time
import requests
import json
import re
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from ..utils.config import get_config, get_optional_config

class YahooAuctionClient:
    """Yahoo!オークションAPIと通信するクライアントクラス"""
    
    def _parse_relative_time(self, time_str: str) -> str:
        """
        日本語の相対時間形式を解析してISO 8601形式のタイムスタンプに変換します。
        
        Args:
            time_str: 相対時間形式の文字列（例: "3日", "6時間"）
            
        Returns:
            str: ISO 8601形式のタイムスタンプ
        """
        if not time_str:
            return datetime.now().isoformat()
        
        # 数字と単位を抽出
        match = re.match(r'(\d+)([日時間分秒])', time_str)
        if not match:
            return datetime.now().isoformat()
        
        value = int(match.group(1))
        unit = match.group(2)
        
        # 現在時刻から相対時間を計算
        now = datetime.now()
        if unit == '日':
            end_time = now - timedelta(days=value)
        elif unit == '時間':
            end_time = now - timedelta(hours=value)
        elif unit == '分':
            end_time = now - timedelta(minutes=value)
        elif unit == '秒':
            end_time = now - timedelta(seconds=value)
        else:
            end_time = now
        
        # ISO 8601形式に変換
        return end_time.isoformat()
    
    def __init__(self):
        """
        YahooAuctionClientを初期化します。
        環境変数から認証情報を読み込みます。
        """
        self.app_id = get_optional_config("YAHOO_APP_ID")
        self.base_url = "https://auctions.yahooapis.jp/AuctionWebService/V2"
        self.headers = {
            "User-Agent": get_optional_config("USER_AGENT", "RecordCollector/1.0")
        }
        self.delay = float(get_optional_config("YAHOO_REQUEST_DELAY", "1.0"))
        self.driver = None  # Seleniumドライバー（終了オークション用）
        
        # YAHOO_APP_IDが設定されていない場合の警告
        if not self.app_id:
            print("警告: YAHOO_APP_IDが設定されていません。Yahoo!オークションAPIは利用できません。")
    
    def _initialize_driver(self):
        """Seleniumドライバーを初期化します（終了オークション用）"""
        if self.driver is None:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
            
            # ChromeDriverのパスを設定
            chrome_driver_path = "/Users/hagiryouta/Downloads/chromedriver-mac-arm64/chromedriver"
            service = Service(executable_path=chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
    
    def _close_driver(self):
        """Seleniumドライバーを閉じます"""
        if self.driver is not None:
            self.driver.quit()
            self.driver = None
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        APIリクエストを実行します。
        
        Args:
            endpoint: APIエンドポイント
            params: リクエストパラメータ
            
        Returns:
            Dict[str, Any]: APIレスポンス
        """
        # YAHOO_APP_IDが設定されていない場合はエラーを発生させる
        if not self.app_id:
            raise ValueError("YAHOO_APP_IDが設定されていません。Yahoo!オークションAPIを使用するには有効なApp IDが必要です。")
        
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
        
        # XMLレスポンスをパース
        root = ET.fromstring(response.content)
        
        # XMLをディクショナリに変換
        return self._xml_to_dict(root)
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """XMLエレメントをディクショナリに変換"""
        result = {}
        
        # 属性を追加
        for key, value in element.attrib.items():
            result[key] = value
        
        # テキスト内容を追加
        if element.text and element.text.strip():
            result["text"] = element.text.strip()
        
        # 子要素を再帰的に処理
        for child in element:
            child_dict = self._xml_to_dict(child)
            tag = child.tag
            
            # 同じタグが複数ある場合はリストに
            if tag in result:
                if isinstance(result[tag], list):
                    result[tag].append(child_dict)
                else:
                    result[tag] = [result[tag], child_dict]
            else:
                result[tag] = child_dict
        
        return result
    
    def search_active_items(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        キーワードで現在出品中の商品を検索します。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 出品中商品のリスト
        """
        # YAHOO_APP_IDが設定されていない場合は空のリストを返す
        if not self.app_id:
            print(f"Yahoo!オークション検索をスキップしました（App ID未設定）: {keyword}")
            return []
        
        endpoint = "search"
        params = {
            "query": keyword,
            "output": "xml",
            "sort": "price",  # 価格順
            "order": "a",     # 昇順（安い順）
            "results": limit
        }
        
        try:
            response = self._make_request(endpoint, params)
            items = response.get("Result", {}).get("Item", [])
            
            # 単一アイテムの場合はリストに変換
            if not isinstance(items, list):
                items = [items]
            
            # 必要なデータを抽出
            results = []
            for item in items:
                # 価格情報を統一フォーマットに変換
                current_price = int(float(item.get("CurrentPrice", 0)))
                buy_now_price = int(float(item.get("BidOrBuy", 0))) if "BidOrBuy" in item else None
                
                # 最終価格を決定（即決価格がある場合はそれを優先）
                final_price = buy_now_price if buy_now_price and buy_now_price > 0 else current_price
                
                result = {
                    "search_term": keyword,
                    "item_id": item.get("AuctionID", ""),
                    "title": item.get("Title", ""),
                    "price": final_price,  # 統一された価格フィールド
                    "current_price": current_price,
                    "buy_now_price": buy_now_price,
                    "bids": int(item.get("Bids", 0)),
                    "currency": "JPY",
                    "status": "active",
                    "sold_date": None,
                    "end_time": datetime.fromisoformat(item.get("EndTime", datetime.now().isoformat())).isoformat() if item.get("EndTime") else datetime.now().isoformat(),
                    "condition": item.get("ItemStatus", ""),
                    "url": item.get("AuctionItemUrl", ""),
                    "image_url": item.get("Image", ""),
                    "seller": item.get("Seller", {}).get("Id", "")
                }
                results.append(result)
            
            return results
        except Exception as e:
            print(f"Error searching active items for '{keyword}': {str(e)}")
            return []

    def search_items(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        キーワードで現在出品中の商品を検索します（後方互換性のため）。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 出品中商品のリスト
        """
        return self.search_active_items(keyword, limit)
    
    def get_item_details(self, auction_id: str) -> Dict[str, Any]:
        """
        オークションIDから商品詳細を取得します。
        
        Args:
            auction_id: オークションID
            
        Returns:
            Dict[str, Any]: 商品詳細
        """
        # YAHOO_APP_IDが設定されていない場合は空の辞書を返す
        if not self.app_id:
            print(f"Yahoo!オークション詳細取得をスキップしました（App ID未設定）: {auction_id}")
            return {}
        
        endpoint = "auctionItem"
        params = {
            "auctionID": auction_id,
            "output": "xml"
        }
        
        try:
            response = self._make_request(endpoint, params)
            item = response.get("Item", {})
            
            result = {
                "item_id": auction_id,
                "title": item.get("Title", ""),
                "current_price": int(float(item.get("Price", 0))),
                "buy_now_price": int(float(item.get("BidOrBuy", 0))) if "BidOrBuy" in item else None,
                "bids": int(item.get("Bids", 0)),
                "currency": "JPY",
                "status": "active" if item.get("Status") == "open" else "ended",
                "end_time": datetime.fromisoformat(item.get("EndTime", datetime.now().isoformat())).isoformat() if item.get("EndTime") else datetime.now().isoformat(),
                "condition": item.get("State", ""),
                "url": item.get("AuctionItemUrl", ""),
                "image_url": item.get("Image", ""),
                "seller": item.get("Seller", {}).get("Id", ""),
                "description": item.get("Description", "")
            }
            
            return result
        except Exception as e:
            print(f"Error getting item details for '{auction_id}': {str(e)}")
            return {}
    
    def search_completed_items(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        キーワードで終了したオークションを検索します（スクレイピング）。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 終了済みオークションのリスト
        """
        try:
            self._initialize_driver()
            
            # Yahoo!オークションの検索URLを構築
            encoded_keyword = requests.utils.quote(keyword)
            search_url = f"https://auctions.yahoo.co.jp/search/search?p={encoded_keyword}&va={encoded_keyword}&is_closed=1&b=1&n={limit}"
            
            self.driver.get(search_url)
            time.sleep(3)  # ページ読み込み待機
            
            # 商品リストを取得
            items = []
            
            # 商品要素を取得
            from selenium.webdriver.common.by import By
            item_elements = self.driver.find_elements(By.CSS_SELECTOR, ".Product")
            
            for item_element in item_elements[:limit]:
                try:
                    # 商品情報を抽出
                    item_url_element = item_element.find_element(By.CSS_SELECTOR, ".Product__titleLink")
                    item_url = item_url_element.get_attribute("href")
                    item_id = item_url.split("/")[-1].split("?")[0]
                    title = item_url_element.text
                    
                    # 価格情報
                    price_element = item_element.find_element(By.CSS_SELECTOR, ".Product__priceValue")
                    price_text = price_element.text.replace("円", "").replace(",", "")
                    price = int(price_text) if price_text.isdigit() else 0
                    
                    # 入札数
                    bids = 0
                    try:
                        bids_element = item_element.find_element(By.CSS_SELECTOR, ".Product__bid")
                        bids_text = bids_element.text.replace("入札", "")
                        bids = int(bids_text) if bids_text.isdigit() else 0
                    except:
                        pass
                    
                    # 画像URL
                    image_url = ""
                    try:
                        img_element = item_element.find_element(By.CSS_SELECTOR, ".Product__imageData")
                        image_url = img_element.get_attribute("src")
                    except:
                        pass
                    
                    # 終了日時
                    end_time = ""
                    try:
                        time_element = item_element.find_element(By.CSS_SELECTOR, ".Product__time")
                        relative_time = time_element.text
                        # 相対時間形式をISO 8601形式に変換
                        end_time = self._parse_relative_time(relative_time)
                    except:
                        end_time = datetime.now().isoformat()
                    
                    item = {
                        "search_term": keyword,
                        "item_id": item_id,
                        "title": title,
                        "current_price": price,  # 終了価格
                        "buy_now_price": None,   # 終了済みなので即決価格は不明
                        "bids": bids,
                        "currency": "JPY",
                        "status": "ended",
                        "end_time": end_time,
                        "condition": "",         # 一覧からは取得困難
                        "url": item_url,
                        "image_url": image_url,
                        "seller": ""             # 一覧からは取得困難
                    }
                    
                    items.append(item)
                    
                    # APIレート制限対応
                    time.sleep(self.delay)
                    
                except Exception as e:
                    print(f"Error extracting item data: {str(e)}")
                    continue
            
            return items
        except Exception as e:
            print(f"Error searching completed items for '{keyword}': {str(e)}")
            return []
        finally:
            self._close_driver()
    
    def get_complete_data(self, keyword: str, active_limit: int = 50, completed_limit: int = 50) -> List[Dict[str, Any]]:
        """
        キーワードの完全なデータ（出品中と終了済み）を取得します。
        
        Args:
            keyword: 検索キーワード
            active_limit: 出品中アイテムの取得数
            completed_limit: 終了済みアイテムの取得数
            
        Returns:
            List[Dict[str, Any]]: 完全なデータ
        """
        # 出品中のアイテムを取得
        active_items = self.search_items(keyword, active_limit)
        time.sleep(self.delay)  # APIレート制限対応
        
        # 終了済みのアイテムを取得
        completed_items = self.search_completed_items(keyword, completed_limit)
        
        # 統計情報を計算
        active_prices = [item["current_price"] for item in active_items if item["current_price"] > 0]
        completed_prices = [item["current_price"] for item in completed_items if item["current_price"] > 0]
        
        lowest_active_price = min(active_prices) if active_prices else 0
        avg_sold_price = sum(completed_prices) / len(completed_prices) if completed_prices else 0
        
        # 中央値を計算
        median_sold_price = 0
        if completed_prices:
            completed_prices.sort()
            mid = len(completed_prices) // 2
            if len(completed_prices) % 2 == 0 and len(completed_prices) > 1:
                median_sold_price = (completed_prices[mid - 1] + completed_prices[mid]) / 2
            else:
                median_sold_price = completed_prices[mid]
        
        # 結果を統合
        all_items = []
        
        # 出品中アイテムに統計情報を追加
        for item in active_items:
            item.update({
                "lowest_current_price": lowest_active_price,
                "active_listings_count": len(active_items),
                "avg_sold_price": round(avg_sold_price, 2),
                "median_sold_price": round(median_sold_price, 2),
                "sold_count": len(completed_items)
            })
            all_items.append(item)
        
        # 終了済みアイテムに統計情報を追加
        for item in completed_items:
            item.update({
                "lowest_current_price": lowest_active_price,
                "active_listings_count": len(active_items),
                "avg_sold_price": round(avg_sold_price, 2),
                "median_sold_price": round(median_sold_price, 2),
                "sold_count": len(completed_items)
            })
            all_items.append(item)
        
        return all_items
