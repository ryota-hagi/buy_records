import logging
import time
from typing import Dict, List, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.search.platform_strategies import PlatformSearchManager
from src.jan.jan_lookup import get_product_name_from_jan

logger = logging.getLogger(__name__)

class SearchExecutor:
    """検索を実行し、結果を統合するクラス（プラットフォーム戦略対応版）"""
    
    def __init__(self, max_workers: int = 4, task_manager=None, task_id: str = None):
        """
        初期化
        
        Args:
            max_workers: 同時に実行するワーカー数
            task_manager: タスクマネージャー（進捗ログ用）
            task_id: タスクID（進捗ログ用）
        """
        self.max_workers = max_workers
        self.task_manager = task_manager
        self.task_id = task_id
        self.platform_manager = PlatformSearchManager()
    
    def execute_search(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        検索を実行する（正しいフロー）
        各プラットフォームから20件ずつ取得し、安い順に並べ替えて20件を表示
        
        Args:
            search_params: 検索パラメータ
                
        Returns:
            Dict[str, Any]: 検索結果
        """
        logger.info(f"Executing search with params: {search_params}")
        
        # 進捗ログ: 検索開始
        self._log_progress("search_started", "started", "検索を開始しました")
        
        # 検索パラメータを取得（JANコード検索に特化：eBay、メルカリ、Yahoo!ショッピングのみ）
        platforms = search_params.get('platforms', ['ebay', 'mercari', 'yahoo_shopping'])
        
        # Discogsを明示的に除外（JANコード検索に不適切なため）
        if 'discogs' in platforms:
            platforms.remove('discogs')
        if 'yahoo_auction' in platforms:
            platforms.remove('yahoo_auction')
            if 'yahoo_shopping' not in platforms:
                platforms.append('yahoo_shopping')
        
        # 進捗ログ: パラメータ解析完了
        self._log_progress("params_parsed", "completed", f"検索パラメータを解析しました。対象プラットフォーム: {', '.join(platforms)}")
        
        # 並列で各プラットフォームの検索を実行
        platform_results = {}
        
        # 進捗ログ: プラットフォーム検索開始
        self._log_progress("platform_search_started", "started", "プラットフォーム別検索を開始しました（各20件ずつ取得）")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 各プラットフォームの検索タスクを作成
            future_to_platform = {}
                
            if 'ebay' in platforms:
                self._log_progress("ebay_search", "started", platform="ebay")
                future = executor.submit(self._search_ebay, search_params)
                future_to_platform[future] = 'ebay'
                
            if 'mercari' in platforms:
                self._log_progress("mercari_search", "started", platform="mercari")
                future = executor.submit(self._search_mercari, search_params)
                future_to_platform[future] = 'mercari'
                
            if 'yahoo_shopping' in platforms:
                self._log_progress("yahoo_shopping_search", "started", platform="yahoo_shopping")
                future = executor.submit(self._search_yahoo_shopping, search_params)
                future_to_platform[future] = 'yahoo_shopping'
            
            # 結果を収集
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    result = future.result()
                    platform_results[platform] = result
                    count = result.get('count', 0) if 'error' not in result else 0
                    self._log_progress(f"{platform}_search", "completed", f"{platform}の検索が完了しました", platform=platform, count=count)
                    logger.info(f"Completed search for {platform}: {count} results")
                except Exception as e:
                    logger.error(f"Error searching {platform}: {e}")
                    platform_results[platform] = {'error': str(e), 'items': []}
                    self._log_progress(f"{platform}_search", "failed", f"{platform}の検索でエラーが発生しました: {str(e)}", platform=platform)
        
        # 進捗ログ: 結果統合開始
        self._log_progress("integration_started", "started", "検索結果を統合しています（安い順に並べ替え）")
        
        # 結果を統合
        integrated_results = self._integrate_results(platform_results, search_params)
        
        # 進捗ログ: 検索完了
        total_count = integrated_results.get('count', 0)
        self._log_progress("search_completed", "completed", f"検索が完了しました。総件数: {total_count}件", count=total_count)
        
        return {
            'search_params': search_params,
            'platform_results': platform_results,
            'integrated_results': integrated_results
        }
    
    def _log_progress(self, step: str, status: str, message: str = None, platform: str = None, count: int = None):
        """進捗ログを記録する"""
        if self.task_manager and self.task_id:
            try:
                self.task_manager.add_processing_log(
                    self.task_id, 
                    step, 
                    status, 
                    message=message, 
                    platform=platform, 
                    count=count
                )
            except Exception as e:
                logger.error(f"Error logging progress: {e}")
    
    def _search_ebay(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """eBayで検索を実行（プラットフォーム戦略使用）"""
        try:
            query = search_params.get('query', '')
            jan_code = query if query.isdigit() and len(query) >= 8 else None
            
            # プラットフォーム戦略を使用して検索
            items = self.platform_manager.search_platform('ebay', query, jan_code, 20)
            
            return {
                'items': items,
                'count': len(items)
            }
            
        except Exception as e:
            logger.error(f"Error in _search_ebay: {e}")
            return {'error': str(e), 'items': []}
    
    def _search_mercari(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """メルカリで検索を実行（プラットフォーム戦略使用）"""
        try:
            query = search_params.get('query', '')
            jan_code = query if query.isdigit() and len(query) >= 8 else None
            
            # アーティストとタイトルが指定されている場合は結合
            if search_params.get('artist') and search_params.get('title'):
                query = f"{search_params['artist']} {search_params['title']}"
            elif search_params.get('artist'):
                query = search_params['artist']
            elif search_params.get('title'):
                query = search_params['title']
            
            # プラットフォーム戦略を使用して検索
            items = self.platform_manager.search_platform('mercari', query, jan_code, 20)
            
            # 価格でフィルタリング
            if search_params.get('min_price') or search_params.get('max_price'):
                filtered_items = []
                
                for item in items:
                    price = item.get('total_price', 0)
                    
                    if search_params.get('min_price') and price < search_params['min_price']:
                        continue
                        
                    if search_params.get('max_price') and price > search_params['max_price']:
                        continue
                        
                    filtered_items.append(item)
                    
                items = filtered_items
            
            return {
                'items': items,
                'count': len(items)
            }
            
        except Exception as e:
            logger.error(f"Error in _search_mercari: {e}")
            return {'error': str(e), 'items': []}
    
    def _search_yahoo_shopping(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Yahoo!ショッピングで検索を実行（プラットフォーム戦略使用）"""
        try:
            query = search_params.get('query', '')
            jan_code = query if query.isdigit() and len(query) >= 8 else None
            
            # アーティストとタイトルが指定されている場合は結合
            if search_params.get('artist') and search_params.get('title'):
                query = f"{search_params['artist']} {search_params['title']}"
            elif search_params.get('artist'):
                query = search_params['artist']
            elif search_params.get('title'):
                query = search_params['title']
            
            # プラットフォーム戦略を使用して検索
            items = self.platform_manager.search_platform('yahoo_shopping', query, jan_code, 20)
            
            return {
                'items': items,
                'count': len(items)
            }
            
        except Exception as e:
            logger.error(f"Error in _search_yahoo_shopping: {e}")
            return {'error': str(e), 'items': []}
    
    def _integrate_results(self, platform_results: Dict[str, Dict[str, Any]], 
                          search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        各プラットフォームの結果を統合する（正しいフロー）
        各プラットフォームから最大20件ずつ取得し、安い順に並べ替えて20件を表示
        
        Args:
            platform_results: 各プラットフォームの検索結果
            search_params: 検索パラメータ
            
        Returns:
            Dict[str, Any]: 統合された結果
        """
        try:
            # 各プラットフォームのアイテムを取得
            all_items = []
            
            for platform, result in platform_results.items():
                if 'error' in result:
                    continue
                    
                items = result.get('items', [])
                
                # プラットフォーム戦略からの結果は既に統一フォーマットなので、そのまま使用
                for item in items:
                    # プラットフォーム戦略からの結果は既に統一フォーマット
                    # 互換性のため、追加フィールドを設定
                    formatted_item = item.copy()
                    
                    # 互換性フィールドを追加
                    formatted_item.update({
                        'title': item.get('item_title', ''),
                        'price': item.get('base_price', 0),
                        'url': item.get('item_url', ''),
                        'image_url': item.get('item_image_url', ''),
                        'condition': item.get('item_condition', ''),
                        'currency': item.get('currency', 'JPY'),
                        'seller': item.get('seller', ''),
                    })
                    
                    all_items.append(formatted_item)
            
            # 価格でソート（昇順）
            sorted_items = sorted(
                all_items, 
                key=lambda x: x.get('total_price', 0) if isinstance(x.get('total_price'), (int, float)) else 0
            )
            
            # 上位20件を取得
            final_items = sorted_items[:20]
            
            return {
                'items': final_items,
                'count': len(final_items)
            }
            
        except Exception as e:
            logger.error(f"Error in _integrate_results: {e}")
            raise
