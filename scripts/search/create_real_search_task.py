#!/usr/bin/env python3
"""
実際の検索タスクを作成して実行するスクリプト
"""

import os
import sys
import json
import uuid
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.supabase_client import get_supabase_client
from src.jan.jan_lookup import lookup_jan_code

def create_search_task(jan_code):
    """新しい検索タスクを作成"""
    print(f"=== JANコード {jan_code} の検索タスクを作成 ===")
    
    try:
        # JANコードから商品名を取得
        product_name = lookup_jan_code(jan_code)
        if not product_name:
            print(f"JANコード {jan_code} の商品名を取得できませんでした")
            return None
        
        print(f"商品名: {product_name}")
        
        supabase = get_supabase_client()
        
        # タスクデータを準備
        task_id = str(uuid.uuid4())
        task_data = {
            'id': task_id,
            'name': f'JANコード検索: {product_name}',
            'status': 'pending',
            'search_params': {
                'jan_code': jan_code,
                'product_name': product_name,
                'platforms': ['mercari']
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # タスクを作成
        response = supabase.table('search_tasks').insert(task_data).execute()
        
        if response.data:
            print(f"✅ 検索タスクを作成しました: {task_id}")
            return task_id
        else:
            print("❌ 検索タスクの作成に失敗しました")
            return None
            
    except Exception as e:
        print(f"エラー: {e}")
        return None

def run_search_task(task_id):
    """検索タスクを実行"""
    print(f"\n=== タスク {task_id} を実行 ===")
    
    try:
        supabase = get_supabase_client()
        
        # タスクを取得
        response = supabase.table('search_tasks').select('*').eq('id', task_id).single().execute()
        
        if not response.data:
            print("タスクが見つかりません")
            return False
        
        task = response.data
        jan_code = task['search_params']['jan_code']
        product_name = task['search_params']['product_name']
        
        print(f"JANコード: {jan_code}")
        print(f"商品名: {product_name}")
        
        # タスクステータスを実行中に更新
        supabase.table('search_tasks').update({
            'status': 'running',
            'updated_at': datetime.now().isoformat()
        }).eq('id', task_id).execute()
        
        # メルカリ検索を実行
        from src.collectors.mercari import MercariCollector
        
        collector = MercariCollector()
        print("メルカリ検索を開始...")
        
        # 検索を実行
        results = collector.search_by_jan_code(jan_code, product_name)
        
        if results:
            print(f"✅ {len(results)}件の検索結果を取得しました")
            
            # 検索結果をsearch_resultsテーブルに保存
            for result in results:
                result_data = {
                    'task_id': task_id,
                    'platform': 'mercari',
                    'item_title': result.get('title', ''),
                    'item_url': result.get('url', ''),
                    'item_image_url': result.get('image_url', ''),
                    'item_condition': result.get('condition', ''),
                    'base_price': result.get('price', 0),
                    'shipping_fee': result.get('shipping_cost', 0),
                    'total_price': result.get('total_price', result.get('price', 0)),
                    'status': result.get('status', 'active'),
                    'created_at': datetime.now().isoformat()
                }
                
                supabase.table('search_results').insert(result_data).execute()
            
            # タスクを完了に更新
            supabase.table('search_tasks').update({
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).eq('id', task_id).execute()
            
            print(f"✅ タスクが完了しました")
            return True
        else:
            print("❌ 検索結果が取得できませんでした")
            
            # タスクを失敗に更新
            supabase.table('search_tasks').update({
                'status': 'failed',
                'error_message': '検索結果が取得できませんでした',
                'updated_at': datetime.now().isoformat()
            }).eq('id', task_id).execute()
            
            return False
            
    except Exception as e:
        print(f"エラー: {e}")
        
        # タスクを失敗に更新
        try:
            supabase = get_supabase_client()
            supabase.table('search_tasks').update({
                'status': 'failed',
                'error_message': str(e),
                'updated_at': datetime.now().isoformat()
            }).eq('id', task_id).execute()
        except:
            pass
        
        return False

def main():
    """メイン関数"""
    print("実際の検索タスク作成・実行スクリプト")
    print(f"実行時刻: {datetime.now()}")
    print()
    
    # JANコードを指定（サントリー 緑茶 伊右衛門 600ml ペット）
    jan_code = "4901777300446"
    
    # 1. 検索タスクを作成
    task_id = create_search_task(jan_code)
    
    if task_id:
        # 2. 検索タスクを実行
        success = run_search_task(task_id)
        
        if success:
            print(f"\n✅ 検索タスク {task_id} が正常に完了しました")
            print("WebUIで結果を確認してください")
        else:
            print(f"\n❌ 検索タスク {task_id} の実行に失敗しました")
    else:
        print("検索タスクの作成に失敗しました")

if __name__ == "__main__":
    main()
