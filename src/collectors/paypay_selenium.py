"""
PayPayフリマ検索用Seleniumスクレイパー
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


class PayPaySeleniumScraper:
    """PayPayフリマ検索用Seleniumスクレイパー"""
    
    def __init__(self, selenium_url: str = "http://localhost:5001"):
        """
        初期化
        
        Args:
            selenium_url: Seleniumサーバーのベースアドレス
        """
        self.selenium_url = selenium_url
        self.base_url = "https://paypayfleamarket.yahoo.co.jp"
        
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
        
        # リモートWebDriverに接続
        driver = webdriver.Remote(
            command_executor=f'{self.selenium_url}/wd/hub',
            options=options
        )
        
        try:
            # 検索URLを構築
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"{self.base_url}/search/{encoded_keyword}"
            
            print(f"PayPayフリマ検索URL: {search_url}")
            
            # ページにアクセス
            driver.get(search_url)
            
            # ページ読み込み待機（最大30秒）
            wait = WebDriverWait(driver, 30)
            
            # JavaScriptの実行完了を待つ
            driver.execute_script("return document.readyState") == "complete"
            time.sleep(3)  # 追加の待機時間
            
            # 商品要素が表示されるまで待機
            try:
                # 複数のセレクタを試す
                item_selectors = [
                    'a[href*="/item/"]',
                    '[data-testid="search-result-item"]',
                    'div[class*="ItemCard"]',
                    'article[class*="item"]'
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
                    print("PayPayフリマ: 商品要素が見つかりませんでした")
                    return []
                    
            except TimeoutException:
                print("PayPayフリマ: ページの読み込みがタイムアウトしました")
                return []
            
            # スクロールして追加の商品を読み込む
            self._scroll_page(driver)
            
            # 商品情報を抽出
            items = self._extract_items(driver)
            
            print(f"PayPayフリマ: {len(items)}件の商品を取得")
            return items
            
        except Exception as e:
            print(f"PayPayフリマ検索エラー: {str(e)}")
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
        
        # 商品要素を探す
        selectors = [
            'a[href*="/item/"]',
            'div[data-testid="search-result-item"]',
            'div[class*="ItemCard"]'
        ]
        
        item_elements = []
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    item_elements = elements
                    print(f"PayPayフリマ: {selector}で{len(elements)}件の商品を発見")
                    break
            except:
                continue
        
        if not item_elements:
            print("PayPayフリマ: 商品要素が見つかりませんでした")
            return []
        
        # 重複を避けるためにコンテナIDをセットで管理
        seen_containers = set()
        
        # 各商品の情報を抽出
        for element in item_elements[:30]:  # 最大30件
            try:
                # コンテナの一意性を確認
                container_id = None
                try:
                    # data-testidやidを確認
                    container_id = element.get_attribute('data-testid') or element.get_attribute('id')
                    if not container_id:
                        # 商品URLから一意のIDを生成
                        link_elem = element if element.tag_name == 'a' else element.find_element(By.CSS_SELECTOR, 'a[href*="/item/"]')
                        url = link_elem.get_attribute('href')
                        if url:
                            container_id = url.split('/item/')[-1].split('?')[0]
                except:
                    pass
                
                # 重複チェック
                if container_id and container_id in seen_containers:
                    continue
                if container_id:
                    seen_containers.add(container_id)
                
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
                link_element = element.find_element(By.CSS_SELECTOR, 'a[href*="/item/"]')
            
            # URL取得
            url = link_element.get_attribute('href')
            if not url:
                return None
            
            # 商品ID抽出
            item_id_match = re.search(r'/item/([a-zA-Z0-9]+)', url)
            item_id = item_id_match.group(1) if item_id_match else ''
            
            # タイトル取得（リンク要素内から取得）
            title = ''
            try:
                # リンク要素のテキストを優先
                link_text = link_element.text.strip()
                if link_text and not re.match(r'^[¥￥\d,]+$', link_text):
                    title = link_text
                else:
                    # 画像のalt属性を試す
                    img = element.find_element(By.TAG_NAME, 'img')
                    title = img.get_attribute('alt') or ''
            except:
                pass
            
            # タイトルが取得できない場合は要素全体のテキストから抽出
            if not title:
                item_text = element.text.strip()
                lines = item_text.split('\n')
                for line in lines:
                    if (line and 
                        not re.match(r'^[¥￥\d,]+$', line) and 
                        not re.match(r'^\d+円$', line) and
                        'SOLD' not in line.upper() and
                        len(line) > 5):
                        title = line
                        break
            
            # 価格抽出
            price = 0
            price_patterns = [
                r'¥\s*([\d,]+)',
                r'￥\s*([\d,]+)',
                r'([\d,]+)\s*円',
                r'¥([\d,]+)',
                r'￥([\d,]+)'
            ]
            
            item_text = element.text.strip()
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
            
            # 画像URL取得
            image_url = ''
            try:
                img = element.find_element(By.TAG_NAME, 'img')
                image_url = img.get_attribute('src') or img.get_attribute('data-src') or ''
            except:
                pass
            
            # 送料情報の抽出
            shipping_fee = None
            if '送料込み' in item_text or '送料無料' in item_text:
                shipping_fee = 0
            
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
                'platform': 'paypay',
                'shipping_fee': shipping_fee,
                'total_price': price + (shipping_fee if shipping_fee else 0),
                'currency': 'JPY',
                'condition': '中古',
                'store_name': 'PayPayフリマ出品者',
                'location': 'Japan'
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
            
            # 3回スクロール
            for _ in range(3):
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