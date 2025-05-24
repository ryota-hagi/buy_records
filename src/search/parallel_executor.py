import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional, Tuple

from src.search.task_manager import SearchTaskManager, TaskStatus

logger = logging.getLogger(__name__)

class ParallelTaskExecutor:
    """複数の検索タスクを並列に実行するクラス"""
    
    def __init__(self, max_workers: int = 4, max_running_tasks: int = 10):
        """
        初期化
        
        Args:
            max_workers: 同時に実行するワーカー数
            max_running_tasks: 同時に実行できるタスクの最大数
        """
        self.max_workers = max_workers
        self.max_running_tasks = max_running_tasks
        self.task_manager = SearchTaskManager()
        self.executor = None
        self.running = False
    
    def start(self) -> None:
        """並列処理エンジンを開始する"""
        if self.running:
            logger.warning("Parallel executor is already running")
            return
            
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        logger.info(f"Started parallel executor with {self.max_workers} workers")
    
    def stop(self) -> None:
        """並列処理エンジンを停止する"""
        if not self.running:
            logger.warning("Parallel executor is not running")
            return
            
        self.running = False
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
        logger.info("Stopped parallel executor")
    
    def execute_task(self, task_id: str, executor_func: Callable[[Dict[str, Any], Any, str], Dict[str, Any]]) -> None:
        """
        タスクを実行する
        
        Args:
            task_id: 実行するタスクのID
            executor_func: タスクを実行する関数。search_params, task_manager, task_idを引数に取り、結果を返す必要がある
        """
        if not self.running:
            logger.error("Cannot execute task: parallel executor is not running")
            return
            
        # タスク情報を取得
        task = self.task_manager.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
            
        # タスクがPENDINGでない場合は実行しない
        if task['status'] != TaskStatus.PENDING.value:
            logger.warning(f"Cannot execute task {task_id}: status is {task['status']}")
            return
            
        # タスクのステータスを更新
        self.task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        
        try:
            # タスクを実行
            search_params = task['search_params']
            
            # 実行時間を計測
            start_time = time.time()
            
            # 実行関数を呼び出し（task_managerとtask_idを渡す）
            result = executor_func(search_params, self.task_manager, task_id)
            
            execution_time = time.time() - start_time
            
            # 結果に実行時間を追加
            if isinstance(result, dict):
                result['execution_time'] = execution_time
            
            # 検索結果をsearch_resultsテーブルに保存
            try:
                if isinstance(result, dict) and result.get('integrated_results'):
                    self.task_manager.save_search_results(task_id, result)
                    logger.info(f"Saved search results for task {task_id}")
                else:
                    logger.warning(f"No search results to save for task {task_id}")
            except Exception as save_error:
                logger.error(f"Error saving search results for task {task_id}: {save_error}")
                # 保存エラーは致命的ではないので、タスクは完了として扱う
            
            # タスクのステータスを更新
            self.task_manager.update_task_status(
                task_id, 
                TaskStatus.COMPLETED, 
                result=result
            )
            
            logger.info(f"Task {task_id} completed in {execution_time:.2f} seconds")
            
        except Exception as e:
            error_msg = f"Error executing task {task_id}: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            
            # タスクのステータスを更新
            self.task_manager.update_task_status(
                task_id, 
                TaskStatus.FAILED, 
                error=str(e)
            )
    
    def submit_task(self, task_id: str, executor_func: Callable[[Dict[str, Any], Any, str], Dict[str, Any]]) -> None:
        """
        タスクを実行キューに追加する
        
        Args:
            task_id: 実行するタスクのID
            executor_func: タスクを実行する関数
        """
        if not self.running:
            logger.error("Cannot submit task: parallel executor is not running")
            return
            
        if not self.executor:
            logger.error("Cannot submit task: executor is not initialized")
            return
            
        # 実行中のタスク数を確認
        running_count = self.task_manager.count_running_tasks()
        if running_count >= self.max_running_tasks:
            logger.warning(f"Cannot submit task: maximum number of running tasks ({self.max_running_tasks}) reached")
            return
            
        # タスクを実行キューに追加
        self.executor.submit(self.execute_task, task_id, executor_func)
        logger.info(f"Submitted task {task_id} to execution queue")
    
    def process_pending_tasks(self, executor_func: Callable[[Dict[str, Any], Any, str], Dict[str, Any]], 
                             batch_size: int = 5) -> int:
        """
        実行待ちのタスクを処理する
        
        Args:
            executor_func: タスクを実行する関数
            batch_size: 一度に処理するタスク数
            
        Returns:
            int: 処理されたタスク数
        """
        if not self.running:
            logger.error("Cannot process pending tasks: parallel executor is not running")
            return 0
            
        # 実行中のタスク数を確認
        running_count = self.task_manager.count_running_tasks()
        available_slots = self.max_running_tasks - running_count
        
        if available_slots <= 0:
            logger.info("No available slots for pending tasks")
            return 0
            
        # 実行待ちのタスクを取得
        pending_tasks = self.task_manager.get_pending_tasks(limit=min(batch_size, available_slots))
        
        if not pending_tasks:
            logger.info("No pending tasks found")
            return 0
            
        # タスクを実行キューに追加
        for task in pending_tasks:
            self.submit_task(task['id'], executor_func)
            
        return len(pending_tasks)
    
    def execute_search_tasks(self, search_executor: Callable[[Dict[str, Any], Any, str], Dict[str, Any]], 
                            interval: int = 5, max_iterations: Optional[int] = None) -> None:
        """
        検索タスクを定期的に処理する
        
        Args:
            search_executor: 検索を実行する関数
            interval: チェック間隔（秒）
            max_iterations: 最大イテレーション数（Noneの場合は無限ループ）
        """
        if not self.running:
            self.start()
            
        iteration = 0
        
        try:
            while self.running:
                if max_iterations is not None and iteration >= max_iterations:
                    break
                    
                processed = self.process_pending_tasks(search_executor)
                logger.info(f"Processed {processed} pending tasks")
                
                iteration += 1
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping executor")
            self.stop()
        except Exception as e:
            logger.error(f"Error in execute_search_tasks: {e}")
            self.stop()
            raise
