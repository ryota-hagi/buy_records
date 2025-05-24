"""
プラットフォーム別検索戦略
各プラットフォームの特性に応じた検索方法を実装します。
"""

import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from src.jan.jan_lookup import get_product_name_from_jan
from src.utils.translator import translator
from src.utils.exchange_rate import get_usd_to_jpy_rate
from src.collectors.yahoo_shopping import YahooShoppingClient
from src.collectors.mercari_simple import MercariClient
from src.collectors.ebay import EbayClient
from src.collectors.yahoo_auction import YahooAuctionClient

logger = logging.getLogger(__name__)


class PlatformSearchStrategy(ABC):
    """プラットフォーム検索戦略の基底クラス"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
    
    @abstractmethod
    def search(self, query: str, jan_code: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        検索を実行します。
        
        Args:
            query: 検索クエリ（商品名またはJANコード）
            jan_code: JANコード（指定された場合）
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        pass
    
    def _format_result(self, item: Dict[str, Any], search_term: str) -> Dict[str, Any]:
        """
        検索結果を統一フォーマットに変換します。
        
        Args:
            item: 元の検索結果
            search_term: 検索に使用したクエリ
            
        Returns:
            Dict[str, Any]: 統一フォーマットの検索結果
        """
        return {
            'platform': self.platform_name,
            'item_id': item.get('item_id', ''),
            'item_title': item.get('title', item.get('name', '')),
            'item_url': item.get('url', ''),
            'item_image_url': item.get('image_url', ''),
            'item_condition': item.get('condition', ''),
            'base_price': item.get('price', 0),
            'shipping_fee': item.get('shipping_fee', 0),
            'total_price': item.get('price', 0) + item.get('shipping_fee', 0),
            'currency': item.get('currency', 'JPY'),
            'seller': item.get('seller', ''),
            'search_term': search_term
        }


class YahooShoppingStrategy(PlatformSearchStrategy):
    """Yahoo!ショッピング検索戦略"""
    
    def __init__(self):
        super().__init__('Yahoo!ショッピング')
        self.client = YahooShoppingClient()
    
    def search(self, query: str, jan_code: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Yahoo!ショッピングで検索を実行します。
        JANコードがある場合はJANコード検索を優先し、結果がない場合は商品名検索にフォールバック。
        
        Args:
            query: 検索クエリ（商品名またはJANコード）
            jan_code: JANコード（指定された場合）
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        try:
            results = []
            search_term = query
            
            # JANコードが指定されている場合、まずJANコード検索を試行
            if jan_code and jan_code.isdigit() and len(jan_code) >= 8:
                logger.info(f"Yahoo!ショッピング: JANコード検索を実行 - {jan_code}")
                results = self.client.search_by_jan_code(jan_code, limit)
                search_term = jan_code
                
                if results:
                    logger.info(f"Yahoo!ショッピング: JANコード検索で{len(results)}件取得")
                else:
                    logger.info("Yahoo!ショッピング: JANコード検索で結果なし、商品名検索にフォールバック")
            
            # JANコード検索で結果がない場合、または最初から商品名検索の場合
            if not results:
                # JANコードから商品名を取得
                if jan_code and jan_code.isdigit() and len(jan_code) >= 8:
                    product_name = get_product_name_from_jan(jan_code)
                    if product_name:
                        search_term = product_name
                        logger.info(f"Yahoo!ショッピング: JANコードから商品名を取得 - {product_name}")
                    else:
                        search_term = jan_code
                else:
                    search_term = query
                
                logger.info(f"Yahoo!ショッピング: 商品名検索を実行 - {search_term}")
                results = self.client.search_items(search_term, limit)
                logger.info(f"Yahoo!ショッピング: 商品名検索で{len(results)}件取得")
            
            # 結果を統一フォーマットに変換
            formatted_results = []
            for item in results:
                # Yahoo!ショッピングの送料情報を処理
                shipping_fee = 0
                if not item.get('shipping_info', {}).get('free_shipping', False):
                    shipping_fee = item.get('shipping_info', {}).get('shipping_cost', 0)
                
                formatted_item = {
                    'platform': self.platform_name,
                    'item_id': item.get('item_id', ''),
                    'item_title': item.get('title', item.get('name', '')),
                    'item_url': item.get('url', ''),
                    'item_image_url': item.get('image_url', ''),
                    'item_condition': item.get('condition', 'new'),
                    'base_price': item.get('price', 0),
                    'shipping_fee': shipping_fee,
                    'total_price': item.get('price', 0) + shipping_fee,
                    'currency': 'JPY',
                    'seller': item.get('store_name', ''),
                    'search_term': search_term
                }
                formatted_results.append(formatted_item)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Yahoo!ショッピング検索エラー: {e}")
            return []


class MercariStrategy(PlatformSearchStrategy):
    """メルカリ検索戦略"""
    
    def __init__(self):
        super().__init__('メルカリ')
        self.client = MercariClient()
    
    def search(self, query: str, jan_code: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        メルカリで検索を実行します。
        商品名での検索のみ実行（JANコードの場合は商品名に変換）。
        
        Args:
            query: 検索クエリ（商品名またはJANコード）
            jan_code: JANコード（指定された場合）
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        try:
            search_term = query
            
            # JANコードが指定されている場合、商品名に変換
            if jan_code and jan_code.isdigit() and len(jan_code) >= 8:
                product_name = get_product_name_from_jan(jan_code)
                if product_name:
                    search_term = product_name
                    logger.info(f"メルカリ: JANコードから商品名を取得 - {product_name}")
                else:
                    search_term = jan_code
                    logger.info(f"メルカリ: JANコードから商品名を取得できず、JANコードで検索 - {jan_code}")
            
            logger.info(f"メルカリ: 商品名検索を実行 - {search_term}")
            results = self.client.search_active_items(search_term, limit)
            logger.info(f"メルカリ: {len(results)}件取得")
            
            # 結果を統一フォーマットに変換
            formatted_results = []
            for item in results:
                formatted_item = {
                    'platform': self.platform_name,
                    'item_id': item.get('item_id', ''),
                    'item_title': item.get('title', ''),
                    'item_url': item.get('url', ''),
                    'item_image_url': item.get('image_url', ''),
                    'item_condition': item.get('condition', ''),
                    'base_price': item.get('price', 0),
                    'shipping_fee': item.get('shipping_fee', 0),
                    'total_price': item.get('price', 0) + item.get('shipping_fee', 0),
                    'currency': 'JPY',
                    'seller': item.get('seller', ''),
                    'search_term': search_term
                }
                formatted_results.append(formatted_item)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"メルカリ検索エラー: {e}")
            return []


class EbayStrategy(PlatformSearchStrategy):
    """eBay検索戦略"""
    
    def __init__(self):
        super().__init__('eBay')
        self.client = EbayClient()
    
    def search(self, query: str, jan_code: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        eBayで検索を実行します。
        複数の英語クエリを生成して段階的に検索を実行。
        
        Args:
            query: 検索クエリ（商品名またはJANコード）
            jan_code: JANコード（指定された場合）
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        try:
            search_term = query
            
            # JANコードが指定されている場合、商品名に変換
            if jan_code and jan_code.isdigit() and len(jan_code) >= 8:
                product_name = get_product_name_from_jan(jan_code)
                if product_name:
                    search_term = product_name
                    logger.info(f"eBay: JANコードから商品名を取得 - {product_name}")
                else:
                    search_term = jan_code
                    logger.info(f"eBay: JANコードから商品名を取得できず、JANコードで検索 - {jan_code}")
            
            # 複数の英語クエリを生成
            english_queries = translator.generate_multiple_queries(search_term)
            logger.info(f"eBay: {len(english_queries)}個の英語クエリを生成")
            
            all_results = []
            total_found = 0
            
            # 各クエリで段階的に検索実行
            for i, english_query in enumerate(english_queries, 1):
                if total_found >= limit:
                    logger.info(f"eBay: 十分な結果が得られたため検索を終了 ({total_found}件)")
                    break
                
                logger.info(f"eBay: クエリ{i}/{len(english_queries)}で検索実行 - '{english_query}'")
                
                try:
                    # 残りの必要件数を計算
                    remaining_limit = limit - total_found
                    query_limit = min(remaining_limit, 10)  # 1クエリあたり最大10件
                    
                    results = self.client.search_active_items(english_query, query_limit)
                    logger.info(f"eBay: クエリ{i}で{len(results)}件取得")
                    
                    if results:
                        # 結果を統一フォーマットに変換
                        formatted_results = self._format_ebay_results(results, english_query)
                        
                        # 重複除去（同じitem_idの商品は除外）
                        existing_ids = {item.get('item_id') for item in all_results}
                        new_results = [item for item in formatted_results 
                                     if item.get('item_id') not in existing_ids]
                        
                        all_results.extend(new_results)
                        total_found = len(all_results)
                        
                        logger.info(f"eBay: クエリ{i}で新規{len(new_results)}件追加（累計{total_found}件）")
                        
                        # 十分な結果が得られた場合は早期終了
                        if total_found >= limit:
                            break
                    else:
                        logger.info(f"eBay: クエリ{i}で結果なし")
                        
                except Exception as query_error:
                    logger.warning(f"eBay: クエリ{i}の検索でエラー - {query_error}")
                    continue
            
            # 結果を価格順でソート
            all_results.sort(key=lambda x: x.get('total_price', 0))
            
            # 指定された件数に制限
            final_results = all_results[:limit]
            
            logger.info(f"eBay: 最終結果{len(final_results)}件を返却")
            return final_results
            
        except Exception as e:
            logger.error(f"eBay検索エラー: {e}")
            return []
    
    def _format_ebay_results(self, results: List[Dict[str, Any]], search_query: str) -> List[Dict[str, Any]]:
        """
        eBay検索結果を統一フォーマットに変換します。
        
        Args:
            results: eBayからの検索結果
            search_query: 使用した検索クエリ
            
        Returns:
            List[Dict[str, Any]]: 統一フォーマットの検索結果
        """
        formatted_results = []
        
        for item in results:
            try:
                # 価格をJPYに変換
                price = item.get('price', 0)
                currency = item.get('currency', 'USD')
                if currency == 'USD':
                    # ExchangeRate-APIからリアルタイムレートを取得
                    usd_to_jpy_rate = get_usd_to_jpy_rate()
                    price_jpy = int(price * usd_to_jpy_rate)
                    logger.debug(f"eBay: USD価格 ${price} を JPY {price_jpy} に変換（レート: {usd_to_jpy_rate}）")
                else:
                    price_jpy = int(price)
                
                # 商品タイトルの関連性をチェック
                relevance_score = self._calculate_relevance_score(item.get('title', ''), search_query)
                
                formatted_item = {
                    'platform': self.platform_name,
                    'item_id': item.get('item_id', ''),
                    'item_title': item.get('title', ''),
                    'item_url': item.get('url', ''),
                    'item_image_url': item.get('image_url', ''),
                    'item_condition': item.get('condition', ''),
                    'base_price': price_jpy,
                    'shipping_fee': 0,  # eBayは送料込み価格として扱う
                    'total_price': price_jpy,
                    'currency': 'JPY',
                    'seller': item.get('seller', ''),
                    'search_term': search_query,
                    'relevance_score': relevance_score
                }
                
                # 価格が妥当な範囲内かチェック
                if self._is_price_reasonable(price_jpy):
                    formatted_results.append(formatted_item)
                else:
                    logger.debug(f"eBay: 価格が異常なため除外 - {price_jpy}円: {item.get('title', '')}")
                    
            except Exception as format_error:
                logger.warning(f"eBay: 結果フォーマット中にエラー - {format_error}")
                continue
        
        return formatted_results
    
    def _calculate_relevance_score(self, title: str, search_query: str) -> float:
        """
        商品タイトルと検索クエリの関連性スコアを計算します。
        
        Args:
            title: 商品タイトル
            search_query: 検索クエリ
            
        Returns:
            float: 関連性スコア（0.0-1.0）
        """
        if not title or not search_query:
            return 0.0
        
        title_lower = title.lower()
        query_lower = search_query.lower()
        
        # 検索クエリの単語を分割
        query_words = query_lower.split()
        
        # タイトルに含まれる検索語の割合を計算
        matched_words = 0
        for word in query_words:
            if len(word) > 2 and word in title_lower:  # 2文字以下の単語は除外
                matched_words += 1
        
        if len(query_words) == 0:
            return 0.0
        
        return matched_words / len(query_words)
    
    def _is_price_reasonable(self, price_jpy: int) -> bool:
        """
        価格が妥当な範囲内かチェックします。
        極端に安い商品や高い商品を除外します。
        
        Args:
            price_jpy: 価格（円）
            
        Returns:
            bool: 価格が妥当な場合True
        """
        # 極端に安い（500円未満）または高い（100万円以上）価格を除外
        # Nintendo Switchの場合、本体だけでなくソフトやアクセサリーも含める
        return 500 <= price_jpy <= 1000000


class YahooAuctionStrategy(PlatformSearchStrategy):
    """Yahoo!オークション検索戦略"""
    
    def __init__(self):
        super().__init__('Yahoo!オークション')
        self.client = YahooAuctionClient()
    
    def search(self, query: str, jan_code: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Yahoo!オークションで検索を実行します。
        商品名での検索を実行（JANコードの場合は商品名に変換）。
        
        Args:
            query: 検索クエリ（商品名またはJANコード）
            jan_code: JANコード（指定された場合）
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        try:
            search_term = query
            
            # JANコードが指定されている場合、商品名に変換
            if jan_code and jan_code.isdigit() and len(jan_code) >= 8:
                product_name = get_product_name_from_jan(jan_code)
                if product_name:
                    search_term = product_name
                    logger.info(f"Yahoo!オークション: JANコードから商品名を取得 - {product_name}")
                else:
                    search_term = jan_code
                    logger.info(f"Yahoo!オークション: JANコードから商品名を取得できず、JANコードで検索 - {jan_code}")
            
            logger.info(f"Yahoo!オークション: 商品名検索を実行 - {search_term}")
            results = self.client.search_active_items(search_term, limit)
            logger.info(f"Yahoo!オークション: {len(results)}件取得")
            
            # 結果を統一フォーマットに変換
            formatted_results = []
            for item in results:
                formatted_item = {
                    'platform': self.platform_name,
                    'item_id': item.get('item_id', ''),
                    'item_title': item.get('title', ''),
                    'item_url': item.get('url', ''),
                    'item_image_url': item.get('image_url', ''),
                    'item_condition': item.get('condition', ''),
                    'base_price': item.get('price', 0),
                    'shipping_fee': item.get('shipping_fee', 0),
                    'total_price': item.get('price', 0) + item.get('shipping_fee', 0),
                    'currency': 'JPY',
                    'seller': item.get('seller', ''),
                    'search_term': search_term
                }
                formatted_results.append(formatted_item)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Yahoo!オークション検索エラー: {e}")
            return []


class DiscogsStrategy(PlatformSearchStrategy):
    """Discogs検索戦略"""
    
    def __init__(self):
        super().__init__('Discogs')
        # Discogsクライアントは後で実装
        self.client = None
    
    def search(self, query: str, jan_code: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Discogsで検索を実行します。
        英訳した商品名での検索を実行（JANコードの場合は商品名に変換してから英訳）。
        
        Args:
            query: 検索クエリ（商品名またはJANコード）
            jan_code: JANコード（指定された場合）
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        try:
            # Discogsクライアントが実装されていない場合は空の結果を返す
            if not self.client:
                logger.warning("Discogs検索: クライアントが実装されていません")
                return []
            
            search_term = query
            
            # JANコードが指定されている場合、商品名に変換
            if jan_code and jan_code.isdigit() and len(jan_code) >= 8:
                product_name = get_product_name_from_jan(jan_code)
                if product_name:
                    search_term = product_name
                    logger.info(f"Discogs: JANコードから商品名を取得 - {product_name}")
                else:
                    search_term = jan_code
                    logger.info(f"Discogs: JANコードから商品名を取得できず、JANコードで検索 - {jan_code}")
            
            # 商品名を英語に翻訳
            english_query = translator.translate_product_name(search_term)
            logger.info(f"Discogs: 英語翻訳 '{search_term}' -> '{english_query}'")
            
            logger.info(f"Discogs: 英語クエリで検索を実行 - {english_query}")
            # TODO: Discogsクライアントの実装後に有効化
            # results = self.client.search_items(english_query, limit)
            results = []
            logger.info(f"Discogs: {len(results)}件取得")
            
            # 結果を統一フォーマットに変換
            formatted_results = []
            for item in results:
                formatted_item = {
                    'platform': self.platform_name,
                    'item_id': item.get('item_id', ''),
                    'item_title': item.get('title', ''),
                    'item_url': item.get('url', ''),
                    'item_image_url': item.get('image_url', ''),
                    'item_condition': item.get('condition', ''),
                    'base_price': item.get('price', 0),
                    'shipping_fee': item.get('shipping_fee', 0),
                    'total_price': item.get('price', 0) + item.get('shipping_fee', 0),
                    'currency': item.get('currency', 'USD'),
                    'seller': item.get('seller', ''),
                    'search_term': english_query
                }
                formatted_results.append(formatted_item)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Discogs検索エラー: {e}")
            return []


class PlatformSearchManager:
    """プラットフォーム検索管理クラス"""
    
    def __init__(self):
        """検索管理クラスを初期化"""
        self.strategies = {
            'yahoo_shopping': YahooShoppingStrategy(),
            'mercari': MercariStrategy(),
            'ebay': EbayStrategy(),
            'yahoo_auction': YahooAuctionStrategy(),
            'discogs': DiscogsStrategy()
        }
    
    def search_platform(self, platform: str, query: str, jan_code: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        指定されたプラットフォームで検索を実行します。
        
        Args:
            platform: プラットフォーム名
            query: 検索クエリ
            jan_code: JANコード（指定された場合）
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        if platform not in self.strategies:
            logger.error(f"未対応のプラットフォーム: {platform}")
            return []
        
        strategy = self.strategies[platform]
        return strategy.search(query, jan_code, limit)
    
    def search_all_platforms(self, query: str, jan_code: str = None, platforms: List[str] = None, limit: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """
        複数のプラットフォームで検索を実行します。
        
        Args:
            query: 検索クエリ
            jan_code: JANコード（指定された場合）
            platforms: 検索対象のプラットフォームリスト（Noneの場合は全プラットフォーム）
            limit: 各プラットフォームで取得する結果の最大数
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: プラットフォーム別の検索結果
        """
        if platforms is None:
            platforms = list(self.strategies.keys())
        
        results = {}
        for platform in platforms:
            if platform in self.strategies:
                results[platform] = self.search_platform(platform, query, jan_code, limit)
            else:
                logger.warning(f"未対応のプラットフォームをスキップ: {platform}")
                results[platform] = []
        
        return results
