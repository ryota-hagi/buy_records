#!/usr/bin/env python
"""
継続的にタスクを処理するスクリプト
"""

import sys
import os
import time
import logging
import signal

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

# グローバル変数
running = True

def signal_handler(signum, frame):
    """シグナルハンドラー"""
    global running
    logger.info("Received shutdown signal")
    running = False

def process_tasks():
    """タスクを継続的に処理する"""
    global running
    
    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    task_manager = TaskManager()
    
    logger.info("Starting continuous task processing...")
    
    while running:
        try:
            # 待機中のタスクを取得
            pending_tasks = task_manager.get_pending_tasks(limit=1)
            
            if pending_tasks:
                task = pending_tasks[0]
                task_id = task['id']
                
                logger.info(f"Processing task: {task_id} - {task['name']}")
                
                # タスクを実行中に変更
                task_manager.update_task_status(task_id, 'running')
                
                # 開始ログを追加
                task_manager.add_processing_log(
                    task_id, 
                    'task_started', 
                    'started', 
                    'タスクの実行を開始しました'
                )
                
                # 検索実行
                search_executor = SearchExecutor(task_manager=task_manager, task_id=task_id)
                
                try:
                    result = search_executor.execute_search(task['search_params'])
                    
                    logger.info(f"Task {task_id} completed successfully")
                    task_manager.complete_task(task_id, result)
                    
                    # 完了ログを追加
                    task_manager.add_processing_log(
                        task_id, 
                        'task_completed', 
                        'completed', 
                        'タスクが正常に完了しました'
                    )
                    
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    task_manager.fail_task(task_id, str(e))
                    
                    # エラーログを追加
                    task_manager.add_processing_log(
                        task_id, 
                        'task_failed', 
                        'failed', 
                        f'タスクが失敗しました: {str(e)}'
                    )
            else:
                # 待機中のタスクがない場合は少し待機
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"Error in task processing loop: {e}")
            time.sleep(10)  # エラー時は少し長めに待機
    
    logger.info("Task processing stopped")

if __name__ == '__main__':
    process_tasks()
