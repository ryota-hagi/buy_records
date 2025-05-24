#!/usr/bin/env python
"""
Mercariデータ取得スクリプト
指定したキーワードのメルカリ商品情報を取得し、JSONファイルに保存します。
"""

import sys
import os
import argparse
from typing import List
import json
import time
from tqdm import tqdm

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.mercari import MercariClient
from src.utils.config import get_config

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

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='Fetch Mercari data and store in JSON')
    parser.add_argument('--file', type=str, help='Path to file containing search keywords')
    parser.add_argument('--output', type=str, default='mercari_data.json', help='Output JSON file path')
    parser.add_argument('--batch-size', type=int, default=1, help='Number of keywords to process in one batch')
    args = parser.parse_args()
    
    # キーワードを読み込む
    keywords = load_keywords(args.file)
    batch_size = args.batch_size
    
    print(f"Fetching data for {len(keywords)} Mercari search keywords...")
    
    # Mercariクライアントを初期化
    mercari_client = MercariClient()
    
    # データ取得
    all_results = []
    for i in tqdm(range(0, len(keywords), batch_size)):
        batch = keywords[i:i+batch_size]
        for keyword in batch:
            try:
                keyword_results = mercari_client.get_complete_data(keyword)
                all_results.extend(keyword_results)
                # APIレート制限対応
                time.sleep(float(get_config("MERCARI_REQUEST_DELAY", "2.0")))
            except Exception as e:
                print(f"Error processing keyword '{keyword}': {str(e)}")
    
    # 結果をJSONファイルに保存
    output_file = args.output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"Data saved to {output_file}")
    print(f"Total records: {len(all_results)}")
    
    # 次のステップの説明
    print("\nTo save this data to Supabase using MCP:")
    print("1. Start the Supabase MCP server:")
    print("   npx -y @supabase/mcp-server-supabase@latest --access-token YOUR_SUPABASE_ACCESS_TOKEN")
    print("2. Create the mercari_data table using MCP tools")
    print("   - Use the SQL in scripts/create_mercari_table.sql")
    print("3. Insert the data using SQL queries via MCP")
    
    # Discogsデータとの連携例
    print("\nTo integrate with Discogs data:")
    print("1. Extract artist and title from Discogs data")
    print("2. Use them as search keywords for Mercari")
    print("   python scripts/fetch_mercari.py --file discogs_keywords.json --output mercari_data.json")
    print("3. Compare prices between platforms")

if __name__ == "__main__":
    main()
