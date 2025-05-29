"""
Supabaseクライアントユーティリティ

Supabaseとの接続を管理し、データベース操作を行うためのユーティリティ関数を提供します。
"""

import os
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from .config import get_config
from tenacity import retry, stop_after_attempt, wait_exponential

# グローバルクライアントインスタンス
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """
    Supabaseクライアントをシングルトンパターンで取得します。
    
    Returns:
        Client: Supabaseクライアントインスタンス
    
    Raises:
        ValueError: Supabase接続情報が設定されていない場合
    """
    global _supabase_client
    
    if _supabase_client is None:
        supabase_url = get_config("SUPABASE_URL")
        supabase_key = get_config("SUPABASE_SERVICE_KEY") or get_config("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase接続情報が設定されていません。.envファイルを確認してください。")
        
        _supabase_client = create_client(
            supabase_url, 
            supabase_key,
            options={
                'schema': 'public',
                'headers': {'x-my-custom-header': 'buy_records'},
                'autoRefreshToken': True,
                'persistSession': True,
                'detectSessionInUrl': False
            }
        )
    
    return _supabase_client

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def execute_with_retry(func, *args, **kwargs):
    """リトライ機能付きの実行関数"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # 接続エラーの場合、クライアントをリセット
        global _supabase_client
        _supabase_client = None
        raise e

def check_connection() -> bool:
    """データベース接続の健全性をチェック"""
    try:
        client = get_supabase_client()
        # 簡単なクエリを実行して接続を確認
        result = client.table('search_tasks').select('id').limit(1).execute()
        # 結果が返ってきたら成功
        return hasattr(result, 'data')
    except Exception as e:
        print(f"Connection check failed: {str(e)}")
        # 接続をリセット
        global _supabase_client
        _supabase_client = None
        return False

def insert_data(table_name: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    データをSupabaseテーブルに挿入します。
    
    Args:
        table_name: テーブル名
        data: 挿入するデータのリスト
        
    Returns:
        Dict[str, Any]: 挿入結果
    """
    if not data:
        return {"count": 0, "status": "success", "message": "データがありません"}
    
    try:
        client = get_supabase_client()
        result = client.table(table_name).insert(data).execute()
        return {
            "count": len(result.data),
            "status": "success",
            "message": f"{len(result.data)}件のデータを挿入しました"
        }
    except Exception as e:
        return {
            "count": 0,
            "status": "error",
            "message": f"データ挿入エラー: {str(e)}"
        }

def upsert_data(table_name: str, data: List[Dict[str, Any]], on_conflict: str) -> Dict[str, Any]:
    """
    データをSupabaseテーブルに挿入または更新します。
    
    Args:
        table_name: テーブル名
        data: 挿入または更新するデータのリスト
        on_conflict: 競合時に使用するカラム名
        
    Returns:
        Dict[str, Any]: 挿入または更新結果
    """
    if not data:
        return {"count": 0, "status": "success", "message": "データがありません"}
    
    try:
        client = get_supabase_client()
        result = client.table(table_name).upsert(data, on_conflict=on_conflict).execute()
        return {
            "count": len(result.data),
            "status": "success",
            "message": f"{len(result.data)}件のデータを挿入または更新しました"
        }
    except Exception as e:
        return {
            "count": 0,
            "status": "error",
            "message": f"データ挿入または更新エラー: {str(e)}"
        }

def get_existing_ids(table_name: str, id_column: str, search_term_column: Optional[str] = None, search_term: Optional[str] = None) -> List[str]:
    """
    既存のIDリストを取得します。
    
    Args:
        table_name: テーブル名
        id_column: ID列名
        search_term_column: 検索キーワード列名（省略可）
        search_term: 検索キーワード（省略可）
        
    Returns:
        List[str]: 既存のIDリスト
    """
    try:
        client = get_supabase_client()
        query = client.table(table_name).select(id_column)
        
        if search_term_column and search_term:
            query = query.eq(search_term_column, search_term)
            
        result = query.execute()
        return [item[id_column] for item in result.data]
    except Exception as e:
        print(f"既存ID取得エラー: {str(e)}")
        return []

def filter_new_items(data: List[Dict[str, Any]], existing_ids: List[str], id_key: str = "item_id") -> List[Dict[str, Any]]:
    """
    新しいアイテムのみをフィルタリングします。
    
    Args:
        data: フィルタリングするデータのリスト
        existing_ids: 既存のIDリスト
        id_key: データ内のID項目のキー名
        
    Returns:
        List[Dict[str, Any]]: 新しいアイテムのリスト
    """
    return [item for item in data if item.get(id_key) not in existing_ids]

def create_table_if_not_exists(sql_file_path: str) -> bool:
    """
    SQLファイルを使用してテーブルを作成します（存在しない場合）。
    
    Args:
        sql_file_path: SQLファイルのパス
        
    Returns:
        bool: テーブル作成が成功したかどうか
    """
    try:
        # SQLファイルを読み込む
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Supabaseクライアントを取得
        client = get_supabase_client()
        
        # SQLを複数のステートメントに分割
        # 空白行と空のステートメントを除去
        sql_statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
        
        # 各SQLステートメントを実行
        for stmt in sql_statements:
            try:
                # Supabaseの新しいAPIを使用してSQLを実行
                # 注意: これはSupabaseのPostgREST APIを使用しており、
                # 直接SQLを実行するわけではありません
                result = client.rpc('execute_sql', {'query': stmt}).execute()
                
                # 実行結果を確認
                if hasattr(result, 'error') and result.error:
                    print(f"SQLステートメント実行エラー: {result.error}")
                    
                    # テーブルが既に存在する場合は成功とみなす
                    if "already exists" in str(result.error):
                        print("テーブルは既に存在します")
                        continue
                    
                    # その他のエラーの場合は失敗
                    return False
            except Exception as e:
                # Supabaseの新しいAPIでエラーが発生した場合、
                # 従来のREST APIを使用して試行
                try:
                    import requests
                    
                    # Supabase REST APIを使用してSQLを実行
                    supabase_url = get_config("SUPABASE_URL")
                    supabase_key = get_config("SUPABASE_SERVICE_KEY")
                    
                    url = f"{supabase_url}/rest/v1/rpc/execute_sql"
                    headers = {
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "query": stmt
                    }
                    
                    response = requests.post(url, headers=headers, json=data)
                    
                    if response.status_code != 200:
                        print(f"REST API実行エラー: {response.status_code} {response.text}")
                        
                        # テーブルが既に存在する場合は成功とみなす
                        if "already exists" in response.text:
                            print("テーブルは既に存在します")
                            continue
                        
                        # その他のエラーの場合は失敗
                        return False
                except Exception as rest_error:
                    print(f"REST API実行エラー: {str(rest_error)}")
                    return False
        
        print("テーブル作成に成功しました")
        return True
    except Exception as e:
        print(f"テーブル作成エラー: {str(e)}")
        return False
