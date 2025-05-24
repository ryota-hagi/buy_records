"""
JANコード検索エンジン
JANコードから商品情報を取得し、複数のプラットフォームで価格比較を行います。
プラットフォーム別検索戦略を使用した改良版。
"""

import concurrent.futures
from typing import Dict, Any, List, Optional
import logging
from src.search.platform_strategies import PlatformSearchManager
from src.jan.jan_lookup import get_product_name_from_jan

logger = logging.getLogger(__name__)


class JANSearchEngine:
    """JANコード商品検索エンジン（プラットフォーム戦略対応版）"""
    
    def __init__(self):
        """検索エンジンを初期化"""
        self.platform_manager = PlatformSearchManager()
        # デフォルトの検索対象プラットフォーム（全プラットフォーム）
        self.default_platforms = ['mercari', 'yahoo_shopping', 'yahoo_auction', 'ebay']
        
    def search_by_jan(self, jan_code: str, limit: int = 20, platforms: List[str] = None) -> List[Dict[str, Any]]:
        """
        JANコードで商品を検索し、価格順にソートした結果を返します。
        各プラットフォームから20個ずつ取得し、統合して最安値順に並び替えて最終的に20個のリストにします。
        
        Args:
            jan_code: JANコード
            limit: 最終的に取得する結果の最大数（デフォルト20）
            platforms: 検索対象のプラットフォームリスト（Noneの場合はデフォルト）
            
        Returns:
            List[Dict[str, Any]]: 価格順にソートされた商品リスト（最大limit件）
        """
        try:
            logger.info(f"Starting search for JAN code: {jan_code}")
            
            # 検索対象プラットフォームを決定
            if platforms is None:
                platforms = self.default_platforms
            
            # JANコードから商品名を取得（フォールバック用）
            product_name = get_product_name_from_jan(jan_code)
            if product_name:
                logger.info(f"Product name from JAN code: {product_name}")
            
            # 各プラットフォームから20個ずつ並列で検索
            all_results = []
            platform_results_count = {}
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(platforms)) as executor:
                # 各プラットフォームでの検索を並列実行（各プラットフォームから20個ずつ取得）
                future_to_platform = {}
                
                for platform in platforms:
                    future = executor.submit(
                        self.platform_manager.search_platform,
                        platform,
                        jan_code,  # クエリとしてJANコードを渡す
                        jan_code,  # JANコードパラメータ
                        20  # 各プラットフォームから20個ずつ取得
                    )
                    future_to_platform[future] = platform
                
                # 結果を収集
                for future in concurrent.futures.as_completed(future_to_platform):
                    platform = future_to_platform[future]
                    try:
                        platform_results = future.result(timeout=30)
                        if platform_results:
                            all_results.extend(platform_results)
                            platform_results_count[platform] = len(platform_results)
                            logger.info(f"{platform}: {len(platform_results)} items found")
                        else:
                            platform_results_count[platform] = 0
                            logger.info(f"{platform}: No items found")
                    except Exception as e:
                        platform_results_count[platform] = 0
                        logger.error(f"Platform search failed for {platform}: {e}")
            
            # プラットフォーム別の取得件数をログ出力
            total_found = sum(platform_results_count.values())
            logger.info(f"Platform results summary: {platform_results_count}, Total: {total_found}")
            
            # 全結果を価格順にソートして最終的にlimit件を取得
            sorted_results = self._sort_and_format_results(all_results, limit)
            
            logger.info(f"Search completed: {len(sorted_results)} results returned (from {total_found} total)")
            return sorted_results
            
        except Exception as e:
            logger.error(f"Error in search_by_jan: {e}")
            return []
    
    def search_by_product_name(self, product_name: str, limit: int = 20, platforms: List[str] = None) -> List[Dict[str, Any]]:
        """
        商品名で商品を検索し、価格順にソートした結果を返します。
        
        Args:
            product_name: 商品名
            limit: 取得する結果の最大数
            platforms: 検索対象のプラットフォームリスト（Noneの場合はデフォルト）
            
        Returns:
            List[Dict[str, Any]]: 価格順にソートされた商品リスト
        """
        try:
            logger.info(f"Starting search for product name: {product_name}")
            
            # 検索対象プラットフォームを決定
            if platforms is None:
                platforms = self.default_platforms
            
            # 各プラットフォームから並列で検索
            all_results = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(platforms)) as executor:
                # 各プラットフォームでの検索を並列実行
                future_to_platform = {}
                
                for platform in platforms:
                    future = executor.submit(
                        self.platform_manager.search_platform,
                        platform,
                        product_name,  # クエリとして商品名を渡す
                        None,  # JANコードなし
                        limit
                    )
                    future_to_platform[future] = platform
                
                # 結果を収集
                for future in concurrent.futures.as_completed(future_to_platform):
                    platform = future_to_platform[future]
                    try:
                        platform_results = future.result(timeout=30)
                        if platform_results:
                            all_results.extend(platform_results)
                            logger.info(f"{platform}: {len(platform_results)} items found")
                        else:
                            logger.info(f"{platform}: No items found")
                    except Exception as e:
                        logger.error(f"Platform search failed for {platform}: {e}")
            
            # 結果を価格順にソートして上位を取得
            sorted_results = self._sort_and_format_results(all_results, limit)
            
            logger.info(f"Search completed: {len(sorted_results)} results found")
            return sorted_results
            
        except Exception as e:
            logger.error(f"Error in search_by_product_name: {e}")
            return []
    
    def _sort_and_format_results(self, results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """
        結果を価格順にソートし、フォーマットします。
        
        Args:
            results: 検索結果のリスト
            limit: 取得する結果の最大数
            
        Returns:
            ソートされた結果のリスト
        """
        try:
            # 価格が0より大きい結果のみを対象とする
            valid_results = [r for r in results if r.get('total_price', 0) > 0]
            
            # 価格順（昇順）でソート
            sorted_results = sorted(valid_results, key=lambda x: x.get('total_price', float('inf')))
            
            # 上位limit件を取得
            return sorted_results[:limit]
            
        except Exception as e:
            logger.error(f"Error sorting results: {e}")
            return results[:limit]
    
    def get_search_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        検索結果のサマリーを取得します。
        
        Args:
            results: 検索結果のリスト
            
        Returns:
            サマリー情報
        """
        if not results:
            return {
                'total_count': 0,
                'lowest_price': 0,
                'highest_price': 0,
                'average_price': 0,
                'median_price': 0,
                'platform_counts': {}
            }
        
        prices = [r['total_price'] for r in results if r['total_price'] > 0]
        platform_counts = {}
        
        for result in results:
            platform = result.get('platform', 'Unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        # 中央値を計算
        median_price = 0
        if prices:
            prices_sorted = sorted(prices)
            mid = len(prices_sorted) // 2
            if len(prices_sorted) % 2 == 0 and len(prices_sorted) > 1:
                median_price = (prices_sorted[mid - 1] + prices_sorted[mid]) / 2
            else:
                median_price = prices_sorted[mid]
        
        return {
            'total_count': len(results),
            'lowest_price': min(prices) if prices else 0,
            'highest_price': max(prices) if prices else 0,
            'average_price': sum(prices) // len(prices) if prices else 0,
            'median_price': int(median_price),
            'platform_counts': platform_counts
        }
    
    def get_platform_results(self, jan_code: str = None, product_name: str = None, limit: int = 20, platforms: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        プラットフォーム別の検索結果を取得します。
        
        Args:
            jan_code: JANコード（指定された場合）
            product_name: 商品名（指定された場合）
            limit: 各プラットフォームで取得する結果の最大数
            platforms: 検索対象のプラットフォームリスト（Noneの場合はデフォルト）
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: プラットフォーム別の検索結果
        """
        try:
            # 検索対象プラットフォームを決定
            if platforms is None:
                platforms = self.default_platforms
            
            # 検索クエリを決定
            query = jan_code if jan_code else product_name
            if not query:
                logger.error("JANコードまたは商品名のいずれかを指定してください")
                return {}
            
            # プラットフォーム別検索を実行
            results = self.platform_manager.search_all_platforms(
                query=query,
                jan_code=jan_code,
                platforms=platforms,
                limit=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in get_platform_results: {e}")
            return {}
    
    def get_available_platforms(self) -> List[str]:
        """
        利用可能なプラットフォームのリストを取得します。
        
        Returns:
            List[str]: 利用可能なプラットフォーム名のリスト
        """
        return list(self.platform_manager.strategies.keys())
