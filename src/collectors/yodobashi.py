"""
ヨドバシカメラ商品検索
"""
import requests
from bs4 import BeautifulSoup
import urllib.parse
from typing import List, Dict, Optional
import time
import re


class YodobashiScraper:
    """ヨドバシカメラの商品検索スクレイパー"""
    
    def __init__(self):
        self.base_url = "https://www.yodobashi.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.timeout = 60  # タイムアウトを60秒に延長
        
    def search(self, keyword: str) -> List[Dict]:
        """
        キーワードで商品を検索
        
        Args:
            keyword: 検索キーワード
            
        Returns:
            商品情報のリスト
        """
        try:
            # URLエンコード
            encoded_keyword = urllib.parse.quote(keyword, safe='')
            
            # 新しいURL形式を使用
            search_url = f"{self.base_url}/?word={encoded_keyword}"
            
            print(f"ヨドバシ検索URL: {search_url}")
            
            # リクエスト送信（タイムアウト設定を延長）
            response = requests.get(
                search_url, 
                headers=self.headers, 
                timeout=self.timeout,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                print(f"ヨドバシHTTPエラー: {response.status_code}")
                return []
            
            # HTMLパース
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 商品リストを取得（複数のセレクタを試す）
            items = []
            
            # セレクタ1: 通常の商品リスト
            product_items = soup.find_all('div', class_='srcResultItem')
            
            # セレクタ2: 別の形式
            if not product_items:
                product_items = soup.find_all('div', class_='productListTile')
            
            # セレクタ3: さらに別の形式
            if not product_items:
                product_items = soup.find_all('li', class_='js_productList')
            
            print(f"ヨドバシ: {len(product_items)}件の商品要素を発見")
            
            for item in product_items[:20]:  # 最大20件
                try:
                    product_info = self._extract_product_info(item)
                    if product_info:
                        items.append(product_info)
                except Exception as e:
                    continue
            
            return items
            
        except requests.Timeout:
            print(f"ヨドバシ検索タイムアウト: {self.timeout}秒を超えました")
            return []
        except Exception as e:
            print(f"ヨドバシ検索エラー: {str(e)}")
            return []
    
    def _extract_product_info(self, item) -> Optional[Dict]:
        """
        商品情報を抽出
        
        Args:
            item: BeautifulSoupの商品要素
            
        Returns:
            商品情報の辞書
        """
        try:
            # タイトル取得（複数のセレクタを試す）
            title_elem = (
                item.find('p', class_='pName') or
                item.find('a', class_='js_productListPostTag') or
                item.find('h3') or
                item.find('a', href=True)
            )
            
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if not title:
                return None
            
            # URL取得
            link_elem = item.find('a', href=True)
            if not link_elem:
                return None
                
            url = link_elem['href']
            if not url.startswith('http'):
                url = self.base_url + url
            
            # 価格取得（複数のセレクタを試す）
            price = 0
            price_elem = (
                item.find('span', class_='productPrice') or
                item.find('p', class_='price') or
                item.find(class_=re.compile('price', re.I))
            )
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # 価格から数値を抽出
                price_match = re.search(r'[\d,]+', price_text.replace('￥', '').replace('¥', ''))
                if price_match:
                    price = int(price_match.group().replace(',', ''))
            
            # 画像URL取得
            image_url = ''
            img_elem = item.find('img')
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                if image_url and not image_url.startswith('http'):
                    image_url = self.base_url + image_url
            
            # ポイント情報
            point_info = ''
            point_elem = item.find(class_=re.compile('point', re.I))
            if point_elem:
                point_info = point_elem.get_text(strip=True)
            
            # 在庫状況
            stock_status = '在庫あり'
            stock_elem = item.find(class_=re.compile('stock|availability', re.I))
            if stock_elem:
                stock_text = stock_elem.get_text(strip=True)
                if '在庫なし' in stock_text or '品切れ' in stock_text:
                    stock_status = '在庫なし'
            
            return {
                'platform': 'yodobashi',
                'title': title,
                'price': price,
                'url': url,
                'image_url': image_url,
                'shipping_fee': 0,  # ヨドバシは基本送料無料
                'total_price': price,
                'condition': '新品',
                'store_name': 'ヨドバシカメラ',
                'location': 'Japan',
                'currency': 'JPY',
                'point_info': point_info,
                'stock_status': stock_status
            }
            
        except Exception as e:
            return None