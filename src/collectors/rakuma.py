"""
Rakumaスクレイピングクライアント
RakumaをDOM解析でスクレイピングして商品情報を取得します。
"""

import time
import requests
from typing import List, Dict, Any, Optional
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import os
import sys
from datetime import datetime

class RakumaClient:
    """Rakumaからデータをスクレイピングするクライアントクラス"""
    
    def __init__(self):
        """
        RakumaClientを初期化します。
        """
        self.base_url = "https://fril.jp"
        self.search_url = f"{self.base_url}/s"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        self.delay = 2.5  # レート制限対策
        self.driver = None
        self.chrome_driver_path = self._get_chrome_driver_path()
    
    def _get_chrome_driver_path(self):
        """ChromeDriverのパスを環境に応じて取得"""
        # Docker環境の場合
        if os.path.exists('/usr/bin/chromedriver'):
            return '/usr/bin/chromedriver'
        # ローカル環境の場合
        elif os.path.exists('/Users/hagiryouta/Downloads/chromedriver-mac-arm64/chromedriver'):
            return '/Users/hagiryouta/Downloads/chromedriver-mac-arm64/chromedriver'
        else:
            # システムパスから探す
            return 'chromedriver'
    
    def _initialize_driver(self):
        """Seleniumドライバーを初期化します。"""
        if self.driver is None:
            chrome_options = Options()
            # ヘッドレスモード
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            try:
                service = Service(executable_path=self.chrome_driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                # ChromeDriverが見つからない場合は、引数なしで試す
                self.driver = webdriver.Chrome(options=chrome_options)
    
    def _close_driver(self):
        """Seleniumドライバーを閉じます。"""
        if self.driver is not None:
            self.driver.quit()
            self.driver = None
    
    def _extract_price(self, price_text: str) -> int:
        """価格テキストから数値を抽出"""
        if not price_text:
            return 0
        # ¥や,を除去して数値を抽出
        price_text = re.sub(r'[¥￥,\s円]', '', price_text)
        match = re.search(r'\d+', price_text)
        return int(match.group()) if match else 0
    
    def _normalize_condition(self, condition: str) -> str:
        """商品状態を正規化"""
        if not condition:
            return "中古"
        
        condition_map = {
            '新品': '新品',
            '未使用': '未使用に近い',
            '目立った傷': '目立った傷や汚れなし',
            'やや傷': 'やや傷や汚れあり',
            '傷や汚れ': '傷や汚れあり',
            '状態が悪い': '全体的に状態が悪い',
        }
        
        for key, value in condition_map.items():
            if key in condition:
                return value
        
        return condition
    
    def search_active_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
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
            
            # 検索URLを構築（status=1は販売中）
            encoded_keyword = requests.utils.quote(keyword)
            search_url = f"{self.search_url}?query={encoded_keyword}&sort=price_asc&status=1"
            
            print(f"Rakuma検索URL: {search_url}", file=sys.stderr)
            self.driver.get(search_url)
            
            # ページが読み込まれるまで待機
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(3)  # JavaScriptの実行を待つ
                
                # 商品要素のセレクタ候補
                selectors = [
                    "div.item",
                    "div.item-box",
                    "article.item-box",
                    "div.items-box-content",
                    "section.items-box",
                    "a[href*='/item/']",
                    "div[data-testid='item']",
                    ".item-card",
                    ".product-item",
                    "div.c-item-card",
                    "div.p-item",
                    "li.item",
                    "li[data-item-id]"
                ]
                
                item_elements = []
                used_selector = None
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            item_elements = elements
                            used_selector = selector
                            print(f"商品要素が見つかりました: {selector} ({len(elements)}件)", file=sys.stderr)
                            break
                    except Exception:
                        continue
                
                if not item_elements:
                    print("商品要素が見つかりませんでした", file=sys.stderr)
                    return []
                
            except TimeoutException:
                print("ページの読み込みがタイムアウトしました", file=sys.stderr)
                return []
            
            # 商品情報を抽出
            items = []
            for i, element in enumerate(item_elements[:limit]):
                if i >= limit:
                    break
                    
                try:
                    item_data = {}
                    
                    # 商品URL
                    url = ""
                    link_selectors = ["a", "a[href*='/item/']", ".item-link"]
                    for link_sel in link_selectors:
                        try:
                            link = element.find_element(By.CSS_SELECTOR, link_sel)
                            url = link.get_attribute("href")
                            if url and "/item/" in url:
                                break
                        except:
                            continue
                    
                    if not url:
                        # 親要素から探す
                        try:
                            parent = element.find_element(By.XPATH, "..")
                            if parent.tag_name == "a":
                                url = parent.get_attribute("href")
                        except:
                            pass
                    
                    if not url:
                        continue
                    
                    # 商品ID
                    item_id_match = re.search(r'/item/([a-zA-Z0-9]+)', url)
                    item_id = item_id_match.group(1) if item_id_match else ""
                    
                    # 商品タイトル
                    title = ""
                    title_selectors = [
                        ".item-name", 
                        ".item-title",
                        "h3",
                        "p.item-box__item-name",
                        ".c-item-card__name",
                        "[data-testid='item-name']"
                    ]
                    for title_sel in title_selectors:
                        try:
                            title_elem = element.find_element(By.CSS_SELECTOR, title_sel)
                            title = title_elem.text.strip()
                            if title:
                                break
                        except:
                            continue
                    
                    # alt属性からも試す
                    if not title:
                        try:
                            img = element.find_element(By.TAG_NAME, "img")
                            title = img.get_attribute("alt") or ""
                        except:
                            pass
                    
                    # 価格
                    price = 0
                    price_selectors = [
                        ".item-price",
                        ".item-box__item-price",
                        ".c-item-card__price",
                        "span.price",
                        "[data-testid='item-price']"
                    ]
                    for price_sel in price_selectors:
                        try:
                            price_elem = element.find_element(By.CSS_SELECTOR, price_sel)
                            price_text = price_elem.text
                            price = self._extract_price(price_text)
                            if price > 0:
                                break
                        except:
                            continue
                    
                    # 画像URL
                    image_url = ""
                    try:
                        img = element.find_element(By.TAG_NAME, "img")
                        image_url = img.get_attribute("src") or ""
                        # data-srcもチェック（遅延読み込み対応）
                        if not image_url or "data:" in image_url:
                            image_url = img.get_attribute("data-src") or ""
                    except:
                        pass
                    
                    # 送料
                    shipping_fee = 0
                    try:
                        shipping_elem = element.find_element(By.CSS_SELECTOR, ".shipping-fee, .item-shipping")
                        shipping_text = shipping_elem.text
                        if "送料込み" in shipping_text or "送料無料" in shipping_text:
                            shipping_fee = 0
                        else:
                            shipping_fee = self._extract_price(shipping_text)
                    except:
                        # デフォルトは送料込み
                        shipping_fee = 0
                    
                    # 商品状態（詳細ページから取得する必要がある場合もある）
                    condition = "中古"
                    try:
                        condition_elem = element.find_element(By.CSS_SELECTOR, ".item-condition, .condition")
                        condition = self._normalize_condition(condition_elem.text)
                    except:
                        pass
                    
                    # 出品者名
                    seller_name = ""
                    try:
                        seller_elem = element.find_element(By.CSS_SELECTOR, ".seller-name, .user-name")
                        seller_name = seller_elem.text.strip()
                    except:
                        pass
                    
                    item = {
                        "item_id": item_id,
                        "title": title,
                        "url": url,
                        "image_url": image_url,
                        "price": price,
                        "shipping_fee": shipping_fee,
                        "condition": condition,
                        "seller_name": seller_name or "ラクマ出品者",
                        "location": "日本",
                        "is_sold": False
                    }
                    
                    items.append(item)
                    
                    # レート制限対策
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"商品情報の抽出エラー: {str(e)}", file=sys.stderr)
                    continue
            
            return items
            
        except Exception as e:
            print(f"Rakuma検索エラー: {str(e)}", file=sys.stderr)
            return []
        finally:
            self._close_driver()


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("Usage: python rakuma.py <search_query> [limit]", file=sys.stderr)
        sys.exit(1)
    
    search_query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    client = RakumaClient()
    results = client.search_active_items(search_query, limit)
    
    # 結果をJSON形式で出力
    output = {
        "results": results,
        "metadata": {
            "query": search_query,
            "total_results": len(results),
            "platform": "rakuma",
            "timestamp": datetime.now().isoformat()
        },
        "method": "dom_parsing"
    }
    
    # JSON_STARTとJSON_ENDマーカーで囲んで出力
    print("JSON_START")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("JSON_END")


if __name__ == "__main__":
    main()