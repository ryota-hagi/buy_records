#!/usr/bin/env python
"""
Supabaseに保存されているメルカリデータのURLを確認するスクリプト
"""

import sys
import os
import json
from typing import List, Dict, Any

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.supabase_client import get_supabase_client

def get_mercari_data():
    """
    Supabaseからメルカリデータを取得します。
    
    Returns:
        List[Dict[str, Any]]: メルカリデータのリスト
    """
    try:
        client = get_supabase_client()
        result = client.table("mercari_data").select("id, search_term, title, url").execute()
        return result.data
    except Exception as e:
        print(f"データ取得エラー: {str(e)}")
        return []

def check_urls(data: List[Dict[str, Any]]):
    """
    URLを確認します。
    
    Args:
        data: メルカリデータのリスト
        
    Returns:
        Dict[str, Any]: URL統計情報
    """
    total_records = len(data)
    empty_urls = []
    valid_urls = []
    
    for item in data:
        url = item.get("url", "")
        if not url:
            empty_urls.append(item)
        else:
            valid_urls.append(item)
    
    return {
        "total_records": total_records,
        "empty_urls": len(empty_urls),
        "valid_urls": len(valid_urls),
        "empty_url_percentage": round(len(empty_urls) / total_records * 100, 2) if total_records > 0 else 0,
        "sample_empty_urls": empty_urls[:5] if empty_urls else [],
        "sample_valid_urls": valid_urls[:5] if valid_urls else []
    }

def main():
    """メイン実行関数"""
    print("Supabaseからメルカリデータを取得中...")
    data = get_mercari_data()
    
    if not data:
        print("データが見つかりませんでした。")
        return
    
    print(f"合計 {len(data)} レコードを取得しました。")
    
    # URLを確認
    url_stats = check_urls(data)
    
    print(f"URL統計情報:")
    print(f"- 合計レコード数: {url_stats['total_records']}")
    print(f"- 空のURL数: {url_stats['empty_urls']}")
    print(f"- 有効なURL数: {url_stats['valid_urls']}")
    print(f"- 空のURLの割合: {url_stats['empty_url_percentage']}%")
    
    if url_stats['sample_empty_urls']:
        print("\n空のURLのサンプル:")
        for i, record in enumerate(url_stats['sample_empty_urls']):
            print(f"\n[サンプル {i+1}]")
            print(f"- id: {record.get('id')}")
            print(f"- search_term: {record.get('search_term')}")
            print(f"- title: {record.get('title')}")
            print(f"- url: {record.get('url')}")
    
    if url_stats['sample_valid_urls']:
        print("\n有効なURLのサンプル:")
        for i, record in enumerate(url_stats['sample_valid_urls']):
            print(f"\n[サンプル {i+1}]")
            print(f"- id: {record.get('id')}")
            print(f"- search_term: {record.get('search_term')}")
            print(f"- title: {record.get('title')}")
            print(f"- url: {record.get('url')}")

if __name__ == "__main__":
    main()
