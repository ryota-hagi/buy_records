"""
ラクマ検索用Seleniumスクレイパー
"""
import re
import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import urllib.parse


class RakumaSeleniumScraper:
    """ラクマ検索用Seleniumスクレイパー"""
    
    def __init__(self, selenium_url: str = "http://localhost:5001"):
        """
        初期化
        
        Args:
            selenium_url: Seleniumサーバーのベースアドレス
        """
        self.selenium_url = selenium_url
        self.base_url = "https://rakuma.rakuten.co.jp"
        
    def search(self, keyword: str) -> List[Dict]:
        """
        キーワードで商品を検索
        
        Args:
            keyword: 検索キーワード
            
        Returns:
            商品情報のリスト
        """
        # Seleniumドライバーの設定
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # ローカルChromeDriverを直接使用
        try:
            # リモートWebDriverを試す
            driver = webdriver.Remote(
                command_executor=f'{self.selenium_url}/wd/hub',
                options=options
            )
        except:
            # リモート接続失敗時はローカルChromeDriverを使用
            driver = webdriver.Chrome(options=options)
        
        try:
            # 検索URLを構築（ラクマの新しい検索形式）
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"{self.base_url}/search/{encoded_keyword}"
            
            print(f"ラクマ検索URL: {search_url}")
            
            # ページにアクセス
            driver.get(search_url)
            
            # ページ読み込み待機（最大10秒）
            wait = WebDriverWait(driver, 10)
            
            # JavaScriptの実行完了を待つ
            driver.execute_script("return document.readyState") == "complete"
            time.sleep(1)  # 追加の待機時間を短縮
            
            # 商品要素が表示されるまで待機
            try:
                # 複数のセレクタを試す
                item_selectors = [
                    'a[href*="/item/"]',
                    'div.item',
                    '[class*="item"]',
                    'article'
                ]
                
                item_found = False
                for selector in item_selectors:
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        item_found = True
                        break
                    except TimeoutException:
                        continue
                
                if not item_found:
                    print("ラクマ: 商品要素が見つかりませんでした")
                    return []
                    
            except TimeoutException:
                print("ラクマ: ページの読み込みがタイムアウトしました")
                return []
            
            # スクロールはスキップして時間を節約
            # self._scroll_page(driver)
            
            # 商品情報を抽出
            items = self._extract_items(driver)
            
            print(f"ラクマ: {len(items)}件の商品を取得")
            return items
            
        except Exception as e:
            print(f"ラクマ検索エラー: {str(e)}")
            return []
        finally:
            driver.quit()
    
    def _extract_items(self, driver) -> List[Dict]:
        """
        商品情報を抽出
        
        Args:
            driver: WebDriverインスタンス
            
        Returns:
            商品情報のリスト
        """
        items = []
        
        # 商品要素を探す（ラクマの現在の構造に合わせて更新）
        selectors = [
            'a[href*="rakuma.rakuten.co.jp/item/"]',  # 新しいラクマURL形式
            'a[href*="/item/"]',                       # 商品リンク（相対パス）
            '[data-testid*="item"]',                   # data-testid属性付き要素
            'div[class*="item"] a',                    # 商品コンテナ内のリンク
            'article a',                               # article要素内のリンク
            '//a[contains(@href, "item")]'             # XPath形式
        ]
        
        item_elements = []
        for selector in selectors:
            try:
                # XPathセレクタの場合
                if selector.startswith('//'):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                # 商品リンクを含む要素のみフィルタリング
                valid_elements = []
                for elem in elements:
                    try:
                        # 要素内に商品リンクがあるか確認
                        if elem.tag_name == 'a':
                            href = elem.get_attribute('href')
                            if href and ('rakuma.rakuten.co.jp/item/' in href or '/item/' in href):
                                valid_elements.append(elem)
                        else:
                            # 要素内のリンクを探す
                            links = elem.find_elements(By.CSS_SELECTOR, 'a[href*="item"]')
                            if links:
                                valid_elements.append(elem)
                    except:
                        continue
                
                if valid_elements:
                    item_elements = valid_elements
                    print(f"ラクマ: {selector}で{len(item_elements)}件の商品を発見")
                    break
            except Exception as e:
                continue
        
        if not item_elements:
            print("ラクマ: 商品要素が見つかりませんでした")
            return []
        
        # 重複を避けるためURLをセットで管理
        seen_urls = set()
        unique_elements = []
        
        for elem in item_elements:
            try:
                if elem.tag_name == 'a':
                    url = elem.get_attribute('href')
                else:
                    # 要素内から商品リンクを探す
                    link = elem.find_element(By.CSS_SELECTOR, 'a[href*="item"]')
                    url = link.get_attribute('href')
                
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_elements.append(elem)
            except:
                continue
        
        # 各商品の情報を抽出
        for element in unique_elements[:10]:  # 最大10件に制限して高速化
            try:
                item_info = self._extract_item_info(element, driver)
                if item_info and item_info.get('title') and item_info.get('price', 0) > 0:
                    items.append(item_info)
            except Exception as e:
                continue
        
        return items
    
    def _extract_item_info(self, element, driver) -> Optional[Dict]:
        """
        個別の商品情報を抽出
        
        Args:
            element: 商品要素
            driver: WebDriverインスタンス
            
        Returns:
            商品情報の辞書
        """
        try:
            # リンク要素を取得
            if element.tag_name == 'a':
                link_element = element
            else:
                # コンテナ要素の場合、親要素を最大5階層まで遡る
                try:
                    container = element
                    for _ in range(5):
                        parent = container.find_element(By.XPATH, '..')
                        # 商品コンテナの特徴を持つ要素を探す
                        parent_class = parent.get_attribute('class') or ''
                        if any(cls in parent_class.lower() for cls in ['item', 'product', 'card']):
                            container = parent
                        else:
                            break
                    element = container
                except:
                    pass
                # コンテナ要素の場合、リンクを探す
                link_element = element.find_element(By.CSS_SELECTOR, 'a[href*="item"]')
            
            # URL取得
            url = link_element.get_attribute('href')
            if not url:
                return None
            
            # 完全なURLに変換
            if not url.startswith('http'):
                url = self.base_url + url
            
            # 商品ID抽出（新旧両方のURLパターンに対応）
            # 新形式: https://item.fril.jp/xxxxx
            # 旧形式: /item/xxxxx
            item_id = ''
            if 'item.fril.jp/' in url:
                item_id_match = re.search(r'item\.fril\.jp/([^/\?]+)', url)
                item_id = item_id_match.group(1) if item_id_match else ''
            else:
                item_id_match = re.search(r'/item/([^/\?]+)', url)
                item_id = item_id_match.group(1) if item_id_match else ''
            
            # テキスト全体を取得
            item_text = element.text.strip()
            
            # タイトル取得
            title = ''
            # 画像のalt属性を試す
            try:
                img = element.find_element(By.TAG_NAME, 'img')
                title = img.get_attribute('alt') or ''
            except:
                pass
            
            # タイトルが取得できない場合はテキストから抽出
            if not title:
                lines = item_text.split('\n')
                for line in lines:
                    # 価格やSOLDではない最初の行をタイトルとする
                    if (line and 
                        not re.match(r'^[¥￥\d,]+$', line) and 
                        not re.match(r'^\d+円$', line) and
                        'SOLD' not in line.upper() and
                        len(line) > 5):
                        title = line
                        break
            
            # 価格抽出（親要素のテキストも確認）
            price = 0
            price_patterns = [
                r'¥\s*([\d,]+)',
                r'￥\s*([\d,]+)',
                r'([\d,]+)\s*円',
                r'¥([\d,]+)',
                r'￥([\d,]+)'
            ]
            
            # まず現在の要素のテキストから価格を探す
            for pattern in price_patterns:
                price_matches = re.findall(pattern, item_text)
                if price_matches:
                    # 最初の有効な価格を使用
                    for match in price_matches:
                        price_str = match.replace(',', '')
                        if price_str.isdigit():
                            price = int(price_str)
                            break
                    if price > 0:
                        break
            
            # 価格が見つからない場合、親要素を確認
            if price == 0:
                try:
                    # 親要素を最大3階層まで遡って価格を探す
                    parent = element
                    for _ in range(3):
                        parent = parent.find_element(By.XPATH, '..')
                        parent_text = parent.text.strip()
                        
                        # 現在の商品の価格のみを抽出（最初に見つかったもの）
                        for pattern in price_patterns:
                            price_match = re.search(pattern, parent_text)
                            if price_match:
                                price_str = price_match.group(1).replace(',', '')
                                if price_str.isdigit():
                                    price = int(price_str)
                                    break
                        
                        if price > 0:
                            break
                except:
                    pass
            
            # 画像URL取得
            image_url = ''
            try:
                img = element.find_element(By.TAG_NAME, 'img')
                image_url = img.get_attribute('src') or img.get_attribute('data-src') or ''
            except:
                pass
            
            # 状態（売り切れチェック）
            status = 'available'
            if 'SOLD' in item_text.upper() or '売り切れ' in item_text:
                status = 'sold'
            
            return {
                'title': title,
                'price': price,
                'url': url,
                'image_url': image_url,
                'item_id': item_id,
                'status': status,
                'platform': 'rakuma',
                'currency': 'JPY'
            }
            
        except Exception as e:
            return None
    
    def _scroll_page(self, driver):
        """
        ページをスクロールして追加の商品を読み込む
        
        Args:
            driver: WebDriverインスタンス
        """
        try:
            # ページの高さを取得
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            # 2回スクロール
            for _ in range(2):
                # ページの最下部までスクロール
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 新しい要素が読み込まれるのを待つ
                time.sleep(2)
                
                # 新しい高さを取得
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                # 高さが変わらなければ終了
                if new_height == last_height:
                    break
                    
                last_height = new_height
                
        except Exception as e:
            print(f"スクロールエラー: {str(e)}")