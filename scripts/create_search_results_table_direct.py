#!/usr/bin/env python3
"""
検索結果テーブルを直接作成するスクリプト
"""

import os
import sys
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.supabase_client import get_supabase_client

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_search_results_table():
    """検索結果テーブルを作成する"""
    try:
        supabase = get_supabase_client()
        
        # SQLクエリを定義
        sql_query = """
        -- 検索結果テーブルを作成
        CREATE TABLE IF NOT EXISTS search_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id UUID NOT NULL REFERENCES search_tasks(id) ON DELETE CASCADE,
            platform VARCHAR(50) NOT NULL,
            title TEXT,
            artist TEXT,
            url TEXT,
            image_url TEXT,
            item_price DECIMAL(10,2),
            shipping_cost DECIMAL(10,2) DEFAULT 0,
            total_price DECIMAL(10,2) NOT NULL,
            condition TEXT,
            status VARCHAR(20) DEFAULT 'active',
            description TEXT,
            seller_name TEXT,
            location TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- インデックスを作成
        CREATE INDEX IF NOT EXISTS idx_search_results_task_id ON search_results(task_id);
        CREATE INDEX IF NOT EXISTS idx_search_results_platform ON search_results(platform);
        CREATE INDEX IF NOT EXISTS idx_search_results_total_price ON search_results(total_price);
        CREATE INDEX IF NOT EXISTS idx_search_results_created_at ON search_results(created_at);

        -- RLSを有効化
        ALTER TABLE search_results ENABLE ROW LEVEL SECURITY;

        -- 全てのユーザーが読み取り可能なポリシーを作成
        CREATE POLICY IF NOT EXISTS "Allow read access for all users" ON search_results
            FOR SELECT USING (true);

        -- 全てのユーザーが挿入可能なポリシーを作成
        CREATE POLICY IF NOT EXISTS "Allow insert access for all users" ON search_results
            FOR INSERT WITH CHECK (true);

        -- 全てのユーザーが更新可能なポリシーを作成
        CREATE POLICY IF NOT EXISTS "Allow update access for all users" ON search_results
            FOR UPDATE USING (true);

        -- 全てのユーザーが削除可能なポリシーを作成
        CREATE POLICY IF NOT EXISTS "Allow delete access for all users" ON search_results
            FOR DELETE USING (true);
        """
        
        logger.info("検索結果テーブルを作成しています...")
        
        # SQLを実行
        result = supabase.rpc('exec_sql', {'sql': sql_query}).execute()
        
        if result.data:
            logger.info("検索結果テーブルが正常に作成されました")
        else:
            logger.warning("テーブル作成の結果が不明です")
        
        # テーブルが作成されたか確認
        test_result = supabase.table('search_results').select('id').limit(1).execute()
        logger.info("検索結果テーブルの存在確認: 成功")
        
        return True
        
    except Exception as e:
        logger.error(f"検索結果テーブルの作成に失敗しました: {e}")
        
        # 代替方法: execute_sqlを使用
        try:
            logger.info("代替方法でテーブル作成を試行しています...")
            
            # 個別にSQLを実行
            sqls = [
                """
                CREATE TABLE IF NOT EXISTS search_results (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    task_id UUID NOT NULL,
                    platform VARCHAR(50) NOT NULL,
                    title TEXT,
                    artist TEXT,
                    url TEXT,
                    image_url TEXT,
                    item_price DECIMAL(10,2),
                    shipping_cost DECIMAL(10,2) DEFAULT 0,
                    total_price DECIMAL(10,2) NOT NULL,
                    condition TEXT,
                    status VARCHAR(20) DEFAULT 'active',
                    description TEXT,
                    seller_name TEXT,
                    location TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """,
                "CREATE INDEX IF NOT EXISTS idx_search_results_task_id ON search_results(task_id);",
                "CREATE INDEX IF NOT EXISTS idx_search_results_platform ON search_results(platform);",
                "CREATE INDEX IF NOT EXISTS idx_search_results_total_price ON search_results(total_price);",
                "CREATE INDEX IF NOT EXISTS idx_search_results_created_at ON search_results(created_at);",
                "ALTER TABLE search_results ENABLE ROW LEVEL SECURITY;",
            ]
            
            for sql in sqls:
                try:
                    result = supabase.rpc('exec_sql', {'sql': sql}).execute()
                    logger.info(f"SQL実行成功: {sql[:50]}...")
                except Exception as sql_error:
                    logger.warning(f"SQL実行失敗: {sql[:50]}... - {sql_error}")
            
            # テーブルが作成されたか確認
            test_result = supabase.table('search_results').select('id').limit(1).execute()
            logger.info("検索結果テーブルの存在確認: 成功")
            
            return True
            
        except Exception as alt_error:
            logger.error(f"代替方法でも失敗しました: {alt_error}")
            return False

if __name__ == "__main__":
    success = create_search_results_table()
    if success:
        print("検索結果テーブルの作成が完了しました")
        sys.exit(0)
    else:
        print("検索結果テーブルの作成に失敗しました")
        sys.exit(1)
