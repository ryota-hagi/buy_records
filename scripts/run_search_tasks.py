#!/usr/bin/env python
"""
検索タスクを実行するスクリプト

使用方法:
    python scripts/run_search_tasks.py [--max-workers N] [--max-running-tasks N] [--interval N] [--iterations N]

オプション:
    --max-workers N        同時に実行するワーカー数（デフォルト: 4）
    --max-running-tasks N  同時に実行できるタスクの最大数（デフォルト: 10）
    --interval N           タスクチェック間隔（秒）（デフォルト: 5）
    --iterations N         最大イテレーション数（デフォルト: 無限）
"""

import argparse
import logging
import sys
import os
import time
from typing import Dict, Any

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('search_tasks.log')
    ]
)

logger = logging.getLogger(__name__)

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.search.parallel_executor import ParallelTaskExecutor
from src.search.search_executor import SearchExecutor

def parse_args():
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(description='検索タスクを実行するスクリプト')
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=4,
        help='同時に実行するワーカー数（デフォルト: 4）'
    )
    
    parser.add_argument(
        '--max-running-tasks',
        type=int,
        default=10,
        help='同時に実行できるタスクの最大数（デフォルト: 10）'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='タスクチェック間隔（秒）（デフォルト: 5）'
    )
    
    parser.add_argument(
        '--iterations',
        type=int,
        default=None,
        help='最大イテレーション数（デフォルト: 無限）'
    )
    
    return parser.parse_args()

def execute_search(search_params: Dict[str, Any], task_manager=None, task_id: str = None) -> Dict[str, Any]:
    """
    検索を実行する関数
    
    Args:
        search_params: 検索パラメータ
        task_manager: タスクマネージャー（進捗ログ用）
        task_id: タスクID（進捗ログ用）
        
    Returns:
        Dict[str, Any]: 検索結果
    """
    search_executor = SearchExecutor(task_manager=task_manager, task_id=task_id)
    return search_executor.execute_search(search_params)

def main():
    """メイン関数"""
    args = parse_args()
    
    logger.info(f"Starting search task executor with max_workers={args.max_workers}, "
                f"max_running_tasks={args.max_running_tasks}, interval={args.interval}")
    
    # 並列処理エンジンを初期化
    executor = ParallelTaskExecutor(
        max_workers=args.max_workers,
        max_running_tasks=args.max_running_tasks
    )
    
    try:
        # 検索タスクを実行
        executor.execute_search_tasks(
            search_executor=execute_search,
            interval=args.interval,
            max_iterations=args.iterations
        )
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping executor")
        executor.stop()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        executor.stop()
        raise

if __name__ == '__main__':
    main()
