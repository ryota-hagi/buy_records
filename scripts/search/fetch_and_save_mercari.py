#!/usr/bin/env python
"""
メルカリデータの取得と保存を自動化するスクリプト
指定したキーワードでメルカリ内を検索し、出品中と売り切れ済みのアイテムを取得して、
Supabaseデータベースに保存します。
"""

import sys
import os
import argparse
import json
import time
from typing import List, Dict, Any
from tqdm import tqdm

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.mercari import MercariClient
from src.utils.config import get_config
from src.utils.supabase_client import (
    create_table_if_not_exists, 
    get_existing_ids, 
    filter_new_items, 
    insert_data, 
    upsert_data
)

def load_keywords(file_path: str = None) -> List[str]:
    """
    検索キーワードのリストを読み込みます。
    
    Args:
        file_path: キーワードを含むファイルのパス（省略可）
        
    Returns:
        List[str]: キーワードのリスト
    """
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return data
            except json.JSONDecodeError:
                # 1行1キーワードの形式と仮定
                return [line.strip() for line in f if line.strip()]
    
    # デフォルトのテスト用キーワード
    return ["マイルス・デイビス カインド・オブ・ブルー レコード", 
            "ビートルズ アビーロード レコード", 
            "マイケル・ジャクソン スリラー レコード"]

def fetch_mercari_data(keywords: List[str], batch_size: int = 1, limit: int = 5) -> List[Dict[str, Any]]:
    """
    メルカリデータを取得します。
    
    Args:
        keywords: 検索キーワードのリスト
        batch_size: バッチサイズ
        limit: 各カテゴリ（出品中・売り切れ済み）ごとに取得する結果の最大数
        
    Returns:
        List[Dict[str, Any]]: メルカリデータのリスト
    """
    # Mercariクライアントを初期化
    mercari_client = MercariClient()
    
    # データ取得
    all_results = []
    for i in tqdm(range(0, len(keywords), batch_size)):
        batch = keywords[i:i+batch_size]
        for keyword in batch:
            try:
                keyword_results = mercari_client.get_complete_data(keyword, limit)
                all_results.extend(keyword_results)
                # APIレート制限対応
                time.sleep(float(get_config("MERCARI_REQUEST_DELAY", "2.0")))
            except Exception as e:
                print(f"Error processing keyword '{keyword}': {str(e)}")
    
    return all_results

def save_to_supabase(data: List[Dict[str, Any]], update_existing: bool = False) -> Dict[str, Any]:
    """
    メルカリデータをSupabaseに保存します。
    
    Args:
        data: メルカリデータのリスト
        update_existing: 既存のデータを更新するかどうか
        
    Returns:
        Dict[str, Any]: 保存結果
    """
    if not data:
        return {"count": 0, "status": "success", "message": "データがありません"}
    
    table_name = "mercari_data"
    
    try:
        # バッチサイズ
        batch_size = 50
        total_records = len(data)
        saved_count = 0
        
        # 既存のIDを取得（差分更新のため）
        if not update_existing:
            print("既存のIDを取得中...")
            existing_ids = get_existing_ids(table_name, "item_id")
            print(f"既存のID数: {len(existing_ids)}")
            
            # 新しいアイテムのみをフィルタリング
            new_items = filter_new_items(data, existing_ids)
            print(f"新しいアイテム数: {len(new_items)}")
            
            if not new_items:
                return {"count": 0, "status": "success", "message": "新しいデータがありません"}
            
            data = new_items
            total_records = len(data)
        
        results = []
        for i in range(0, total_records, batch_size):
            batch = data[i:i+batch_size]
            batch_count = len(batch)
            
            print(f"バッチ {i//batch_size + 1} のインポート中... ({batch_count} レコード)")
            
            # データをインポート
            if update_existing:
                result = upsert_data(table_name, batch, "item_id")
            else:
                result = insert_data(table_name, batch)
            
            results.append(result)
            saved_count += result.get("count", 0)
            
            print(f"インポート進捗: {saved_count}/{total_records} レコード")
            print(f"結果: {result.get('message')}")
            
            # APIレート制限対応
            time.sleep(1)
        
        print(f"合計 {saved_count} レコードをインポートしました")
        
        return {
            "count": saved_count,
            "status": "success",
            "message": f"合計 {saved_count} レコードをインポートしました",
            "details": results
        }
    except Exception as e:
        print(f"データインポートエラー: {str(e)}")
        return {
            "count": 0,
            "status": "error",
            "message": f"データインポートエラー: {str(e)}"
        }

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='Fetch Mercari data and save to Supabase')
    parser.add_argument('--file', type=str, help='Path to file containing search keywords')
    parser.add_argument('--keyword', type=str, help='Single search keyword')
    parser.add_argument('--batch-size', type=int, default=1, help='Number of keywords to process in one batch')
    parser.add_argument('--create-table', action='store_true', help='Create table before import')
    parser.add_argument('--update-existing', action='store_true', help='Update existing data')
    parser.add_argument('--output', type=str, help='Save fetched data to JSON file')
    parser.add_argument('--limit', type=int, default=5, help='Maximum number of items to fetch per keyword')
    args = parser.parse_args()
    
    # キーワードを読み込む
    if args.keyword:
        keywords = [args.keyword]
    else:
        keywords = load_keywords(args.file)
    
    batch_size = args.batch_size
    limit = args.limit
    
    print(f"Fetching data for {len(keywords)} Mercari search keywords (limit: {limit} items per keyword)...")
    
    # テーブル作成（オプション）
    if args.create_table:
        print("Creating mercari_data table...")
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_mercari_table.sql')
        if not create_table_if_not_exists(sql_file_path):
            print("テーブル作成に失敗しました。テーブルが既に存在するか確認してください。")
            print("テーブル作成なしで処理を続行します。")
    
    # メルカリデータを取得
    mercari_data = fetch_mercari_data(keywords, batch_size, limit)
    
    if not mercari_data:
        print("No data found")
        return
    
    print(f"Fetched {len(mercari_data)} records from Mercari")
    
    # データをJSONファイルに保存（オプション）
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(mercari_data, f, ensure_ascii=False, indent=2)
        print(f"Saved data to {args.output}")
    
    # データをSupabaseに保存
    print("Saving data to Supabase...")
    result = save_to_supabase(mercari_data, args.update_existing)
    
    if result["status"] == "success":
        print(f"Success: {result['message']}")
    else:
        print(f"Error: {result['message']}")

if __name__ == "__main__":
    main()
