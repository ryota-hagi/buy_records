"""
メルカリ検索用Seleniumスクレイパー
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


class MercariSeleniumScraper:
    """メルカリ検索用Seleniumスクレイパー"""
    
    def __init__(self, selenium_url: str = "http://localhost:5001"):
        """
        初期化
        
        Args:
            selenium_url: Seleniumサーバーのベースアドレス
        """
        self.selenium_url = selenium_url
        self.base_url = "https://jp.mercari.com"
        
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
            search_url = f"{self.base_url}/search?keyword={encoded_keyword}"
            
            print(f"メルカリ検索URL: {search_url}")
            
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
                    'li[data-testid="item-cell"]',
                    'div[data-testid="item-cell"]',
                    'article[aria-label*="商品"]',
                    'a[href*="/item/m"]'
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
                    print("メルカリ: 商品要素が見つかりませんでした")
                    return []
                    
            except TimeoutException:
                print("メルカリ: ページの読み込みがタイムアウトしました")
                return []
            
            # スクロールして追加の商品を読み込む
            self._scroll_page(driver)
            
            # 商品情報を抽出
            items = self._extract_items(driver)
            
            print(f"メルカリ: {len(items)}件の商品を取得")
            return items
            
        except Exception as e:
            print(f"メルカリ検索エラー: {str(e)}")
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
            'li[data-testid="item-cell"]',
            'div[data-testid="item-cell"]',
            'article[aria-label]',
            'a[href*="/item/m"]'
        ]
        
        item_elements = []
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    item_elements = elements
                    print(f"メルカリ: {selector}で{len(elements)}件の商品を発見")
                    break
            except:
                continue
        
        if not item_elements:
            print("メルカリ: 商品要素が見つかりませんでした")
            return []
        
        # 各商品の情報を抽出
        for element in item_elements[:30]:  # 最大30件
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
            # aria-labelから情報を抽出（最も信頼性が高い）
            aria_label = element.get_attribute('aria-label')
            if aria_label:
                # aria-labelから商品タイトルと価格を抽出
                # 例: "商品名の画像 1,000円"
                # 例: "商品名の画像 売り切れ 1,000円"
                match = re.search(r'(.+)の画像\s+(?:売り切れ\s+)?([0-9,]+)円', aria_label)
                if match:
                    title = match.group(1).strip()
                    price_str = match.group(2).replace(',', '')
                    price = int(price_str)
                else:
                    # パターンが一致しない場合は別の方法を試す
                    title = aria_label.replace('の画像', '').strip()
                    price = 0
            else:
                title = ''
                price = 0
            
            # リンク要素を探す
            link_element = None
            if element.tag_name == 'a':
                link_element = element
            else:
                try:
                    link_element = element.find_element(By.CSS_SELECTOR, 'a[href*="/item/"]')
                except:
                    pass
            
            # URL取得
            url = ''
            item_id = ''
            if link_element:
                url = link_element.get_attribute('href')
                if url:
                    # 商品ID抽出
                    item_id_match = re.search(r'/item/m(\d+)', url)
                    item_id = item_id_match.group(1) if item_id_match else ''
            
            # タイトルが取得できていない場合、他の方法を試す
            if not title:
                # テキスト全体から抽出
                item_text = element.text.strip()
                lines = item_text.split('\n')
                for line in lines:
                    if line and not re.match(r'^[¥￥\d,]+$', line) and len(line) > 5:
                        title = line
                        break
            
            # 価格が取得できていない場合
            if price == 0:
                item_text = element.text.strip()
                price_patterns = [
                    r'¥\s*([\d,]+)',
                    r'￥\s*([\d,]+)',
                    r'([\d,]+)\s*円'
                ]
                
                for pattern in price_patterns:
                    price_match = re.search(pattern, item_text)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '')
                        price = int(price_str)
                        break
            
            # 画像URL取得
            image_url = ''
            try:
                img = element.find_element(By.TAG_NAME, 'img')
                image_url = img.get_attribute('src') or img.get_attribute('data-src') or ''
            except:
                pass
            
            # 状態（売り切れチェック）
            status = 'available'
            element_text = element.text.upper()
            if 'SOLD' in element_text or '売り切れ' in element_text or 'SOLDOUT' in element_text:
                status = 'sold'
            
            # 送料情報
            shipping_included = '送料込み' in element.text
            
            return {
                'title': title,
                'price': price,
                'url': url,
                'image_url': image_url,
                'item_id': item_id,
                'status': status,
                'platform': 'mercari',
                'shipping_included': shipping_included,
                'total_price': price,  # メルカリは基本的に送料込み
                'currency': 'JPY',
                'condition': '中古',  # メルカリは基本的に中古品
                'store_name': 'メルカリ出品者',
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