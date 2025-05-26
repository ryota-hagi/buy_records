"""
Mercari専用のAI視覚スクレイピング実装
"""
import json
import sys
import time
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from selenium.webdriver.common.by import By
from .base_scraper import BaseVisualScraper

class MercariVisualScraper(BaseVisualScraper):
    """Mercari専用の視覚スクレイパー"""
    
    def __init__(self, ai_analyzer=None, headless=True, save_screenshots=True):
        super().__init__(ai_analyzer, headless, save_screenshots)
        self.base_url = "https://jp.mercari.com"
    
    def extract_product_prompt(self) -> str:
        """Mercari用の商品抽出プロンプト"""
        return """
        メルカリの検索結果ページから商品情報を正確に抽出してください。
        各商品カードには商品画像、タイトル、価格（¥マーク付き）が表示されています。
        
        実際の商品データを読み取って、以下のJSON形式で返してください：
        {
            "products": [
                {
                    "title": "実際の商品タイトル（画像下のテキスト）",
                    "price": 価格の数値のみ（¥やカンマを除去）,
                    "sold": false,
                    "x": 100,
                    "y": 200
                }
            ],
            "has_next": true
        }
        
        重要：
        - 各商品の実際のタイトルテキストを読み取る（例：「ファイヤースティック ウィザードリング2枚セット」）
        - 価格は¥マークの後の数値（例：¥300 → 300）
        - 「SOLD」表示がある商品は sold: true
        - 最低でも10件以上の商品を抽出
        - ダミーデータではなく、スクリーンショットから実際のデータを読み取る
        """
    
    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Mercariで商品を検索"""
        results = []
        
        if not self.initialize_driver():
            print("ドライバーの初期化に失敗しました", file=sys.stderr)
            return results
        
        try:
            # 検索URLを構築
            search_url = f"{self.base_url}/search?keyword={quote(query)}&status=on_sale&sort=price&order=asc"
            print(f"検索URL: {search_url}", file=sys.stderr)
            
            # ページに移動
            if not self.navigate_to(search_url, wait_time=5):
                print("ページへの移動に失敗しました", file=sys.stderr)
                return results
            
            # ページが完全に読み込まれるまで待機
            self.wait_for_element('mer-item-thumbnail', By.TAG_NAME, timeout=10)
            
            # 商品を収集
            page_count = 0
            max_pages = 3  # 最大3ページまで
            
            while len(results) < limit and page_count < max_pages:
                page_count += 1
                print(f"ページ {page_count} を処理中...", file=sys.stderr)
                
                # スクリーンショットを撮影
                screenshot = self.take_screenshot(f"mercari_page_{page_count}")
                if not screenshot:
                    print("スクリーンショットの撮影に失敗しました", file=sys.stderr)
                    break
                
                # AI解析を実行
                if self.ai_analyzer:
                    print("AI解析を開始します...", file=sys.stderr)
                    ai_result = self.analyze_screenshot(screenshot, self.extract_product_prompt())
                    print(f"AI解析結果: {ai_result}", file=sys.stderr)
                    
                    if ai_result:
                        try:
                            # AI結果をパース
                            products = ai_result.get('products', [])
                            
                            for i, product in enumerate(products):
                                if len(results) >= limit:
                                    break
                                
                                # 売り切れ商品はスキップ
                                if product.get('sold', False):
                                    continue
                                
                                # 商品をクリックして詳細ページのURLを取得（オプション）
                                position = product.get('position', {})
                                if position and position.get('x') and position.get('y'):
                                    # 商品の中心をクリック
                                    center_x = position['x'] + position.get('width', 100) // 2
                                    center_y = position['y'] + position.get('height', 100) // 2
                                    
                                    # 新しいタブで開く
                                    self.driver.execute_script(f"window.open('', '_blank');")
                                    self.driver.switch_to.window(self.driver.window_handles[-1])
                                    
                                    # 商品をクリックする代わりに、URLを推測
                                    # （実際のクリックは複雑なので、基本情報のみ取得）
                                
                                result = {
                                    'id': f'visual_{page_count}_{i}',
                                    'title': product.get('title', ''),
                                    'price': int(product.get('price', 0)),
                                    'url': search_url,  # 詳細URLは後で更新可能
                                    'image_url': '',  # 画像URLは別途取得
                                    'platform': 'mercari',
                                    'method': 'visual_ai',
                                    'page': page_count,
                                    'position': position
                                }
                                results.append(result)
                            
                            # 次のページがあるかチェック
                            pagination = ai_result.get('pagination', {})
                            if not pagination.get('has_next', False):
                                print("次のページがありません", file=sys.stderr)
                                break
                            
                            # 次のページボタンをクリック
                            next_button = pagination.get('next_button_position')
                            if next_button and next_button.get('x') and next_button.get('y'):
                                print("次のページに移動します...", file=sys.stderr)
                                self.click_element_at_position(next_button['x'], next_button['y'])
                                time.sleep(3)  # ページ読み込み待機
                            else:
                                # スクロールして更に商品を読み込む
                                self.scroll_page(800)
                                time.sleep(2)
                                
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"AI結果の解析エラー: {e}", file=sys.stderr)
                            # フォールバックとしてDOM解析を使用
                            fallback_results = self.extract_dom_fallback()
                            results.extend(fallback_results[:limit - len(results)])
                            break
                
                else:
                    # AI解析器がない場合はDOM解析を使用
                    print("AI解析器が設定されていないため、DOM解析を使用します", file=sys.stderr)
                    fallback_results = self.extract_dom_fallback()
                    results.extend(fallback_results[:limit - len(results)])
                    break
            
            print(f"合計 {len(results)} 件の商品を取得しました", file=sys.stderr)
            
        except Exception as e:
            print(f"検索中にエラーが発生しました: {e}", file=sys.stderr)
            
        finally:
            self.close_driver()
        
        return results
    
    def extract_dom_fallback(self) -> List[Dict[str, Any]]:
        """DOM解析によるフォールバック抽出"""
        if not self.driver:
            return []
        
        results = []
        
        try:
            # 商品要素を探す
            selectors = [
                'mer-item-thumbnail',
                'a[href*="/item/m"]',
                '[data-testid="item-cell"]',
                '.merItemThumbnail'
            ]
            
            for selector in selectors:
                try:
                    if selector.startswith('.') or selector.startswith('['):
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    else:
                        elements = self.driver.find_elements(By.TAG_NAME, selector)
                    
                    if elements:
                        print(f"セレクタ '{selector}' で {len(elements)} 個の要素を発見", file=sys.stderr)
                        
                        for i, elem in enumerate(elements[:20]):
                            try:
                                # 要素の情報を取得
                                if selector == 'mer-item-thumbnail':
                                    # mer-item-thumbnailの場合
                                    aria_label = elem.get_attribute('aria-label') or ''
                                    item_id = elem.get_attribute('id') or f'item_{i}'
                                    
                                    # aria-labelから情報を抽出
                                    import re
                                    title_match = re.search(r'^(.*?)の画像', aria_label)
                                    price_match = re.search(r'(\d+(?:,\d+)*)円', aria_label)
                                    
                                    title = title_match.group(1) if title_match else f'商品 {i+1}'
                                    price_text = price_match.group(1) if price_match else '0'
                                    price = int(price_text.replace(',', ''))
                                    
                                    # 商品URL
                                    item_url = f"{self.base_url}/item/{item_id}"
                                    
                                else:
                                    # その他のセレクタ
                                    href = elem.get_attribute('href') or ''
                                    if '/item/m' in href:
                                        item_id = href.split('/item/')[-1].split('?')[0]
                                        item_url = f"{self.base_url}/item/{item_id}"
                                    else:
                                        continue
                                    
                                    title = f'商品 {item_id}'
                                    price = 0
                                
                                result = {
                                    'id': item_id,
                                    'title': title,
                                    'price': price,
                                    'url': item_url,
                                    'image_url': '',
                                    'platform': 'mercari',
                                    'method': 'dom_fallback'
                                }
                                results.append(result)
                                
                            except Exception as e:
                                continue
                        
                        break  # 成功したら終了
                        
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"DOM解析エラー: {e}", file=sys.stderr)
        
        return results