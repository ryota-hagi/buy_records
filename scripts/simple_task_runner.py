#!/usr/bin/env python
"""
シンプルなタスク実行スクリプト
"""

import sys
import os
import time
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.search.task_manager import TaskManager
    from src.search.search_executor import SearchExecutor
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

def run_single_task():
    """単一のタスクを実行する"""
    try:
        # タスクマネージャーを初期化
        logger.info("Initializing task manager...")
        task_manager = TaskManager()
        
        # 待機中のタスクを1つ取得
        logger.info("Getting pending tasks...")
        pending_tasks = task_manager.get_pending_tasks(limit=1)
        logger.info(f"Found {len(pending_tasks)} pending tasks")
        
        if not pending_tasks:
            logger.info("No pending tasks found")
            return
            
        task = pending_tasks[0]
        task_id = task['id']
        logger.info(f"Processing task: {task_id} - {task['name']}")
        
        # タスクを実行中に変更
        logger.info(f"Updating task {task_id} status to running...")
        task_manager.update_task_status(task_id, 'running')
        
        # 進捗ログを追加
        task_manager.add_processing_log(
            task_id, 
            'task_started', 
            'started', 
            'タスクの実行を開始しました'
        )
        
        # 検索実行
        logger.info(f"Starting search execution for task {task_id}...")
        search_executor = SearchExecutor(task_manager=task_manager, task_id=task_id)
        
        result = search_executor.execute_search(task['search_params'])
        
        logger.info(f"Search completed successfully for task {task_id}")
        task_manager.complete_task(task_id, result)
        
        # 完了ログを追加
        task_manager.add_processing_log(
            task_id, 
            'task_completed', 
            'completed', 
            'タスクが正常に完了しました'
        )
        
    except Exception as e:
        logger.error(f"Error processing task: {e}")
        if 'task_id' in locals():
            try:
                task_manager.fail_task(task_id, str(e))
                task_manager.add_processing_log(
                    task_id, 
                    'task_failed', 
                    'failed', 
                    f'タスクが失敗しました: {str(e)}'
                )
            except Exception as log_error:
                logger.error(f"Failed to log error: {log_error}")

def main():
    """メイン関数"""
    logger.info("Starting simple task runner...")
    
    try:
        run_single_task()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    
    logger.info("Task runner finished")

if __name__ == '__main__':
    main()
