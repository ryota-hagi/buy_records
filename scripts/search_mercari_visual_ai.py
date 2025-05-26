#!/usr/bin/env python3
"""
AI視覚認識を使用したMercariスクレイピング
スクリーンショットを撮影し、AIで解析してデータを抽出
"""
import json
import sys
import base64
import time
from io import BytesIO
from PIL import Image
import openai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import os

class VisualAIScraper:
    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Seleniumの設定
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = None
    
    def initialize_driver(self):
        """ドライバーを初期化"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            return True
        except Exception as e:
            print(f"ドライバー初期化エラー: {e}", file=sys.stderr)
            return False
    
    def take_screenshot(self):
        """現在のページのスクリーンショットを撮影"""
        if not self.driver:
            return None
        
        # スクリーンショットをバイト配列として取得
        screenshot_bytes = self.driver.get_screenshot_as_png()
        
        # PILイメージに変換
        image = Image.open(BytesIO(screenshot_bytes))
        
        # Base64エンコード
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return img_base64
    
    def analyze_screenshot_with_ai(self, img_base64, prompt):
        """GPT-4 VisionでスクリーンショットをAI解析"""
        if not self.openai_api_key:
            print("OpenAI APIキーが設定されていません", file=sys.stderr)
            return None
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"AI解析エラー: {e}", file=sys.stderr)
            return None
    
    def extract_product_data(self, img_base64):
        """商品データを抽出するプロンプト"""
        prompt = """
        このスクリーンショットから商品情報を抽出してください。
        以下の形式のJSONで返してください：
        {
            "products": [
                {
                    "title": "商品名",
                    "price": "価格（数値のみ）",
                    "image_position": {"x": x座標, "y": y座標},
                    "clickable_area": {"x": x座標, "y": y座標, "width": 幅, "height": 高さ}
                }
            ],
            "next_page_button": {"x": x座標, "y": y座標} または null
        }
        
        注意点：
        - 価格は円記号や「,」を除いた数値のみ
        - 座標は画面上の実際のピクセル位置
        - 商品画像またはタイトルのクリック可能な領域を特定
        """
        
        return self.analyze_screenshot_with_ai(img_base64, prompt)
    
    def click_element_at_position(self, x, y):
        """指定座標をクリック"""
        if not self.driver:
            return
        
        actions = ActionChains(self.driver)
        actions.move_by_offset(x, y).click().perform()
        # クリック後は位置をリセット
        actions.move_by_offset(-x, -y).perform()
    
    def search_mercari_visual(self, query, limit=20):
        """Mercariを視覚的にスクレイピング"""
        results = []
        
        if not self.initialize_driver():
            return results
        
        try:
            # Mercariの検索ページにアクセス
            search_url = f"https://jp.mercari.com/search?keyword={query}&status=on_sale&sort=price&order=asc"
            print(f"アクセス中: {search_url}", file=sys.stderr)
            
            self.driver.get(search_url)
            time.sleep(3)  # ページ読み込み待機
            
            # スクリーンショット撮影
            img_base64 = self.take_screenshot()
            if not img_base64:
                print("スクリーンショット撮影失敗", file=sys.stderr)
                return results
            
            # デバッグ用：スクリーンショットを保存
            with open("mercari_screenshot.png", "wb") as f:
                f.write(base64.b64decode(img_base64))
            print("スクリーンショット保存: mercari_screenshot.png", file=sys.stderr)
            
            # AIで商品データ抽出
            if self.openai_api_key:
                ai_result = self.extract_product_data(img_base64)
                if ai_result:
                    try:
                        data = json.loads(ai_result)
                        products = data.get('products', [])
                        
                        for i, product in enumerate(products[:limit]):
                            result = {
                                'id': f'visual_{i}',
                                'title': product.get('title', ''),
                                'price': int(product.get('price', 0)),
                                'url': self.driver.current_url,
                                'image_url': '',
                                'platform': 'mercari',
                                'method': 'visual_ai'
                            }
                            results.append(result)
                            
                    except json.JSONDecodeError:
                        print("AI結果のJSON解析エラー", file=sys.stderr)
            
            # AI解析が使えない場合の代替方法（OCR + パターン認識）
            if not results:
                print("代替方法: 基本的なDOM解析を実行", file=sys.stderr)
                
                # 商品要素を探す
                item_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/item/"]')
                
                for i, elem in enumerate(item_elements[:limit]):
                    try:
                        href = elem.get_attribute('href')
                        if '/item/m' in href:
                            item_id = href.split('/item/')[-1].split('?')[0]
                            
                            # 要素の位置を取得（視覚的確認用）
                            location = elem.location
                            size = elem.size
                            
                            result = {
                                'id': item_id,
                                'title': f'商品 {item_id}',
                                'price': 0,
                                'url': href,
                                'image_url': '',
                                'platform': 'mercari',
                                'method': 'visual_fallback',
                                'visual_info': {
                                    'x': location['x'],
                                    'y': location['y'],
                                    'width': size['width'],
                                    'height': size['height']
                                }
                            }
                            results.append(result)
                            
                    except Exception as e:
                        continue
                
        except Exception as e:
            print(f"視覚スクレイピングエラー: {e}", file=sys.stderr)
            
        finally:
            if self.driver:
                self.driver.quit()
        
        return results

def main():
    if len(sys.argv) < 2:
        print("Usage: search_mercari_visual_ai.py <query>", file=sys.stderr)
        sys.exit(1)
    
    query = sys.argv[1]
    
    print("JSON_START", file=sys.stderr)
    
    try:
        scraper = VisualAIScraper()
        results = scraper.search_mercari_visual(query)
        
        output = {
            'success': len(results) > 0,
            'results': results,
            'platform': 'mercari',
            'query': query,
            'method': 'visual_ai_scraping'
        }
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        error_output = {
            'success': False,
            'results': [],
            'error': str(e),
            'platform': 'mercari'
        }
        print(json.dumps(error_output, ensure_ascii=False, indent=2))
    
    print("JSON_END", file=sys.stderr)

if __name__ == "__main__":
    main()