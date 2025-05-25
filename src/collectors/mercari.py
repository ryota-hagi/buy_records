"""
Mercariスクレイピングクライアント
Mercariの商品情報と売却情報をSeleniumを使用してスクレイピングで取得します。
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
    """Mercariからデータをスクレイピングするクライアントクラス"""
    
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
        self.delay = float(get_config("MERCARI_REQUEST_DELAY", "2.0"))
        self.driver = None
        self.chrome_driver_path = "/Users/hagiryouta/Downloads/chromedriver-mac-arm64/chromedriver"
    
    def _initialize_driver(self):
        """Seleniumドライバーを初期化します。"""
        if self.driver is None:
            chrome_options = Options()
            # ヘッドレスモードを無効化
            # chrome_options.add_argument("--headless")
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
    
    def search_active_items(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        出品中のアイテムを検索します。
        
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
            try:
                # ページが完全に読み込まれるまで待機
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # JavaScriptが実行されるまで少し待機
                time.sleep(5)
                
                # 商品要素が存在するか確認（複数のセレクタを試す）
                selectors = [
                    "div[data-testid='item-cell']",  # 古いセレクタ
                    "mer-item-thumbnail, div.merItemThumbnail",  # 古いセレクタ
                    "div.merItemThumbnail",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemName",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemPrice",  # 新しいセレクタの候補
                    "div.merItemThumbnail__item",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemContainer",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemBox",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemCard",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemImage",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemImageContainer",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemImageBox",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemImageCard",  # 新しいセレクタの候補
                    "div.item-card",  # 一般的なセレクタの候補
                    "div.item-box",  # 一般的なセレクタの候補
                    "div.item-container",  # 一般的なセレクタの候補
                    "div.item",  # 一般的なセレクタの候補
                    "div.product-card",  # 一般的なセレクタの候補
                    "div.product-box",  # 一般的なセレクタの候補
                    "div.product-container",  # 一般的なセレクタの候補
                    "div.product",  # 一般的なセレクタの候補
                    "article.item",  # 一般的なセレクタの候補
                    "article.product",  # 一般的なセレクタの候補
                    "a.merItemThumbnail",  # リンク要素の候補
                    "a.merItemThumbnail__item",  # リンク要素の候補
                    "a.merItemThumbnail__itemContainer",  # リンク要素の候補
                    "a.merItemThumbnail__itemBox",  # リンク要素の候補
                    "a.merItemThumbnail__itemCard",  # リンク要素の候補
                    "a.item-card",  # リンク要素の候補
                    "a.item-box",  # リンク要素の候補
                    "a.item-container",  # リンク要素の候補
                    "a.item",  # リンク要素の候補
                    "a.product-card",  # リンク要素の候補
                    "a.product-box",  # リンク要素の候補
                    "a.product-container",  # リンク要素の候補
                    "a.product",  # リンク要素の候補
                    "a[data-testid]",  # data-testid属性を持つリンク要素
                    "a[href*='/item/']",  # 商品ページへのリンク
                    "a[href*='mercari.com/item/']",  # 商品ページへのリンク
                    "a[href*='jp.mercari.com/item/']",  # 商品ページへのリンク
                    "img.item-image",  # 画像要素の候補
                    "img.product-image",  # 画像要素の候補
                    "img.thumbnail",  # 画像要素の候補
                    "img[alt*='商品']",  # 商品画像
                    "img[src*='item']",  # 商品画像
                    "img[src*='product']",  # 商品画像
                    "img[src*='thumbnail']",  # 商品画像
                ]
                
                item_elements = []
                used_selector = None
                
                # 各セレクタを試す
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            item_elements = elements
                            used_selector = selector
                            print(f"商品要素が見つかりました。使用したセレクタ: {selector}")
                            print(f"見つかった要素数: {len(elements)}")
                            break
                    except Exception as e:
                        print(f"セレクタ '{selector}' でのエラー: {str(e)}")
                
                if not item_elements:
                    print("商品要素が見つかりませんでした。ページのHTMLを確認します。")
                    print(f"ページのタイトル: {self.driver.title}")
                    print(f"現在のURL: {self.driver.current_url}")
                    
                    # ページのHTMLを保存（デバッグ用）
                    with open("mercari_page.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print("ページのHTMLを mercari_page.html に保存しました。")
                    
                    return []
            except TimeoutException:
                print("ページの読み込みがタイムアウトしました。アイテムが見つからない可能性があります。")
                return []
            
            # 商品リストを取得
            items = []
            item_count = 0
            
            # 商品要素を取得
            if used_selector:
                item_elements = self.driver.find_elements(By.CSS_SELECTOR, used_selector)
            
            for item_element in item_elements[:limit]:
                try:
                    print(f"商品要素の処理を開始: {item_element}")
                    print(f"商品要素のタグ名: {item_element.tag_name}")
                    print(f"商品要素のHTML: {item_element.get_attribute('outerHTML')[:200]}...")
                    
                    # 商品情報を抽出（セレクタに応じて異なる抽出方法を使用）
                    # aria-label属性から情報を抽出
                    aria_label = item_element.get_attribute("aria-label")
                    if aria_label:
                        print(f"aria-label: {aria_label}")
                        # aria-labelから商品タイトルと価格を抽出
                        # 例: "ATEEZ WILL vinyl LP レコード X ver. ②の画像 5,990円"
                        # または "洋楽レコードLP　2枚セットの画像 売り切れ 4,888円"
                        match = re.search(r'(.+)の画像\s+(?:売り切れ\s+)?([0-9,]+)円', aria_label)
                        if match:
                            title = match.group(1)
                            price_text = match.group(2).replace(",", "")
                            price = int(price_text) if price_text.isdigit() else 0
                            print(f"aria-labelから抽出したタイトル: {title}")
                            print(f"aria-labelから抽出した価格: {price}")
                            
                            # idから商品IDを抽出
                            item_id_attr = item_element.get_attribute("id")
                            if item_id_attr:
                                # "m"で始まる場合は除去、そうでなければそのまま使用
                                if item_id_attr.startswith("m"):
                                    item_id = item_id_attr[1:]
                                else:
                                    item_id = item_id_attr
                                print(f"idから抽出した商品ID: {item_id}")
                                
                                # 商品URLを構築
                                item_url = f"https://jp.mercari.com/item/{item_id_attr}"
                                print(f"構築した商品URL: {item_url}")
                                
                                # 商品画像を取得
                                image_url = ""
                                try:
                                    img_element = item_element.find_element(By.TAG_NAME, "img")
                                    image_url = img_element.get_attribute("src")
                                    print(f"商品画像URL: {image_url}")
                                except:
                                    print("商品画像の取得に失敗しました")
                                
                                item = {
                                    "search_term": keyword,
                                    "item_id": item_id,
                                    "title": title,
                                    "price": price,
                                    "currency": "JPY",
                                    "status": "active",
                                    "sold_date": None,
                                    "condition": "新品",
                                    "url": item_url,
                                    "image_url": image_url,
                                    "seller": "メルカリ出品者"
                                }
                                
                                items.append(item)
                                item_count += 1
                                print(f"商品を追加しました: {title} - {price}円")
                                
                                if item_count >= limit:
                                    break
                                    
                                # APIレート制限対応
                                time.sleep(self.delay)
                                continue
                    
                    if used_selector.startswith("a[href"):
                        # リンク要素の場合
                        item_url = item_element.get_attribute("href")
                        print(f"商品URL: {item_url}")
                        item_id = item_url.split("/")[-1]
                        print(f"商品ID: {item_id}")
                        
                        # 商品タイトルを取得（様々なセレクタを試す）
                        title = ""
                        title_selectors = ["h3", "span.title", "div.title", "span.name", "div.name", ".title", ".name"]
                        for title_selector in title_selectors:
                            try:
                                title_elements = item_element.find_elements(By.CSS_SELECTOR, title_selector)
                                if title_elements:
                                    title = title_elements[0].text
                                    break
                            except:
                                pass
                        
                        # 商品価格を取得（様々なセレクタを試す）
                        price = 0
                        price_selectors = ["span[data-testid='price']", "span.price", "div.price", ".price"]
                        for price_selector in price_selectors:
                            try:
                                price_elements = item_element.find_elements(By.CSS_SELECTOR, price_selector)
                                if price_elements:
                                    price_text = price_elements[0].text.replace("¥", "").replace(",", "")
                                    price = int(price_text) if price_text.isdigit() else 0
                                    break
                            except:
                                pass
                        
                        # 商品画像を取得（様々なセレクタを試す）
                        image_url = ""
                        image_selectors = ["img", "img.thumbnail", "img.item-image", "img.product-image"]
                        for image_selector in image_selectors:
                            try:
                                image_elements = item_element.find_elements(By.CSS_SELECTOR, image_selector)
                                if image_elements:
                                    image_url = image_elements[0].get_attribute("src")
                                    break
                            except:
                                pass
                    
                    elif used_selector.startswith("img"):
                        # 画像要素の場合
                        image_url = item_element.get_attribute("src")
                        
                        # 親要素からリンクを取得
                        parent_element = item_element.find_element(By.XPATH, "./..")
                        while parent_element.tag_name != "a" and parent_element.tag_name != "body":
                            parent_element = parent_element.find_element(By.XPATH, "./..")
                        
                        if parent_element.tag_name == "a":
                            item_url = parent_element.get_attribute("href")
                            item_id = item_url.split("/")[-1]
                        else:
                            # リンクが見つからない場合はスキップ
                            continue
                        
                        # 商品タイトルと価格は親要素から取得
                        title = ""
                        price = 0
                        
                        # 商品タイトルを取得（様々なセレクタを試す）
                        title_selectors = ["h3", "span.title", "div.title", "span.name", "div.name", ".title", ".name"]
                        for title_selector in title_selectors:
                            try:
                                title_elements = parent_element.find_elements(By.CSS_SELECTOR, title_selector)
                                if title_elements:
                                    title = title_elements[0].text
                                    break
                            except:
                                pass
                        
                        # 商品価格を取得（様々なセレクタを試す）
                        price_selectors = ["span[data-testid='price']", "span.price", "div.price", ".price"]
                        for price_selector in price_selectors:
                            try:
                                price_elements = parent_element.find_elements(By.CSS_SELECTOR, price_selector)
                                if price_elements:
                                    price_text = price_elements[0].text.replace("¥", "").replace(",", "")
                                    price = int(price_text) if price_text.isdigit() else 0
                                    break
                            except:
                                pass
                    
                    else:
                        # 通常の要素の場合
                        # 商品情報を抽出
                        try:
                            item_url_element = item_element.find_element(By.CSS_SELECTOR, "a")
                            item_url = item_url_element.get_attribute("href")
                            item_id = item_url.split("/")[-1]
                        except:
                            # リンクが見つからない場合は、親要素を探す
                            try:
                                parent_element = item_element.find_element(By.XPATH, "./..")
                                item_url_element = parent_element.find_element(By.CSS_SELECTOR, "a")
                                item_url = item_url_element.get_attribute("href")
                                item_id = item_url.split("/")[-1]
                            except:
                                # それでも見つからない場合はスキップ
                                continue
                        
                        # 商品タイトル
                        title = ""
                        title_selectors = ["h3", "span.title", "div.title", "span.name", "div.name", ".title", ".name"]
                        for title_selector in title_selectors:
                            try:
                                title_elements = item_element.find_elements(By.CSS_SELECTOR, title_selector)
                                if title_elements:
                                    title = title_elements[0].text
                                    break
                            except:
                                pass
                        
                        # 商品価格
                        price = 0
                        price_selectors = ["span[data-testid='price']", "span.price", "div.price", ".price"]
                        for price_selector in price_selectors:
                            try:
                                price_elements = item_element.find_elements(By.CSS_SELECTOR, price_selector)
                                if price_elements:
                                    price_text = price_elements[0].text.replace("¥", "").replace(",", "")
                                    price = int(price_text) if price_text.isdigit() else 0
                                    break
                            except:
                                pass
                        
                        # 商品画像
                        image_url = ""
                        image_selectors = ["img", "img.thumbnail", "img.item-image", "img.product-image"]
                        for image_selector in image_selectors:
                            try:
                                image_elements = item_element.find_elements(By.CSS_SELECTOR, image_selector)
                                if image_elements:
                                    image_url = image_elements[0].get_attribute("src")
                                    break
                            except:
                                pass
                    
                    # 商品詳細ページにアクセスして追加情報を取得
                    try:
                        item_details = self._get_item_details(item_url)
                        
                        # 検索結果ページに戻る（stale element referenceエラー対策）
                        self.driver.back()
                        time.sleep(2)  # ページが読み込まれるまで待機
                    except Exception as e:
                        print(f"商品詳細の取得に失敗しました: {str(e)}")
                        item_details = {
                            "condition": "",
                            "seller": "",
                            "sold_date": None
                        }
                    
                    item = {
                        "search_term": keyword,
                        "item_id": item_id,
                        "title": title,
                        "price": price,
                        "currency": "JPY",
                        "status": "active",
                        "sold_date": None,
                        "condition": item_details.get("condition", ""),
                        "url": item_url,
                        "image_url": image_url,
                        "seller": item_details.get("seller", "")
                    }
                    
                    items.append(item)
                    item_count += 1
                    
                    if item_count >= limit:
                        break
                        
                    # APIレート制限対応
                    time.sleep(self.delay)
                    
                except Exception as e:
                    print(f"Error extracting item data: {str(e)}")
                    continue
            
            return items
        except Exception as e:
            print(f"Error searching active items for '{keyword}': {str(e)}")
            return []
    
    def search_sold_items(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        売り切れ済みのアイテムを検索します。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 売り切れ済みアイテムのリスト
        """
        try:
            self._initialize_driver()
            
            # 検索URLを構築
            encoded_keyword = requests.utils.quote(keyword)
            search_url = f"{self.search_url}?keyword={encoded_keyword}&status=sold_out&sort=created_time_desc"
            
            print(f"検索URL: {search_url}")
            self.driver.get(search_url)
            
            # ページが読み込まれるまで待機
            try:
                # ページが完全に読み込まれるまで待機
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # JavaScriptが実行されるまで少し待機
                time.sleep(5)
                
                # 商品要素が存在するか確認（複数のセレクタを試す）
                selectors = [
                    "div[data-testid='item-cell']",  # 古いセレクタ
                    "mer-item-thumbnail, div.merItemThumbnail",  # 古いセレクタ
                    "div.merItemThumbnail",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemName",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemPrice",  # 新しいセレクタの候補
                    "div.merItemThumbnail__item",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemContainer",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemBox",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemCard",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemImage",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemImageContainer",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemImageBox",  # 新しいセレクタの候補
                    "div.merItemThumbnail__itemImageCard",  # 新しいセレクタの候補
                    "div.item-card",  # 一般的なセレクタの候補
                    "div.item-box",  # 一般的なセレクタの候補
                    "div.item-container",  # 一般的なセレクタの候補
                    "div.item",  # 一般的なセレクタの候補
                    "div.product-card",  # 一般的なセレクタの候補
                    "div.product-box",  # 一般的なセレクタの候補
                    "div.product-container",  # 一般的なセレクタの候補
                    "div.product",  # 一般的なセレクタの候補
                    "article.item",  # 一般的なセレクタの候補
                    "article.product",  # 一般的なセレクタの候補
                    "a.merItemThumbnail",  # リンク要素の候補
                    "a.merItemThumbnail__item",  # リンク要素の候補
                    "a.merItemThumbnail__itemContainer",  # リンク要素の候補
                    "a.merItemThumbnail__itemBox",  # リンク要素の候補
                    "a.merItemThumbnail__itemCard",  # リンク要素の候補
                    "a.item-card",  # リンク要素の候補
                    "a.item-box",  # リンク要素の候補
                    "a.item-container",  # リンク要素の候補
                    "a.item",  # リンク要素の候補
                    "a.product-card",  # リンク要素の候補
                    "a.product-box",  # リンク要素の候補
                    "a.product-container",  # リンク要素の候補
                    "a.product",  # リンク要素の候補
                    "a[data-testid]",  # data-testid属性を持つリンク要素
                    "a[href*='/item/']",  # 商品ページへのリンク
                    "a[href*='mercari.com/item/']",  # 商品ページへのリンク
                    "a[href*='jp.mercari.com/item/']",  # 商品ページへのリンク
                    "img.item-image",  # 画像要素の候補
                    "img.product-image",  # 画像要素の候補
                    "img.thumbnail",  # 画像要素の候補
                    "img[alt*='商品']",  # 商品画像
                    "img[src*='item']",  # 商品画像
                    "img[src*='product']",  # 商品画像
                    "img[src*='thumbnail']",  # 商品画像
                ]
                
                item_elements = []
                used_selector = None
                
                # 各セレクタを試す
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            item_elements = elements
                            used_selector = selector
                            print(f"商品要素が見つかりました。使用したセレクタ: {selector}")
                            print(f"見つかった要素数: {len(elements)}")
                            break
                    except Exception as e:
                        print(f"セレクタ '{selector}' でのエラー: {str(e)}")
                
                if not item_elements:
                    print("商品要素が見つかりませんでした。ページのHTMLを確認します。")
                    print(f"ページのタイトル: {self.driver.title}")
                    print(f"現在のURL: {self.driver.current_url}")
                    
                    # ページのHTMLを保存（デバッグ用）
                    with open("mercari_sold_page.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print("ページのHTMLを mercari_sold_page.html に保存しました。")
                    
                    return []
            except TimeoutException:
                print("ページの読み込みがタイムアウトしました。アイテムが見つからない可能性があります。")
                return []
            
            # 商品リストを取得
            items = []
            item_count = 0
            
            # 商品要素を取得
            if used_selector:
                item_elements = self.driver.find_elements(By.CSS_SELECTOR, used_selector)
            
            for item_element in item_elements[:limit]:
                try:
                    print(f"商品要素の処理を開始: {item_element}")
                    print(f"商品要素のタグ名: {item_element.tag_name}")
                    print(f"商品要素のHTML: {item_element.get_attribute('outerHTML')[:200]}...")
                    
                    # 商品情報を抽出（セレクタに応じて異なる抽出方法を使用）
                    # aria-label属性から情報を抽出
                    aria_label = item_element.get_attribute("aria-label")
                    if aria_label:
                        print(f"aria-label: {aria_label}")
                        # aria-labelから商品タイトルと価格を抽出
                        # 例: "ATEEZ WILL vinyl LP レコード X ver. ②の画像 5,990円"
                        # または "洋楽レコードLP　2枚セットの画像 売り切れ 4,888円"
                        match = re.search(r'(.+)の画像\s+(?:売り切れ\s+)?([0-9,]+)円', aria_label)
                        if match:
                            title = match.group(1)
                            price_text = match.group(2).replace(",", "")
                            price = int(price_text) if price_text.isdigit() else 0
                            print(f"aria-labelから抽出したタイトル: {title}")
                            print(f"aria-labelから抽出した価格: {price}")
                        
                        # idから商品IDを抽出
                        item_id_attr = item_element.get_attribute("id")
                        if item_id_attr and item_id_attr.startswith("m"):
                            item_id = item_id_attr[1:]  # "m"を除去
                            print(f"idから抽出した商品ID: {item_id}")
                            
                            # 商品URLを直接取得
                            item_url = ""
                            try:
                                # 親要素を探索して、リンク要素を見つける
                                parent_element = item_element
                                for _ in range(5):  # 最大5階層まで親要素を探索
                                    try:
                                        # 現在の要素内のリンクを探す
                                        link_elements = parent_element.find_elements(By.TAG_NAME, "a")
                                        if link_elements:
                                            item_url = link_elements[0].get_attribute("href")
                                            if item_url and ("/item/" in item_url or "/items/" in item_url):
                                                print(f"商品URLを取得しました: {item_url}")
                                                break
                                        
                                        # 親要素に移動
                                        parent_element = parent_element.find_element(By.XPATH, "./..")
                                    except:
                                        break
                                
                                # リンクが見つからない場合は、子要素も探索
                                if not item_url:
                                    link_elements = item_element.find_elements(By.TAG_NAME, "a")
                                    if link_elements:
                                        item_url = link_elements[0].get_attribute("href")
                                        print(f"子要素から商品URLを取得しました: {item_url}")
                            except Exception as e:
                                print(f"商品URLの取得に失敗しました: {str(e)}")
                            
                            # URLが取得できなかった場合は、IDから構築する（フォールバック）
                            if not item_url:
                                print(f"商品URLが取得できなかったため、IDから構築します: {item_id}")
                                item_url = f"https://jp.mercari.com/item/{item_id}"
                                print(f"構築した商品URL: {item_url}")
                            
                            # 商品画像を取得
                            image_url = ""
                            try:
                                img_element = item_element.find_element(By.TAG_NAME, "img")
                                image_url = img_element.get_attribute("src")
                                print(f"商品画像URL: {image_url}")
                            except:
                                print("商品画像の取得に失敗しました")
                            
                            # 商品詳細ページにアクセスして追加情報を取得
                            try:
                                item_details = self._get_item_details(item_url)
                                
                                # 検索結果ページに戻る（stale element referenceエラー対策）
                                self.driver.back()
                                time.sleep(2)  # ページが読み込まれるまで待機
                            except Exception as e:
                                print(f"商品詳細の取得に失敗しました: {str(e)}")
                                item_details = {
                                    "condition": "",
                                    "seller": "",
                                    "sold_date": None
                                }
                            
                            # 売却日時（詳細ページから取得）
                            sold_date = item_details.get("sold_date")
                            
                            item = {
                                "search_term": keyword,
                                "item_id": item_id,
                                "title": title,
                                "price": price,
                                "currency": "JPY",
                                "status": "sold_out",
                                "sold_date": sold_date,
                                "condition": item_details.get("condition", ""),
                                "url": item_url,
                                "image_url": image_url,
                                "seller": item_details.get("seller", "")
                            }
                            
                            items.append(item)
                            item_count += 1
                            
                            if item_count >= limit:
                                break
                                
                            # APIレート制限対応
                            time.sleep(self.delay)
                            continue
                    
                    if used_selector.startswith("a[href"):
                        # リンク要素の場合
                        item_url = item_element.get_attribute("href")
                        item_id = item_url.split("/")[-1]
                        
                        # 商品タイトルを取得（様々なセレクタを試す）
                        title = ""
                        title_selectors = ["h3", "span.title", "div.title", "span.name", "div.name", ".title", ".name"]
                        for title_selector in title_selectors:
                            try:
                                title_elements = item_element.find_elements(By.CSS_SELECTOR, title_selector)
                                if title_elements:
                                    title = title_elements[0].text
                                    break
                            except:
                                pass
                        
                        # 商品価格を取得（様々なセレクタを試す）
                        price = 0
                        price_selectors = ["span[data-testid='price']", "span.price", "div.price", ".price"]
                        for price_selector in price_selectors:
                            try:
                                price_elements = item_element.find_elements(By.CSS_SELECTOR, price_selector)
                                if price_elements:
                                    price_text = price_elements[0].text.replace("¥", "").replace(",", "")
                                    price = int(price_text) if price_text.isdigit() else 0
                                    break
                            except:
                                pass
                        
                        # 商品画像を取得（様々なセレクタを試す）
                        image_url = ""
                        image_selectors = ["img", "img.thumbnail", "img.item-image", "img.product-image"]
                        for image_selector in image_selectors:
                            try:
                                image_elements = item_element.find_elements(By.CSS_SELECTOR, image_selector)
                                if image_elements:
                                    image_url = image_elements[0].get_attribute("src")
                                    break
                            except:
                                pass
                    
                    elif used_selector.startswith("img"):
                        # 画像要素の場合
                        image_url = item_element.get_attribute("src")
                        
                        # 親要素からリンクを取得
                        parent_element = item_element.find_element(By.XPATH, "./..")
                        while parent_element.tag_name != "a" and parent_element.tag_name != "body":
                            parent_element = parent_element.find_element(By.XPATH, "./..")
                        
                        if parent_element.tag_name == "a":
                            item_url = parent_element.get_attribute("href")
                            item_id = item_url.split("/")[-1]
                        else:
                            # リンクが見つからない場合はスキップ
                            continue
                        
                        # 商品タイトルと価格は親要素から取得
                        title = ""
                        price = 0
                        
                        # 商品タイトルを取得（様々なセレクタを試す）
                        title_selectors = ["h3", "span.title", "div.title", "span.name", "div.name", ".title", ".name"]
                        for title_selector in title_selectors:
                            try:
                                title_elements = parent_element.find_elements(By.CSS_SELECTOR, title_selector)
                                if title_elements:
                                    title = title_elements[0].text
                                    break
                            except:
                                pass
                        
                        # 商品価格を取得（様々なセレクタを試す）
                        price_selectors = ["span[data-testid='price']", "span.price", "div.price", ".price"]
                        for price_selector in price_selectors:
                            try:
                                price_elements = parent_element.find_elements(By.CSS_SELECTOR, price_selector)
                                if price_elements:
                                    price_text = price_elements[0].text.replace("¥", "").replace(",", "")
                                    price = int(price_text) if price_text.isdigit() else 0
                                    break
                            except:
                                pass
                    
                    else:
                        # 通常の要素の場合
                        # 商品情報を抽出
                        try:
                            item_url_element = item_element.find_element(By.CSS_SELECTOR, "a")
                            item_url = item_url_element.get_attribute("href")
                            item_id = item_url.split("/")[-1]
                        except:
                            # リンクが見つからない場合は、親要素を探す
                            try:
                                parent_element = item_element.find_element(By.XPATH, "./..")
                                item_url_element = parent_element.find_element(By.CSS_SELECTOR, "a")
                                item_url = item_url_element.get_attribute("href")
                                item_id = item_url.split("/")[-1]
                            except:
                                # それでも見つからない場合はスキップ
                                continue
                        
                        # 商品タイトル
                        title = ""
                        title_selectors = ["h3", "span.title", "div.title", "span.name", "div.name", ".title", ".name"]
                        for title_selector in title_selectors:
                            try:
                                title_elements = item_element.find_elements(By.CSS_SELECTOR, title_selector)
                                if title_elements:
                                    title = title_elements[0].text
                                    break
                            except:
                                pass
                        
                        # 商品価格
                        price = 0
                        price_selectors = ["span[data-testid='price']", "span.price", "div.price", ".price"]
                        for price_selector in price_selectors:
                            try:
                                price_elements = item_element.find_elements(By.CSS_SELECTOR, price_selector)
                                if price_elements:
                                    price_text = price_elements[0].text.replace("¥", "").replace(",", "")
                                    price = int(price_text) if price_text.isdigit() else 0
                                    break
                            except:
                                pass
                        
                        # 商品画像
                        image_url = ""
                        image_selectors = ["img", "img.thumbnail", "img.item-image", "img.product-image"]
                        for image_selector in image_selectors:
                            try:
                                image_elements = item_element.find_elements(By.CSS_SELECTOR, image_selector)
                                if image_elements:
                                    image_url = image_elements[0].get_attribute("src")
                                    break
                            except:
                                pass
                    
                    # 商品詳細ページにアクセスして追加情報を取得
                    try:
                        item_details = self._get_item_details(item_url)
                        
                        # 検索結果ページに戻る（stale element referenceエラー対策）
                        self.driver.back()
                        time.sleep(2)  # ページが読み込まれるまで待機
                    except Exception as e:
                        print(f"商品詳細の取得に失敗しました: {str(e)}")
                        item_details = {
                            "condition": "",
                            "seller": "",
                            "sold_date": None
                        }
                    
                    # 売却日時（詳細ページから取得）
                    sold_date = item_details.get("sold_date")
                    
                    item = {
                        "search_term": keyword,
                        "item_id": item_id,
                        "title": title,
                        "price": price,
                        "currency": "JPY",
                        "status": "sold_out",
                        "sold_date": sold_date,
                        "condition": item_details.get("condition", ""),
                        "url": item_url,
                        "image_url": image_url,
                        "seller": item_details.get("seller", "")
                    }
                    
                    items.append(item)
                    item_count += 1
                    
                    if item_count >= limit:
                        break
                        
                    # APIレート制限対応
                    time.sleep(self.delay)
                    
                except Exception as e:
                    print(f"Error extracting item data: {str(e)}")
                    continue
            
            return items
        except Exception as e:
            print(f"Error searching sold items for '{keyword}': {str(e)}")
            return []
    
    def _get_item_details(self, item_url: str) -> Dict[str, Any]:
        """
        商品詳細ページから追加情報を取得します。
        
        Args:
            item_url: 商品詳細ページのURL
            
        Returns:
            Dict[str, Any]: 商品の追加情報
        """
        details = {
            "condition": "",
            "seller": "",
            "sold_date": None
        }
        
        try:
            self.driver.get(item_url)
            
            # ページが読み込まれるまで待機
            try:
                # ページが完全に読み込まれるまで待機
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # JavaScriptが実行されるまで少し待機
                time.sleep(5)
                
                # 商品情報セクションが存在するか確認
                info_elements = self.driver.find_elements(By.CSS_SELECTOR, "section[data-testid='商品の情報']")
                if not info_elements:
                    # 別のセレクタも試してみる
                    info_elements = self.driver.find_elements(By.CSS_SELECTOR, "table.mer-table")
                    if not info_elements:
                        print("商品情報セクションが見つかりませんでした。ページのHTMLを確認します。")
                        print(f"ページのタイトル: {self.driver.title}")
                        print(f"現在のURL: {self.driver.current_url}")
                        
                        # ページのHTMLを保存（デバッグ用）
                        with open("mercari_detail_page.html", "w", encoding="utf-8") as f:
                            f.write(self.driver.page_source)
                        print("ページのHTMLを mercari_detail_page.html に保存しました。")
                        
                        return details
            except TimeoutException:
                print("詳細ページの読み込みがタイムアウトしました。")
                return details
            
            # 商品の状態を取得
            try:
                condition_elements = self.driver.find_elements(By.XPATH, "//th[contains(text(), '商品の状態')]/following-sibling::td")
                if condition_elements:
                    details["condition"] = condition_elements[0].text
            except NoSuchElementException:
                pass
            
            # 出品者を取得
            try:
                seller_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[data-testid='seller-name']")
                if seller_elements:
                    details["seller"] = seller_elements[0].text
            except NoSuchElementException:
                pass
            
            # 売却日時を取得（売り切れ商品の場合）
            try:
                sold_elements = self.driver.find_elements(By.XPATH, "//p[contains(text(), '売り切れました')]")
                if sold_elements:
                    details["sold_date"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            except NoSuchElementException:
                pass
            
        except Exception as e:
            print(f"Error getting item details from {item_url}: {str(e)}")
        
        return details
    
    def get_complete_data(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        キーワードの完全なデータ（出品中と売り切れ済み）を取得します。
        
        Args:
            keyword: 検索キーワード
            limit: 各カテゴリ（出品中・売り切れ済み）ごとに取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 完全なデータ
        """
        try:
            self._initialize_driver()
            
            # 出品中のアイテムを取得
            print(f"出品中のアイテムを取得中...")
            active_items = self.search_active_items(keyword, limit)
            print(f"出品中のアイテム数: {len(active_items)}")
            if active_items:
                print(f"最初の出品中アイテム: {active_items[0]}")
            time.sleep(self.delay)  # APIレート制限対応
            
            # 売り切れ済みのアイテムを取得
            print(f"売り切れ済みのアイテムを取得中...")
            sold_items = self.search_sold_items(keyword, limit)
            print(f"売り切れ済みのアイテム数: {len(sold_items)}")
            if sold_items:
                print(f"最初の売り切れ済みアイテム: {sold_items[0]}")
            
            # 統計情報を計算
            active_prices = [item["price"] for item in active_items if item["price"] > 0]
            sold_prices = [item["price"] for item in sold_items if item["price"] > 0]
            
            lowest_active_price = min(active_prices) if active_prices else 0
            avg_sold_price = sum(sold_prices) / len(sold_prices) if sold_prices else 0
            
            # 中央値を計算
            median_sold_price = 0
            if sold_prices:
                sold_prices.sort()
                mid = len(sold_prices) // 2
                if len(sold_prices) % 2 == 0 and len(sold_prices) > 1:
                    median_sold_price = (sold_prices[mid - 1] + sold_prices[mid]) / 2
                else:
                    median_sold_price = sold_prices[mid]
            
            # 結果を統合
            all_items = []
            
            # 出品中アイテムに統計情報を追加
            for item in active_items:
                # URLが空の場合はスキップ（モックデータを除外）
                if not item.get("url"):
                    continue
                    
                item.update({
                    "lowest_active_price": lowest_active_price,
                    "active_listings_count": len(active_items),
                    "avg_sold_price": round(avg_sold_price, 2),
                    "median_sold_price": round(median_sold_price, 2),
                    "sold_count": len(sold_items)
                })
                all_items.append(item)
            
            # 売り切れ済みアイテムに統計情報を追加
            for item in sold_items:
                # URLが空の場合はスキップ（モックデータを除外）
                if not item.get("url"):
                    continue
                    
                item.update({
                    "lowest_active_price": lowest_active_price,
                    "active_listings_count": len(active_items),
                    "avg_sold_price": round(avg_sold_price, 2),
                    "median_sold_price": round(median_sold_price, 2),
                    "sold_count": len(sold_items)
                })
                all_items.append(item)
            
            # データがない場合は空のリストを返す
            if not all_items:
                print(f"'{keyword}'の検索結果はありませんでした。")
            
            return all_items
        except Exception as e:
            print(f"Error getting complete data for '{keyword}': {str(e)}")
            return []
        finally:
            self._close_driver()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mercari.py <search_query> [limit]")
        sys.exit(1)
    
    search_query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    try:
        from .mercari_simple import MercariSimpleClient
        client = MercariSimpleClient()
        results = client.search_active_items(search_query, limit)
        
        # JSON形式で出力
        import json
        print(json.dumps(results, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
