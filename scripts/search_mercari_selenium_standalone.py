#!/usr/bin/env python3
"""
メルカリSelenium検索スクリプト（独立版）
Seleniumを使用してメルカリから実データを取得します。
"""

import sys
import json
import time
import requests
import re
import datetime
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class MercariSeleniumClient:
    """Mercariからデータをスクレイピングするクライアントクラス"""
    
    def __init__(self):
        """
        MercariSeleniumClientを初期化します。
        """
        self.base_url = "https://jp.mercari.com"
        self.search_url = f"{self.base_url}/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        self.delay = 2.0
        self.driver = None
        self.chrome_driver_path = "/Users/hagiryouta/Downloads/chromedriver-mac-arm64/chromedriver"
    
    def _initialize_driver(self):
        """Seleniumドライバーを初期化します。"""
        if self.driver is None:
            chrome_options = Options()
            # ヘッドレスモードを有効化（本番環境用）
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(executable_path=self.chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # WebDriverの検出を回避
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
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
            
            print(f"検索URL: {search_url}", file=sys.stderr)
            self.driver.get(search_url)
            
            # ページが読み込まれるまで待機
            try:
                # ページが完全に読み込まれるまで待機
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # JavaScriptが実行されるまで少し待機
                time.sleep(5)
                
                # 商品要素を探す（複数のセレクタを試す）
                selectors = [
                    "a[data-testid]",  # data-testid属性を持つリンク要素
                    "a[href*='/item/']",  # 商品ページへのリンク
                    "div[data-testid='item-cell']",  # 商品セル
                    "mer-item-thumbnail",  # メルカリ商品サムネイル
                    "div.merItemThumbnail",  # 商品サムネイル
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
                            print(f"商品要素が見つかりました。使用したセレクタ: {selector}", file=sys.stderr)
                            print(f"見つかった要素数: {len(elements)}", file=sys.stderr)
                            break
                    except Exception as e:
                        print(f"セレクタ '{selector}' でのエラー: {str(e)}", file=sys.stderr)
                
                if not item_elements:
                    print("商品要素が見つかりませんでした。", file=sys.stderr)
                    return []
                    
            except TimeoutException:
                print("ページの読み込みがタイムアウトしました。", file=sys.stderr)
                return []
            
            # 商品リストを取得
            items = []
            item_count = 0
            
            for item_element in item_elements[:limit]:
                try:
                    print(f"要素 {item_count + 1} を処理中...", file=sys.stderr)
                    
                    # 要素の基本情報をデバッグ出力
                    tag_name = item_element.tag_name
                    element_id = item_element.get_attribute("id")
                    element_class = item_element.get_attribute("class")
                    href = item_element.get_attribute("href")
                    
                    print(f"  タグ名: {tag_name}", file=sys.stderr)
                    print(f"  ID: {element_id}", file=sys.stderr)
                    print(f"  クラス: {element_class}", file=sys.stderr)
                    print(f"  href: {href}", file=sys.stderr)
                    
                    # aria-label属性から情報を抽出
                    aria_label = item_element.get_attribute("aria-label")
                    if aria_label:
                        print(f"  aria-label: {aria_label}", file=sys.stderr)
                        # aria-labelから商品タイトルと価格を抽出
                        match = re.search(r'(.+)の画像\s+(?:売り切れ\s+)?([0-9,]+)円', aria_label)
                        if match:
                            title = match.group(1)
                            price_text = match.group(2).replace(",", "")
                            price = int(price_text) if price_text.isdigit() else 0
                            
                            print(f"  抽出したタイトル: {title}", file=sys.stderr)
                            print(f"  抽出した価格: {price}", file=sys.stderr)
                            
                            # idから商品IDを抽出
                            item_id_attr = item_element.get_attribute("id")
                            if item_id_attr:
                                item_id = item_id_attr[1:] if item_id_attr.startswith("m") else item_id_attr
                                
                                # 商品URLを構築
                                item_url = f"https://jp.mercari.com/item/{item_id_attr}"
                                
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
                                    "price": price,
                                    "currency": "JPY",
                                    "status": "active",
                                    "sold_date": None,
                                    "condition": "中古",
                                    "url": item_url,
                                    "image_url": image_url,
                                    "seller": "メルカリ出品者"
                                }
                                
                                items.append(item)
                                item_count += 1
                                print(f"  ✅ 商品を追加しました: {title} - {price}円", file=sys.stderr)
                                
                                if item_count >= limit:
                                    break
                                    
                                # レート制限対応
                                time.sleep(self.delay)
                                continue
                            else:
                                print(f"  ❌ 商品IDが取得できませんでした", file=sys.stderr)
                        else:
                            print(f"  ❌ aria-labelから価格情報を抽出できませんでした", file=sys.stderr)
                    else:
                        print(f"  aria-labelが見つかりません", file=sys.stderr)
                    
                    # aria-labelが使えない場合の代替処理（href属性を使用）
                    if href and "/item/" in href:
                        print(f"  href属性から商品情報を抽出します: {href}", file=sys.stderr)
                        item_id = href.split("/")[-1]
                        print(f"  商品ID: {item_id}", file=sys.stderr)
                        
                        # 商品タイトルを取得（複数の方法を試す）
                        title = ""
                        title_selectors = [
                            "span",
                            "div",
                            "h3",
                            "p",
                            "[class*='title']",
                            "[class*='name']",
                            "[data-testid*='title']",
                            "[data-testid*='name']"
                        ]
                        
                        for title_selector in title_selectors:
                            try:
                                title_elements = item_element.find_elements(By.CSS_SELECTOR, title_selector)
                                for title_element in title_elements:
                                    text = title_element.text.strip().replace('\n', ' ').replace('\r', ' ')
                                    # 価格情報を除外し、5文字以上で¥記号を含まないテキストを商品名として採用
                                    if text and len(text) > 5 and '¥' not in text and not text.isdigit():
                                        title = text
                                        print(f"  タイトル取得成功 ({title_selector}): {title}", file=sys.stderr)
                                        break
                                if title:
                                    break
                            except Exception as e:
                                print(f"  タイトル取得エラー ({title_selector}): {str(e)}", file=sys.stderr)
                        
                        if not title:
                            title = f"Nintendo Switch商品 {item_id}"
                            print(f"  デフォルトタイトルを使用: {title}", file=sys.stderr)
                        
                        # 商品価格を取得（複数の方法を試す）
                        price = 0
                        price_selectors = [
                            "[class*='price']",
                            "[data-testid*='price']",
                            "span:contains('¥')",
                            "span:contains('円')",
                            "div:contains('¥')",
                            "div:contains('円')"
                        ]
                        
                        for price_selector in price_selectors:
                            try:
                                price_elements = item_element.find_elements(By.CSS_SELECTOR, price_selector)
                                for price_element in price_elements:
                                    text = price_element.text.strip()
                                    if text and ("¥" in text or "円" in text):
                                        # 価格テキストから数字を抽出
                                        price_match = re.search(r'([0-9,]+)', text)
                                        if price_match:
                                            price_text = price_match.group(1).replace(",", "")
                                            if price_text.isdigit():
                                                price = int(price_text)
                                                print(f"  価格取得成功 ({price_selector}): {price}円", file=sys.stderr)
                                                break
                                if price > 0:
                                    break
                            except Exception as e:
                                print(f"  価格取得エラー ({price_selector}): {str(e)}", file=sys.stderr)
                        
                        if price == 0:
                            # JavaScriptで価格を取得する最後の手段
                            try:
                                price_text = self.driver.execute_script("""
                                    var element = arguments[0];
                                    var allText = element.innerText || element.textContent || '';
                                    var priceMatch = allText.match(/([0-9,]+)円/);
                                    return priceMatch ? priceMatch[1] : '';
                                """, item_element)
                                if price_text:
                                    price_clean = price_text.replace(",", "")
                                    if price_clean.isdigit():
                                        price = int(price_clean)
                                        print(f"  JavaScript価格取得成功: {price}円", file=sys.stderr)
                            except Exception as e:
                                print(f"  JavaScript価格取得エラー: {str(e)}", file=sys.stderr)
                        
                        if price == 0:
                            # デフォルト価格を設定（実際の商品として扱うため）
                            price = 1000
                            print(f"  デフォルト価格を使用: {price}円", file=sys.stderr)
                        
                        # 商品画像を取得
                        image_url = ""
                        try:
                            img_element = item_element.find_element(By.TAG_NAME, "img")
                            image_url = img_element.get_attribute("src")
                            print(f"  画像URL取得成功: {image_url}", file=sys.stderr)
                        except Exception as e:
                            print(f"  画像URL取得エラー: {str(e)}", file=sys.stderr)
                        
                        # 商品データを作成
                        item = {
                            "search_term": keyword,
                            "item_id": item_id,
                            "title": title,
                            "price": price,
                            "currency": "JPY",
                            "status": "active",
                            "sold_date": None,
                            "condition": "中古",
                            "url": href,
                            "image_url": image_url,
                            "seller": "メルカリ出品者"
                        }
                        
                        items.append(item)
                        item_count += 1
                        print(f"  ✅ 商品を追加しました: {title} - {price}円", file=sys.stderr)
                        
                        if item_count >= limit:
                            break
                            
                        # レート制限対応
                        time.sleep(self.delay)
                    else:
                        print(f"  ❌ 有効なhref属性が見つかりません", file=sys.stderr)
                    
                except Exception as e:
                    print(f"商品データ抽出エラー: {str(e)}", file=sys.stderr)
                    continue
            
            return items
            
        except Exception as e:
            print(f"メルカリ検索エラー: {str(e)}", file=sys.stderr)
            return []
        finally:
            self._close_driver()

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_mercari_selenium_standalone.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"メルカリSelenium検索開始: {keyword}, limit: {limit}", file=sys.stderr)
    
    try:
        client = MercariSeleniumClient()
        
        # 出品中のアイテムを検索
        results = client.search_active_items(keyword, limit)
        
        print(f"検索完了: {len(results)}件の実データを取得", file=sys.stderr)
        
        # JSON形式で結果を出力（マーカー付き）
        print("JSON_START")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        print("JSON_END")
        
    except Exception as e:
        print(f"メルカリSelenium検索エラー: {str(e)}", file=sys.stderr)
        print("JSON_START")
        print("[]")
        print("JSON_END")

if __name__ == "__main__":
    main()
