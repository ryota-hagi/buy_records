import uuid
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from src.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """検索タスクのステータスを表す列挙型"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SearchTaskManager:
    """検索タスクを管理するクラス"""
    
    def __init__(self):
        """初期化"""
        self.supabase = get_supabase_client()
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """検索タスクテーブルが存在することを確認し、なければ作成する"""
        try:
            # テーブルが存在するか確認
            try:
                # テーブルからデータを取得してみる（テーブルが存在するか確認するため）
                self.supabase.table('search_tasks').select('id').limit(1).execute()
                logger.info("search_tasksテーブルは既に存在します")
                return
            except Exception as e:
                # テーブルが存在しない場合は作成する
                if "relation" in str(e) and "does not exist" in str(e):
                    logger.info("search_tasksテーブルが存在しないため、作成します")
                    
                    # テーブルを作成するためのスクリプトを実行
                    import subprocess
                    import os
                    
                    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                              'scripts', 'create_search_tasks_table_direct.py')
                    
                    result = subprocess.run(['python', script_path], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error(f"テーブル作成に失敗しました: {result.stderr}")
                        raise Exception(f"テーブル作成に失敗しました: {result.stderr}")
                    
                    logger.info("search_tasksテーブルが正常に作成されました")
                else:
                    # その他のエラーの場合はそのまま例外を投げる
                    raise e
        except Exception as e:
            logger.error(f"Error ensuring search_tasks table exists: {e}")
            raise
    
    def create_task(self, name: str, search_params: Dict[str, Any]) -> str:
        """
        新しい検索タスクを作成する
        
        Args:
            name: タスクの名前
            search_params: 検索パラメータ
            
        Returns:
            str: 作成されたタスクのID
        """
        try:
            task_id = str(uuid.uuid4())
            
            # タスクをデータベースに挿入
            task_data = {
                'id': task_id,
                'name': name,
                'status': TaskStatus.PENDING.value,
                'search_params': json.dumps(search_params),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('search_tasks').insert(task_data).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error creating search task: {result.error}")
                raise Exception(f"Error creating search task: {result.error}")
            
            logger.info(f"Created search task: {task_id}")
            return task_id
        
        except Exception as e:
            logger.error(f"Error creating search task: {e}")
            raise
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        タスクの情報を取得する
        
        Args:
            task_id: タスクID
            
        Returns:
            Dict[str, Any] or None: タスク情報、存在しない場合はNone
        """
        try:
            result = self.supabase.table('search_tasks').select('*').eq('id', task_id).execute()
            
            if not result.data or len(result.data) == 0:
                return None
                
            task_data = result.data[0]
            
            # JSONBフィールドをパース
            if task_data.get('search_params'):
                if isinstance(task_data['search_params'], str):
                    task_data['search_params'] = json.loads(task_data['search_params'])
            
            if task_data.get('result'):
                if isinstance(task_data['result'], str):
                    task_data['result'] = json.loads(task_data['result'])
                
            return task_data
            
        except Exception as e:
            logger.error(f"Error getting search task {task_id}: {e}")
            raise
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          result: Optional[Dict[str, Any]] = None, 
                          error: Optional[str] = None,
                          processing_logs: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        タスクのステータスを更新する
        
        Args:
            task_id: タスクID
            status: 新しいステータス
            result: タスク結果（オプション）
            error: エラーメッセージ（オプション）
            processing_logs: 処理ログ（オプション）
        """
        try:
            # 更新データを準備
            update_data = {
                'status': status.value,
                'updated_at': datetime.now().isoformat()
            }
            
            # 完了時刻を設定（完了または失敗の場合）
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                update_data['completed_at'] = datetime.now().isoformat()
            
            # 結果がある場合
            if result is not None:
                update_data['result'] = json.dumps(result)
            
            # エラーがある場合
            if error is not None:
                update_data['error'] = error
            
            # 処理ログがある場合
            if processing_logs is not None:
                update_data['processing_logs'] = json.dumps(processing_logs)
            
            # データを更新
            result = self.supabase.table('search_tasks').update(update_data).eq('id', task_id).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error updating search task {task_id}: {result.error}")
                raise Exception(f"Error updating search task {task_id}: {result.error}")
            
            logger.info(f"Updated search task {task_id} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Error updating search task {task_id}: {e}")
            raise
    
    def add_processing_log(self, task_id: str, step: str, status: str, 
                          message: Optional[str] = None, 
                          platform: Optional[str] = None,
                          count: Optional[int] = None) -> None:
        """
        処理ログを追加する
        
        Args:
            task_id: タスクID
            step: 処理ステップ
            status: ステップのステータス（started, completed, failed）
            message: メッセージ（オプション）
            platform: プラットフォーム名（オプション）
            count: 結果数（オプション）
        """
        try:
            # 現在のタスク情報を取得
            task = self.get_task(task_id)
            if not task:
                return
            
            # 既存の処理ログを取得
            existing_logs = task.get('processing_logs', [])
            if isinstance(existing_logs, str):
                existing_logs = json.loads(existing_logs)
            elif existing_logs is None:
                existing_logs = []
            
            # 新しいログエントリを作成
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'step': step,
                'status': status,
                'message': message,
                'platform': platform,
                'count': count
            }
            
            # ログを追加
            existing_logs.append(log_entry)
            
            # データベースを更新
            update_data = {
                'processing_logs': json.dumps(existing_logs),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('search_tasks').update(update_data).eq('id', task_id).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error adding processing log to task {task_id}: {result.error}")
                raise Exception(f"Error adding processing log to task {task_id}: {result.error}")
            
            logger.info(f"Added processing log to task {task_id}: {step} - {status}")
            
        except Exception as e:
            logger.error(f"Error adding processing log to task {task_id}: {e}")
            raise
    
    def list_tasks(self, limit: int = 50, offset: int = 0, 
                  status: Optional[Union[TaskStatus, List[TaskStatus]]] = None) -> List[Dict[str, Any]]:
        """
        タスクのリストを取得する
        
        Args:
            limit: 取得する最大件数
            offset: オフセット（ページネーション用）
            status: フィルタするステータス（オプション）
            
        Returns:
            List[Dict[str, Any]]: タスクのリスト
        """
        try:
            # クエリを構築
            query = self.supabase.table('search_tasks').select('*').order('created_at', desc=True).limit(limit).offset(offset)
            
            # ステータスでフィルタリング
            if status:
                if isinstance(status, list):
                    status_values = [s.value for s in status]
                    query = query.in_('status', status_values)
                else:
                    query = query.eq('status', status.value)
            
            # クエリを実行
            result = query.execute()
            
            tasks = result.data or []
            
            # JSONBフィールドをパース
            for task in tasks:
                if task.get('search_params'):
                    if isinstance(task['search_params'], str):
                        task['search_params'] = json.loads(task['search_params'])
                
                if task.get('result'):
                    if isinstance(task['result'], str):
                        task['result'] = json.loads(task['result'])
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error listing search tasks: {e}")
            raise
    
    def cancel_task(self, task_id: str) -> bool:
        """
        タスクをキャンセルする
        
        Args:
            task_id: キャンセルするタスクのID
            
        Returns:
            bool: キャンセルに成功した場合はTrue
        """
        try:
            # 現在のタスク情報を取得
            task = self.get_task(task_id)
            if not task:
                return False
            
            # PENDINGまたはRUNNINGの場合のみキャンセル可能
            if task['status'] not in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
                return False
            
            # ステータスを更新
            self.update_task_status(
                task_id, 
                TaskStatus.CANCELLED, 
                error="Task cancelled by user"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling search task {task_id}: {e}")
            raise
    
    def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        実行待ちのタスクを取得する
        
        Args:
            limit: 取得する最大件数
            
        Returns:
            List[Dict[str, Any]]: 実行待ちタスクのリスト
        """
        return self.list_tasks(limit=limit, status=TaskStatus.PENDING)
    
    def count_running_tasks(self) -> int:
        """
        実行中のタスク数を取得する
        
        Returns:
            int: 実行中のタスク数
        """
        try:
            result = self.supabase.table('search_tasks').select('id', count='exact').eq('status', TaskStatus.RUNNING.value).execute()
            
            # count結果を取得
            count = result.count if hasattr(result, 'count') else 0
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting running tasks: {e}")
            raise
    
    def save_search_results(self, task_id: str, search_results: Dict[str, Any]) -> None:
        """
        検索結果をsearch_resultsテーブルに保存する
        
        Args:
            task_id: タスクID
            search_results: 検索結果データ
        """
        try:
            # 既存の検索結果を削除（重複を避けるため）
            self.supabase.table('search_results').delete().eq('task_id', task_id).execute()
            
            # 統合結果から個別のアイテムを取得
            integrated_results = search_results.get('integrated_results', {})
            items = integrated_results.get('items', [])
            
            if not items:
                logger.info(f"No search results to save for task {task_id}")
                return
            
            # 各アイテムをsearch_resultsテーブルに保存
            results_to_insert = []
            
            for item in items:
                # 価格情報を処理
                item_price = 0
                shipping_cost = 0
                total_price = 0
                
                if isinstance(item.get('price'), dict):
                    # Discogsの価格形式
                    item_price = item['price'].get('value', 0)
                    total_price = item_price
                elif isinstance(item.get('price'), (int, float)):
                    # 数値の価格
                    item_price = item['price']
                    total_price = item_price
                
                # 送料が別途ある場合
                if item.get('shipping_cost'):
                    shipping_cost = item['shipping_cost']
                    total_price = item_price + shipping_cost
                
                # total_priceが直接指定されている場合
                if item.get('total_price'):
                    total_price = item['total_price']
                
                # 検索結果データを構築（必須カラムを含む）
                result_data = {
                    'task_id': task_id,
                    'platform': item.get('platform', 'unknown'),
                    'item_title': item.get('item_title', item.get('title', 'Unknown Item')),
                    'item_url': item.get('item_url', item.get('url', '')),
                    'item_image_url': item.get('item_image_url', item.get('image_url', '')),
                    'item_condition': item.get('item_condition', item.get('condition', '')),
                    'base_price': item_price,
                    'shipping_fee': shipping_cost,
                    'created_at': datetime.now().isoformat()
                }
                
                results_to_insert.append(result_data)
            
            # バッチで挿入
            if results_to_insert:
                result = self.supabase.table('search_results').insert(results_to_insert).execute()
                
                if hasattr(result, 'error') and result.error:
                    logger.error(f"Error saving search results for task {task_id}: {result.error}")
                    raise Exception(f"Error saving search results for task {task_id}: {result.error}")
                
                logger.info(f"Saved {len(results_to_insert)} search results for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error saving search results for task {task_id}: {e}")
            raise

    def delete_old_tasks(self, days: int = 30) -> int:
        """
        古いタスクを削除する
        
        Args:
            days: 何日前より古いタスクを削除するか
            
        Returns:
            int: 削除されたタスク数
        """
        try:
            # 現在時刻からdays日前の日時を計算
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 古いタスクを削除
            result = self.supabase.table('search_tasks').delete().lt('created_at', cutoff_date).execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info(f"Deleted {deleted_count} old search tasks")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting old tasks: {e}")
            raise
