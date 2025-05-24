"""
Discogsデータからヤフオク検索用のキーワードを生成するスクリプト
"""

import json
import os
import sys
from typing import List, Dict, Any

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.supabase_client import get_supabase_client

def generate_keywords() -> List[str]:
    """
    Discogsデータからヤフオク検索用のキーワードを生成します。
    
    Returns:
        List[str]: 検索キーワードのリスト
    """
    try:
        # Supabaseからデータを取得
        client = get_supabase_client()
        response = client.table("discogs_listings").select("title", "artist").execute()
        
        if not response.data:
            print("Discogsデータが見つかりません。")
            return []
        
        keywords = []
        for item in response.data:
            title = item.get("title", "")
            artist = item.get("artist", "")
            
            # 基本キーワード: アーティスト + タイトル
            if artist and title:
                keywords.append(f"{artist} {title}")
            
            # アーティストのみ
            if artist:
                keywords.append(artist)
            
            # タイトルのみ
            if title:
                keywords.append(title)
            
            # アーティスト + "レコード"
            if artist:
                keywords.append(f"{artist} レコード")
                keywords.append(f"{artist} LP")
                keywords.append(f"{artist} アナログ")
            
            # タイトル + "レコード"
            if title:
                keywords.append(f"{title} レコード")
                keywords.append(f"{title} LP")
                keywords.append(f"{title} アナログ")
        
        # 重複を削除
        keywords = list(set(keywords))
        
        # 長すぎるキーワードを除外（ヤフオクの検索制限に合わせる）
        keywords = [k for k in keywords if len(k) <= 100]
        
        print(f"{len(keywords)}件のキーワードを生成しました。")
        return keywords
    
    except Exception as e:
        print(f"キーワード生成エラー: {str(e)}")
        return []

def save_keywords(keywords: List[str], output_file: str = "yahoo_auction_keywords.json") -> None:
    """
    生成したキーワードをJSONファイルに保存します。
    
    Args:
        keywords: 検索キーワードのリスト
        output_file: 出力ファイル名
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(keywords, f, ensure_ascii=False, indent=2)
        print(f"キーワードを {output_file} に保存しました。")
    except Exception as e:
        print(f"キーワード保存エラー: {str(e)}")

if __name__ == "__main__":
    keywords = generate_keywords()
    save_keywords(keywords)
