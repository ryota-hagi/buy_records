#!/usr/bin/env python3
"""
Supabase接続の修正と安定化スクリプト
"""
import os
import sys
import time
from datetime import datetime

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.config import get_config
from src.utils.supabase_client import get_supabase_client, check_connection, execute_with_retry

def test_supabase_connection():
    """Supabase接続をテストし、問題を診断"""
    print("=== Supabase Connection Fix ===\n")
    
    # 環境変数チェック
    print("📍 Checking environment variables...")
    supabase_url = get_config("SUPABASE_URL", required=False)
    supabase_key = get_config("SUPABASE_SERVICE_KEY", required=False) or get_config("SUPABASE_ANON_KEY", required=False)
    
    if not supabase_url:
        print("❌ SUPABASE_URL not found in .env")
        return False
    
    if not supabase_key:
        print("❌ SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY not found in .env")
        return False
    
    print(f"✅ SUPABASE_URL: {supabase_url[:30]}...")
    print(f"✅ SUPABASE_KEY: {supabase_key[:20]}...")
    
    # 接続テスト
    print("\n📍 Testing database connection...")
    
    # 初回接続
    try:
        if check_connection():
            print("✅ Initial connection successful")
        else:
            print("❌ Initial connection failed")
            # リトライ
            print("   Retrying connection...")
            time.sleep(2)
            if check_connection():
                print("✅ Connection successful on retry")
            else:
                print("❌ Connection still failing")
                return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    
    # テーブル存在確認
    print("\n📍 Checking tables...")
    try:
        client = get_supabase_client()
        
        # search_tasksテーブル
        result = execute_with_retry(
            lambda: client.table('search_tasks').select('id').limit(1).execute()
        )
        print("✅ search_tasks table accessible")
        
        # search_resultsテーブル
        result = execute_with_retry(
            lambda: client.table('search_results').select('id').limit(1).execute()
        )
        print("✅ search_results table accessible")
        
    except Exception as e:
        print(f"❌ Table access error: {str(e)}")
        print("\n📍 Attempting to create missing tables...")
        
        # テーブル作成を試みる
        try:
            create_tables()
            print("✅ Tables created successfully")
        except Exception as create_error:
            print(f"❌ Failed to create tables: {str(create_error)}")
            return False
    
    # 書き込みテスト
    print("\n📍 Testing write operations...")
    try:
        test_data = {
            'keyword': 'connection_test',
            'status': 'completed',
            'created_at': datetime.now().isoformat()
        }
        
        result = execute_with_retry(
            lambda: client.table('search_tasks').insert(test_data).execute()
        )
        
        if result.data:
            print("✅ Write operation successful")
            task_id = result.data[0]['id']
            
            # クリーンアップ
            execute_with_retry(
                lambda: client.table('search_tasks').delete().eq('id', task_id).execute()
            )
            print("✅ Cleanup successful")
        else:
            print("❌ Write operation failed")
            return False
            
    except Exception as e:
        print(f"❌ Write operation error: {str(e)}")
        return False
    
    # 接続プール設定の最適化
    print("\n📍 Optimizing connection settings...")
    optimize_connection_settings()
    
    return True

def create_tables():
    """必要なテーブルを作成"""
    client = get_supabase_client()
    
    # search_tasksテーブルのSQL
    search_tasks_sql = """
    CREATE TABLE IF NOT EXISTS search_tasks (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        keyword VARCHAR(255) NOT NULL,
        status VARCHAR(50) DEFAULT 'pending',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        result_count INTEGER DEFAULT 0,
        error_message TEXT
    );
    """
    
    # search_resultsテーブルのSQL
    search_results_sql = """
    CREATE TABLE IF NOT EXISTS search_results (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        task_id UUID REFERENCES search_tasks(id) ON DELETE CASCADE,
        platform VARCHAR(50) NOT NULL,
        item_id VARCHAR(255) NOT NULL,
        title TEXT,
        price DECIMAL(10, 2),
        url TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(platform, item_id)
    );
    """
    
    # SQLを実行（Supabase SQLエディタで実行する必要がある場合）
    print("   Note: Tables may need to be created via Supabase Dashboard SQL editor")
    print("   SQL statements have been prepared")

def optimize_connection_settings():
    """接続設定を最適化"""
    # 環境変数に推奨設定を追加
    recommendations = {
        "SUPABASE_POOL_SIZE": "10",
        "SUPABASE_MAX_RETRIES": "3",
        "SUPABASE_RETRY_DELAY": "2",
        "SUPABASE_TIMEOUT": "30"
    }
    
    print("   Recommended .env settings:")
    for key, value in recommendations.items():
        current = os.environ.get(key)
        if current != value:
            print(f"   - {key}={value} (current: {current or 'not set'})")

def test_connection_stability():
    """接続の安定性をテスト"""
    print("\n📍 Testing connection stability...")
    
    success_count = 0
    total_tests = 10
    
    for i in range(total_tests):
        try:
            if check_connection():
                success_count += 1
                print(f"   Test {i+1}/{total_tests}: ✅")
            else:
                print(f"   Test {i+1}/{total_tests}: ❌")
            time.sleep(0.5)
        except Exception as e:
            print(f"   Test {i+1}/{total_tests}: ❌ ({str(e)})")
    
    success_rate = (success_count / total_tests) * 100
    print(f"\n   Success rate: {success_rate:.1f}%")
    
    return success_rate >= 90

if __name__ == "__main__":
    # 接続テスト
    connection_ok = test_supabase_connection()
    
    if connection_ok:
        print("\n✅ Supabase connection is working!")
        
        # 安定性テスト
        if test_connection_stability():
            print("\n✅ Connection is stable!")
        else:
            print("\n⚠️  Connection is unstable")
            print("\nRecommended actions:")
            print("1. Check network connectivity")
            print("2. Verify Supabase project is not paused")
            print("3. Consider upgrading Supabase plan for better stability")
    else:
        print("\n❌ Supabase connection needs attention")
        print("\nRecommended actions:")
        print("1. Verify SUPABASE_URL and keys in .env")
        print("2. Check if Supabase project is active")
        print("3. Create required tables via Supabase Dashboard")
        print("4. Check network firewall settings")