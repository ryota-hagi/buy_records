#!/usr/bin/env python
"""
search_tasksテーブルをSupabaseに直接作成するスクリプト
"""

import os
import sys
import logging
import json
from datetime import datetime

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.supabase_client import get_supabase_client

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """メイン関数"""
    try:
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        logger.info("search_tasksテーブルを作成しています...")
        
        # テーブルが存在するか確認
        try:
            # テーブルからデータを取得してみる（テーブルが存在するか確認するため）
            supabase.table('search_tasks').select('id').limit(1).execute()
            logger.info("search_tasksテーブルは既に存在します")
            return 0
        except Exception as e:
            # テーブルが存在しない場合は作成する
            if "relation" in str(e) and "does not exist" in str(e):
                logger.info("search_tasksテーブルが存在しないため、作成します")
            else:
                # その他のエラーの場合はそのまま例外を投げる
                raise e
        
        # サンプルデータを作成（テーブル作成のテスト用）
        sample_task = {
            "name": "サンプル検索タスク",
            "status": "pending",
            "search_params": json.dumps({
                "query": "テスト",
                "platforms": ["discogs", "ebay"]
            }),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # テーブルにデータを挿入（テーブルが存在しない場合は自動的に作成される）
        result = supabase.table('search_tasks').insert(sample_task).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"テーブル作成中にエラーが発生しました: {result.error}")
            return 1
        
        logger.info("search_tasksテーブルが正常に作成されました")
        
        # サンプルデータを削除
        task_id = result.data[0]['id']
        supabase.table('search_tasks').delete().eq('id', task_id).execute()
        logger.info("サンプルデータを削除しました")
        
        return 0
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
