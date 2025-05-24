"""JANコード検索タスクマネージャー"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from src.utils.supabase_client import SupabaseClient
from src.jan.jan_lookup import JANLookupClient
from src.pricing.calculator import PriceCalculator

logger = logging.getLogger(__name__)


class JANSearchTaskManager:
    """JANコード検索タスクの管理クラス"""
    
    def __init__(self, supabase_client: SupabaseClient, jan_lookup_client: JANLookupClient):
        """
        初期化
        
        Args:
            supabase_client: Supabaseクライアント
            jan_lookup_client: JANコードルックアップクライアント
        """
        self.supabase = supabase_client
        self.jan_lookup = jan_lookup_client
        self.price_calculator = PriceCalculator()
        
    def create_task(self, jan_code: str) -> Optional[Dict[str, Any]]:
        """
        新しい検索タスクを作成
        
        Args:
            jan_code: JANコード
            
        Returns:
            作成されたタスク情報
        """
        try:
            # JANコードから商品情報を取得
            product_info = self.jan_lookup.lookup_product(jan_code)
            if not product_info:
                logger.error(f"Product not found for JAN code: {jan_code}")
                return None
                
            # タスクデータを準備
            task_data = {
                'id': str(uuid.uuid4()),
                'jan_code': jan_code,
                'product_name': product_info.get('product_name', ''),
                'brand_name': product_info.get('brand_name', ''),
                'maker_name': product_info.get('maker_name', ''),
                'product_image_url': product_info.get('product_image_url', ''),
                'product_url': product_info.get('product_url', ''),
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # データベースに保存
            result = self.supabase.table('jan_search_tasks').insert(task_data).execute()
            
            if result.data:
                logger.info(f"Task created successfully: {task_data['id']}")
                return result.data[0]
            else:
                logger.error(f"Failed to create task for JAN code: {jan_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating task for JAN code {jan_code}: {e}")
            return None
            
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        タスク情報を取得
        
        Args:
            task_id: タスクID
            
        Returns:
            タスク情報
        """
        try:
            result = self.supabase.table('jan_search_tasks').select('*').eq('id', task_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                logger.warning(f"Task not found: {task_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
            
    def update_task_status(self, task_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """
        タスクステータスを更新
        
        Args:
            task_id: タスクID
            status: 新しいステータス
            error_message: エラーメッセージ（オプション）
            
        Returns:
            更新成功の場合True
        """
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if status == 'completed':
                update_data['completed_at'] = datetime.now().isoformat()
            elif status == 'failed' and error_message:
                update_data['error_message'] = error_message
                
            result = self.supabase.table('jan_search_tasks').update(update_data).eq('id', task_id).execute()
            
            if result.data:
                logger.info(f"Task status updated: {task_id} -> {status}")
                return True
            else:
                logger.error(f"Failed to update task status: {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating task status {task_id}: {e}")
            return False
            
    def get_tasks(self, 
                  status: Optional[str] = None, 
                  limit: int = 10, 
                  offset: int = 0) -> List[Dict[str, Any]]:
        """
        タスク一覧を取得
        
        Args:
            status: フィルターするステータス
            limit: 取得件数
            offset: オフセット
            
        Returns:
            タスク一覧
        """
        try:
            query = self.supabase.table('jan_search_tasks').select('*')
            
            if status:
                query = query.eq('status', status)
                
            query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []
            
    def save_search_results(self, task_id: str, results: List[Dict[str, Any]]) -> bool:
        """
        検索結果を保存
        
        Args:
            task_id: タスクID
            results: 検索結果のリスト
            
        Returns:
            保存成功の場合True
        """
        try:
            # 既存の結果を削除
            self.supabase.table('search_results').delete().eq('task_id', task_id).execute()
            
            # 新しい結果を保存
            search_results = []
            for result in results:
                # 価格計算
                price_info = self.price_calculator.calculate_total_price(
                    result.get('price', 0),
                    result.get('platform', ''),
                    result
                )
                
                search_result = {
                    'id': str(uuid.uuid4()),
                    'task_id': task_id,
                    'platform': result.get('platform', ''),
                    'item_title': result.get('title', ''),
                    'price': float(price_info['base_price']),
                    'shipping_fee': float(price_info['shipping_fee']),
                    'service_fee': float(price_info['service_fee'] + price_info['payment_fee']),
                    'currency': result.get('currency', 'JPY'),
                    'item_url': result.get('url', ''),
                    'item_image_url': result.get('image_url', ''),
                    'seller_name': result.get('seller', ''),
                    'condition_text': result.get('condition', ''),
                    'created_at': datetime.now().isoformat(),
                    'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
                }
                search_results.append(search_result)
                
            if search_results:
                result = self.supabase.table('search_results').insert(search_results).execute()
                
                if result.data:
                    logger.info(f"Saved {len(search_results)} search results for task {task_id}")
                    return True
                else:
                    logger.error(f"Failed to save search results for task {task_id}")
                    return False
            else:
                logger.warning(f"No search results to save for task {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving search results for task {task_id}: {e}")
            return False
            
    def get_search_results(self, task_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        検索結果を取得（総額でソート）
        
        Args:
            task_id: タスクID
            limit: 取得件数
            
        Returns:
            検索結果のリスト
        """
        try:
            result = self.supabase.table('search_results').select('*').eq('task_id', task_id).order('total_price').limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting search results for task {task_id}: {e}")
            return []
            
    def cleanup_expired_results(self) -> int:
        """
        期限切れの検索結果を削除
        
        Returns:
            削除された件数
        """
        try:
            # 期限切れの結果を削除
            result = self.supabase.rpc('cleanup_expired_search_results').execute()
            
            deleted_count = result.data if result.data else 0
            logger.info(f"Cleaned up {deleted_count} expired search results")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired results: {e}")
            return 0
            
    def cancel_task(self, task_id: str) -> bool:
        """
        タスクをキャンセル
        
        Args:
            task_id: タスクID
            
        Returns:
            キャンセル成功の場合True
        """
        try:
            # タスクの現在のステータスを確認
            task = self.get_task(task_id)
            if not task:
                logger.error(f"Task not found for cancellation: {task_id}")
                return False
                
            if task['status'] in ['completed', 'failed', 'cancelled']:
                logger.warning(f"Cannot cancel task in status {task['status']}: {task_id}")
                return False
                
            # ステータスをキャンセルに更新
            return self.update_task_status(task_id, 'cancelled')
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
