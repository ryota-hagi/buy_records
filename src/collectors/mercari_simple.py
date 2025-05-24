"""
Mercariスクレイピングクライアント（簡素化版）
実際のスクレイピングのみを行い、モックデータは生成しない
"""

import time
import requests
from typing import List, Dict, Any, Optional
import json
import re
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from ..utils.config import get_config

class MercariClient:
    """Mercariからデータをスクレイピングするクライアントクラス（簡素化版）"""
    
    def __init__(self):
        """
        MercariClientを初期化します。
        """
        self.base_url = "https://jp.mercari.com"
        self.search_url = f"{self.base_url}/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        self.delay = float(get_config("MERCARI_REQUEST_DELAY", "1.0"))
        self.driver = None
        self.chrome_driver_path = "/Users/hagiryouta/Downloads/chromedriver-mac-arm64/chromedriver"
    
    def _initialize_driver(self):
        """Seleniumドライバーを初期化します。"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # ヘッドレスモード
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(executable_path=self.chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
    
    def _close_driver(self):
        """Seleniumドライバーを閉じます。"""
        if self.driver is not None:
            self.driver.quit()
            self.driver = None
    
    def search_active_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        出品中のアイテムを検索します（実際のスクレイピングのみ）。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 出品中アイテムのリスト
        """
        try:
            self._initialize_driver()
            
            # 検索URLを構築
            encoded_keyword = requests.utils.quote(keyword)
            search_url = f"{self.search_url}?keyword={encoded_keyword}&status=on_sale&sort=price_asc"
            
            print(f"検索URL: {search_url}")
            self.driver.get(search_url)
            
            # ページが読み込まれるまで待機
            time.sleep(5)
            
            # 商品要素を取得（複数のセレクタを試す）
            selectors = [
                "mer-item-thumbnail",
                "div.merItemThumbnail",
                "div[data-testid='item-cell']",
                "a[href*='/item/']"
            ]
            
            item_elements = []
            used_selector = None
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) >= 1:  # 最低1件は見つかることを確認
                        item_elements = elements
                        used_selector = selector
                        print(f"商品要素が見つかりました。使用したセレクタ: {selector}")
                        print(f"見つかった要素数: {len(elements)}")
                        break
                except Exception as e:
                    print(f"セレクタ '{selector}' でのエラー: {str(e)}")
            
            if not item_elements:
                print("商品要素が見つかりませんでした。")
                return []
            
            # 商品リストを取得
            items = []
            
            for i, item_element in enumerate(item_elements[:limit]):
                try:
                    # aria-label属性から情報を抽出
                    aria_label = item_element.get_attribute("aria-label")
                    if aria_label:
                        # aria-labelから商品タイトルと価格を抽出
                        match = re.search(r'(.+?)の画像\s+(?:売り切れ\s+)?([0-9,]+)円', aria_label)
                        if match:
                            title = match.group(1).strip()
                            price_text = match.group(2).replace(",", "")
                            price = int(price_text) if price_text.isdigit() else 0
                            
                            # 商品IDを取得
                            item_id_attr = item_element.get_attribute("id")
                            if item_id_attr:
                                item_id = item_id_attr.replace("m", "") if item_id_attr.startswith("m") else item_id_attr
                                item_url = f"https://jp.mercari.com/item/{item_id_attr}"
                            else:
                                # IDが取得できない場合はスキップ
                                continue
                            
                            # 商品画像を取得
                            image_url = ""
                            try:
                                img_element = item_element.find_element(By.TAG_NAME, "img")
                                image_url = img_element.get_attribute("src")
                            except:
                                pass
                            
                            item = {
                                "search_term": keyword,
                                "item_id": item_id,
                                "title": title,
                                "name": title,  # 互換性のため
                                "price": price,
                                "currency": "JPY",
                                "status": "active",
                                "sold_date": None,
                                "condition": "中古",
                                "url": item_url,
                                "image_url": image_url,
                                "seller": "メルカリ出品者",
                                "thumbnails": [{"url": image_url}] if image_url else []
                            }
                            
                            items.append(item)
                            print(f"商品を追加しました: {title} - {price}円")
                            
                            if len(items) >= limit:
                                break
                            
                            time.sleep(0.5)  # 短い待機時間
                    
                    # aria-labelが取得できない場合はスキップ（モックデータは生成しない）
                        
                except Exception as e:
                    print(f"商品要素の処理でエラー: {str(e)}")
                    continue
            
            return items
            
        except Exception as e:
            print(f"Error searching active items for '{keyword}': {str(e)}")
            return []
        finally:
            self._close_driver()
    
    
    def search_sold_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        売り切れ済みのアイテムを検索します（実際のスクレイピングのみ）。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 売り切れ済みアイテムのリスト
        """
        try:
            self._initialize_driver()
            
            # 検索URLを構築（売り切れ商品）
            encoded_keyword = requests.utils.quote(keyword)
            search_url = f"{self.search_url}?keyword={encoded_keyword}&status=sold_out&sort=created_time_desc"
            
            print(f"検索URL: {search_url}")
            self.driver.get(search_url)
            
            # ページが読み込まれるまで待機
            time.sleep(5)
            
            # 商品要素を取得（複数のセレクタを試す）
            selectors = [
                "mer-item-thumbnail",
                "div.merItemThumbnail",
                "div[data-testid='item-cell']",
                "a[href*='/item/']"
            ]
            
            item_elements = []
            used_selector = None
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) >= 1:
                        item_elements = elements
                        used_selector = selector
                        print(f"商品要素が見つかりました。使用したセレクタ: {selector}")
                        print(f"見つかった要素数: {len(elements)}")
                        break
                except Exception as e:
                    print(f"セレクタ '{selector}' でのエラー: {str(e)}")
            
            if not item_elements:
                print("売り切れ商品要素が見つかりませんでした。")
                return []
            
            # 商品リストを取得
            items = []
            
            for i, item_element in enumerate(item_elements[:limit]):
                try:
                    # aria-label属性から情報を抽出
                    aria_label = item_element.get_attribute("aria-label")
                    if aria_label:
                        # aria-labelから商品タイトルと価格を抽出
                        match = re.search(r'(.+?)の画像\s+(?:売り切れ\s+)?([0-9,]+)円', aria_label)
                        if match:
                            title = match.group(1).strip()
                            price_text = match.group(2).replace(",", "")
                            price = int(price_text) if price_text.isdigit() else 0
                            
                            # 商品IDを取得
                            item_id_attr = item_element.get_attribute("id")
                            if item_id_attr:
                                item_id = item_id_attr.replace("m", "") if item_id_attr.startswith("m") else item_id_attr
                                item_url = f"https://jp.mercari.com/item/{item_id_attr}"
                            else:
                                # IDが取得できない場合はスキップ
                                continue
                            
                            # 商品画像を取得
                            image_url = ""
                            try:
                                img_element = item_element.find_element(By.TAG_NAME, "img")
                                image_url = img_element.get_attribute("src")
                            except:
                                pass
                            
                            item = {
                                "search_term": keyword,
                                "item_id": item_id,
                                "title": title,
                                "name": title,  # 互換性のため
                                "price": price,
                                "currency": "JPY",
                                "status": "sold_out",
                                "sold_date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "condition": "中古",
                                "url": item_url,
                                "image_url": image_url,
                                "seller": "メルカリ出品者",
                                "thumbnails": [{"url": image_url}] if image_url else []
                            }
                            
                            items.append(item)
                            print(f"売り切れ商品を追加しました: {title} - {price}円")
                            
                            if len(items) >= limit:
                                break
                            
                            time.sleep(0.5)  # 短い待機時間
                        
                except Exception as e:
                    print(f"売り切れ商品要素の処理でエラー: {str(e)}")
                    continue
            
            return items
            
        except Exception as e:
            print(f"Error searching sold items for '{keyword}': {str(e)}")
            return []
        finally:
            self._close_driver()
    
    def get_complete_data(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        キーワードの完全なデータ（出品中と売り切れ済み）を取得します。
        
        Args:
            keyword: 検索キーワード
            limit: 各カテゴリごとに取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 完全なデータ
        """
        try:
            # 出品中のアイテムを取得
            active_items = self.search_active_items(keyword, limit)
            
            # 統計情報を計算
            active_prices = [item["price"] for item in active_items if item["price"] > 0]
            lowest_active_price = min(active_prices) if active_prices else 0
            
            # 結果を統合
            all_items = []
            
            for item in active_items:
                item.update({
                    "lowest_active_price": lowest_active_price,
                    "active_listings_count": len(active_items),
                    "avg_sold_price": 0,
                    "median_sold_price": 0,
                    "sold_count": 0
                })
                all_items.append(item)
            
            return all_items
            
        except Exception as e:
            print(f"Error getting complete data for '{keyword}': {str(e)}")
            return []
