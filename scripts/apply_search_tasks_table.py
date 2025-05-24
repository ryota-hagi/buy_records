#!/usr/bin/env python
"""
search_tasksテーブルをSupabaseに作成するスクリプト
"""

import os
import sys
import logging
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.supabase_client import create_table_if_not_exists

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """メイン関数"""
    try:
        # SQLファイルのパス
        sql_file_path = Path(__file__).parent / 'create_search_tasks_table.sql'
        
        # テーブルを作成
        logger.info("search_tasksテーブルを作成しています...")
        success = create_table_if_not_exists(str(sql_file_path))
        
        if success:
            logger.info("search_tasksテーブルが正常に作成されました")
            return 0
        else:
            logger.error("テーブル作成に失敗しました")
            return 1
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
