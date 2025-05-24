#!/usr/bin/env python3
"""
search_tasksテーブルにprocessing_logsカラムを追加するスクリプト
"""

import os
import sys
import logging
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.supabase_client import get_supabase_client

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_processing_logs_column():
    """search_tasksテーブルにprocessing_logsカラムを追加"""
    try:
        supabase = get_supabase_client()
        
        # カラムを追加するSQL
        sql = """
        ALTER TABLE search_tasks 
        ADD COLUMN IF NOT EXISTS processing_logs JSONB DEFAULT '[]'::jsonb;
        """
        
        # SQLを実行（Supabaseの場合はrpcを使用）
        try:
            # 直接SQLを実行する方法がない場合は、既存のテーブルを確認
            result = supabase.table('search_tasks').select('*').limit(1).execute()
            
            # カラムが存在するかチェック
            if result.data and len(result.data) > 0:
                first_row = result.data[0]
                if 'processing_logs' not in first_row:
                    logger.info("processing_logsカラムが存在しません。手動でSupabaseダッシュボードから追加してください。")
                    logger.info("以下のSQLを実行してください:")
                    logger.info(sql)
                else:
                    logger.info("processing_logsカラムは既に存在します。")
            else:
                logger.info("テーブルにデータがありません。カラムの存在確認ができません。")
                logger.info("以下のSQLを手動で実行してください:")
                logger.info(sql)
                
        except Exception as e:
            logger.error(f"カラム確認中にエラーが発生しました: {e}")
            logger.info("以下のSQLを手動でSupabaseダッシュボードから実行してください:")
            logger.info(sql)
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    add_processing_logs_column()
