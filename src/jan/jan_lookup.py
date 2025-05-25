"""JANコードルックアップAPIクライアント"""

import requests
import urllib.parse
from typing import Optional, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


class JANLookupClient:
    """JANコードルックアップAPIクライアント"""
    
    def __init__(self, app_id: str):
        """
        初期化
        
        Args:
            app_id: JANコードルックアップAPIのアプリID
        """
        self.app_id = app_id
        self.base_url = "https://api.jancodelookup.com/"
        self.session = requests.Session()
        
    def lookup_product(self, jan_code: str) -> Optional[Dict[str, Any]]:
        """
        JANコードから商品情報を取得
        
        Args:
            jan_code: 13桁のJANコード
            
        Returns:
            商品情報の辞書、見つからない場合はNone
        """
        # JANコードのバリデーション
        if not self._validate_jan_code(jan_code):
            logger.error(f"Invalid JAN code: {jan_code}")
            return None
            
        try:
            # APIリクエストパラメータ
            params = {
                'appId': self.app_id,
                'query': jan_code,
                'type': 'code',
                'hits': 1,
                'page': 1
            }
            
            # APIリクエスト実行
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # レスポンスの検証
            if not data.get('info') or data['info'].get('count', 0) == 0:
                logger.warning(f"No product found for JAN code: {jan_code}")
                return None
                
            # 商品情報を取得
            products = data.get('product', [])
            if not products:
                logger.warning(f"No product data for JAN code: {jan_code}")
                return None
                
            product = products[0]
            
            # 商品情報を正規化
            return self._normalize_product_data(product)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for JAN code {jan_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for JAN code {jan_code}: {e}")
            return None
            
    def _validate_jan_code(self, jan_code: str) -> bool:
        """
        JANコードのバリデーション
        
        Args:
            jan_code: JANコード
            
        Returns:
            有効な場合True
        """
        # 文字列チェック
        if not isinstance(jan_code, str):
            return False
            
        # 長さチェック（13桁または8桁）
        if len(jan_code) not in [8, 13]:
            return False
            
        # 数字のみチェック
        if not jan_code.isdigit():
            return False
            
        return True
        
    def _normalize_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        商品データの正規化
        
        Args:
            product: APIから取得した商品データ
            
        Returns:
            正規化された商品データ
        """
        return {
            'jan_code': product.get('codeNumber', ''),
            'code_type': product.get('codeType', ''),
            'product_name': product.get('itemName', ''),
            'product_model': product.get('itemModel', ''),
            'product_url': product.get('itemUrl', ''),
            'product_image_url': product.get('itemImageUrl', ''),
            'brand_name': product.get('brandName', ''),
            'maker_name': product.get('makerName', ''),
            'maker_name_kana': product.get('makerNameKana', ''),
            'product_details': product.get('ProductDetails', ''),
        }
        
    def search_by_keyword(self, keyword: str, hits: int = 30, page: int = 1) -> Optional[Dict[str, Any]]:
        """
        キーワードで商品検索
        
        Args:
            keyword: 検索キーワード
            hits: 取得件数
            page: ページ番号
            
        Returns:
            検索結果
        """
        try:
            # キーワードをURLエンコード
            encoded_keyword = urllib.parse.quote(keyword, encoding='utf-8')
            
            # APIリクエストパラメータ
            params = {
                'appId': self.app_id,
                'query': encoded_keyword,
                'type': 'keyword',
                'hits': hits,
                'page': page
            }
            
            # APIリクエスト実行
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 商品データを正規化
            if 'product' in data and data['product']:
                data['product'] = [self._normalize_product_data(p) for p in data['product']]
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for keyword {keyword}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for keyword {keyword}: {e}")
            return None


def get_product_name_from_jan(jan_code: str) -> Optional[str]:
    """
    JANコードから商品名を取得する関数
    
    Args:
        jan_code: JANコード
        
    Returns:
        商品名、見つからない場合はNone
    """
    # 実際のAPIを使用してJANコードから商品名を取得
    try:
        from ..utils.config import get_config
        app_id = get_config("JAN_LOOKUP_APP_ID", "")
        
        if app_id:
            client = JANLookupClient(app_id)
            product_data = client.lookup_product(jan_code)
            if product_data:
                product_name = product_data.get('product_name', '')
                if product_name:
                    # 商品名を検索しやすい形に簡略化
                    simplified_name = _simplify_product_name(product_name)
                    return simplified_name if simplified_name else product_name
                    
        logger.warning(f"No product found for JAN code {jan_code} via API")
        
    except Exception as e:
        logger.error(f"Failed to lookup JAN code {jan_code} via API: {e}")
    
    # APIで取得できない場合はNoneを返す（ハードコーディングなし）
    return None


def _simplify_product_name(product_name: str) -> str:
    """
    商品名を検索しやすい形に簡略化する
    
    Args:
        product_name: 元の商品名
        
    Returns:
        簡略化された商品名
    """
    if not product_name:
        return ""
    
    # MacBook Proの場合の簡略化
    if "MacBook Pro" in product_name or "MACBOOK PRO" in product_name:
        if "14" in product_name:
            return "MacBook Pro 14インチ"
        elif "16" in product_name:
            return "MacBook Pro 16インチ"
        else:
            return "MacBook Pro"
    
    # iPhone の場合の簡略化
    if "iPhone" in product_name or "IPHONE" in product_name:
        # iPhone 15 Pro などの抽出
        import re
        iphone_match = re.search(r'iPhone\s*(\d+)(?:\s*(Pro|Plus|mini))?', product_name, re.IGNORECASE)
        if iphone_match:
            model = iphone_match.group(1)
            variant = iphone_match.group(2) or ""
            return f"iPhone {model} {variant}".strip()
        return "iPhone"
    
    # iPad の場合の簡略化
    if "iPad" in product_name or "IPAD" in product_name:
        if "Pro" in product_name:
            return "iPad Pro"
        elif "Air" in product_name:
            return "iPad Air"
        elif "mini" in product_name:
            return "iPad mini"
        else:
            return "iPad"
    
    # その他の場合は最初の3つの単語を取得
    words = product_name.split()
    if len(words) > 3:
        return " ".join(words[:3])
    
    return product_name
