"""
AI視覚スクレイピングの基底クラス
"""
import os
import sys
import time
import base64
from io import BytesIO
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BaseVisualScraper(ABC):
    """AI視覚スクレイピングの基底クラス"""
    
    def __init__(self, ai_analyzer=None, headless=True, save_screenshots=False):
        """
        Args:
            ai_analyzer: AI解析器インスタンス
            headless: ヘッドレスモードで実行するか
            save_screenshots: スクリーンショットを保存するか
        """
        self.ai_analyzer = ai_analyzer
        self.headless = headless
        self.save_screenshots = save_screenshots
        self.screenshot_dir = "./screenshots"
        self.driver = None
        
        if self.save_screenshots and not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
    
    def initialize_driver(self):
        """Seleniumドライバーを初期化"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # ユーザーエージェントを設定
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # スクリプトを注入して自動化を隠す
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"ドライバー初期化エラー: {e}", file=sys.stderr)
            return False
    
    def close_driver(self):
        """ドライバーを閉じる"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def navigate_to(self, url: str, wait_time: int = 3):
        """URLに移動"""
        if not self.driver:
            return False
        
        try:
            self.driver.get(url)
            time.sleep(wait_time)  # ページ読み込み待機
            return True
        except Exception as e:
            print(f"ナビゲーションエラー: {e}", file=sys.stderr)
            return False
    
    def take_screenshot(self, name: Optional[str] = None) -> Optional[str]:
        """スクリーンショットを撮影してBase64エンコード"""
        if not self.driver:
            return None
        
        try:
            # スクリーンショットを撮影
            screenshot_bytes = self.driver.get_screenshot_as_png()
            
            # PILイメージに変換
            image = Image.open(BytesIO(screenshot_bytes))
            
            # 保存する場合
            if self.save_screenshots and name:
                filename = f"{self.screenshot_dir}/{name}_{int(time.time())}.png"
                image.save(filename)
                print(f"スクリーンショット保存: {filename}", file=sys.stderr)
            
            # Base64エンコード
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return img_base64
            
        except Exception as e:
            print(f"スクリーンショット撮影エラー: {e}", file=sys.stderr)
            return None
    
    def click_element_at_position(self, x: int, y: int):
        """指定座標をクリック"""
        if not self.driver:
            return False
        
        try:
            actions = ActionChains(self.driver)
            # 絶対座標でクリック
            actions.move_to_element_with_offset(self.driver.find_element(By.TAG_NAME, 'body'), x, y)
            actions.click()
            actions.perform()
            return True
        except Exception as e:
            print(f"クリックエラー: {e}", file=sys.stderr)
            return False
    
    def scroll_page(self, pixels: int = 500):
        """ページをスクロール"""
        if not self.driver:
            return False
        
        try:
            self.driver.execute_script(f"window.scrollBy(0, {pixels});")
            time.sleep(1)  # スクロール後の読み込み待機
            return True
        except Exception as e:
            print(f"スクロールエラー: {e}", file=sys.stderr)
            return False
    
    def analyze_screenshot(self, screenshot_base64: str, prompt: str) -> Optional[Dict[str, Any]]:
        """AI解析器でスクリーンショットを解析"""
        if not self.ai_analyzer:
            print("AI解析器が設定されていません", file=sys.stderr)
            return None
        
        try:
            result = self.ai_analyzer.analyze_image(screenshot_base64, prompt)
            return result
        except Exception as e:
            print(f"AI解析エラー: {e}", file=sys.stderr)
            return None
    
    def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = 10):
        """要素が表示されるまで待機"""
        if not self.driver:
            return None
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except Exception as e:
            print(f"要素待機タイムアウト: {selector}", file=sys.stderr)
            return None
    
    def extract_dom_fallback(self) -> List[Dict[str, Any]]:
        """DOM解析によるフォールバック抽出"""
        # サブクラスで実装
        return []
    
    @abstractmethod
    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """検索を実行（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def extract_product_prompt(self) -> str:
        """商品抽出用のプロンプトを返す（サブクラスで実装）"""
        pass