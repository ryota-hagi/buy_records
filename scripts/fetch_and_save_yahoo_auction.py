"""
Yahoo!オークションのデータを取得し、Supabaseに保存するスクリプト
"""

import json
import os
import sys
import time
from typing import List, Dict, Any
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.yahoo_auction import YahooAuctionClient
from src.utils.supabase_client import get_supabase_client, create_table_if_not_exists, upsert_data, get_existing_ids, filter_new_items
from src.utils.config import get_config

def fetch_and_save_yahoo_auction_data(keywords: List[str] = None, limit: int = 10) -> None:
    """
    Yahoo!オークションのデータを取得し、Supabaseに保存します。
    
    Args:
        keywords: 検索キーワードのリスト（指定がない場合はファイルから読み込み）
        limit: 各キーワードごとに取得する結果の最大数
    """
    try:
        # テーブルはすでに作成済みと仮定
        print("Yahoo!オークションデータ取得を開始します...")
        
        # キーワードの読み込み
        if not keywords:
            try:
                with open("yahoo_auction_keywords.json", "r", encoding="utf-8") as f:
                    keywords = json.load(f)
            except FileNotFoundError:
                print("キーワードファイルが見つかりません。")
                return
        
        # Yahoo!オークションクライアントの初期化
        client = YahooAuctionClient()
        
        # バッチサイズの設定
        batch_size = int(get_config("BATCH_SIZE", "10"))
        
        # 既存のアイテムIDを取得
        existing_ids = get_existing_ids("yahoo_auction_items", "item_id")
        print(f"既存のアイテム数: {len(existing_ids)}")
        
        # 結果を格納するリスト
        all_items = []
        
        # 各キーワードで検索
        for i, keyword in enumerate(keywords):
            print(f"[{i+1}/{len(keywords)}] '{keyword}' の検索中...")
            
            try:
                # データ取得
                items = client.get_complete_data(keyword, limit, limit)
                
                # 新しいアイテムのみをフィルタリング
                new_items = filter_new_items(items, existing_ids)
                
                print(f"  取得: {len(items)}件, 新規: {len(new_items)}件")
                
                # 結果を追加
                all_items.extend(new_items)
                
                # 既存IDリストを更新
                existing_ids.extend([item["item_id"] for item in new_items])
                
                # バッチサイズに達したらデータを保存
                if len(all_items) >= batch_size:
                    save_result = upsert_data("yahoo_auction_items", all_items, "item_id")
                    print(f"  保存結果: {save_result}")
                    all_items = []
                
                # APIレート制限対応
                time.sleep(float(get_config("REQUEST_DELAY", "1.0")))
                
            except Exception as e:
                print(f"  エラー: {str(e)}")
                continue
        
        # 残りのデータを保存
        if all_items:
            save_result = upsert_data("yahoo_auction_items", all_items, "item_id")
            print(f"最終保存結果: {save_result}")
        
        print("処理が完了しました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    # コマンドライン引数からキーワードを取得（オプション）
    import argparse
    parser = argparse.ArgumentParser(description="Yahoo!オークションのデータを取得し、Supabaseに保存します。")
    parser.add_argument("--keywords", nargs="+", help="検索キーワードのリスト")
    parser.add_argument("--limit", type=int, default=10, help="各キーワードごとに取得する結果の最大数")
    args = parser.parse_args()
    
    fetch_and_save_yahoo_auction_data(args.keywords, args.limit)
