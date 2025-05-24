#!/usr/bin/env python
"""
Discogsデータからメルカリ検索用のキーワードを生成するスクリプト
Discogsのデータを読み込み、メルカリでの検索に適したキーワードを生成します。
"""

import sys
import os
import argparse
import json
from typing import List, Dict, Any

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_discogs_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Discogsデータを読み込みます。
    
    Args:
        file_path: Discogsデータを含むJSONファイルのパス
        
    Returns:
        List[Dict[str, Any]]: Discogsデータのリスト
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {str(e)}")
            return []

def generate_keywords(discogs_data: List[Dict[str, Any]]) -> List[str]:
    """
    Discogsデータからメルカリ検索用のキーワードを生成します。
    
    Args:
        discogs_data: Discogsデータのリスト
        
    Returns:
        List[str]: 生成されたキーワードのリスト
    """
    keywords = []
    
    for item in discogs_data:
        # 基本情報を取得
        artist = item.get("artist", "")
        title = item.get("title", "")
        
        if not artist or not title:
            continue
        
        # 基本キーワード（アーティスト + タイトル + レコード）
        basic_keyword = f"{artist} {title} レコード"
        keywords.append(basic_keyword)
        
        # 日本語検索用のキーワード（カタカナ変換など）
        # 例: "Beatles" -> "ビートルズ"
        # 実際の実装では、より洗練された変換ロジックが必要
        japanese_artist = convert_to_japanese(artist)
        if japanese_artist != artist:
            japanese_keyword = f"{japanese_artist} {title} レコード"
            keywords.append(japanese_keyword)
    
    # 重複を削除
    return list(set(keywords))

def convert_to_japanese(text: str) -> str:
    """
    英語のアーティスト名を日本語（カタカナ）に変換します。
    実際の実装では、より洗練された変換ロジックが必要です。
    
    Args:
        text: 変換する英語テキスト
        
    Returns:
        str: 変換された日本語テキスト
    """
    # 簡易的な変換マッピング（実際の実装ではより包括的なものが必要）
    mapping = {
        "Beatles": "ビートルズ",
        "Miles Davis": "マイルス・デイビス",
        "Michael Jackson": "マイケル・ジャクソン",
        "Led Zeppelin": "レッド・ツェッペリン",
        "Pink Floyd": "ピンク・フロイド",
        "Queen": "クイーン",
        "David Bowie": "デヴィッド・ボウイ",
        "Rolling Stones": "ローリング・ストーンズ",
        "Bob Dylan": "ボブ・ディラン",
        "Jimi Hendrix": "ジミ・ヘンドリックス"
    }
    
    # 完全一致の場合
    if text in mapping:
        return mapping[text]
    
    # 部分一致の場合
    for eng, jpn in mapping.items():
        if eng.lower() in text.lower():
            return text.replace(eng, jpn)
    
    return text

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='Generate Mercari search keywords from Discogs data')
    parser.add_argument('--input', type=str, default='discogs_data.json', help='Input Discogs JSON file path')
    parser.add_argument('--output', type=str, default='mercari_keywords.json', help='Output keywords JSON file path')
    args = parser.parse_args()
    
    # Discogsデータを読み込む
    discogs_data = load_discogs_data(args.input)
    
    if not discogs_data:
        print(f"No data found in {args.input}")
        return
    
    print(f"Loaded {len(discogs_data)} records from Discogs data")
    
    # キーワードを生成
    keywords = generate_keywords(discogs_data)
    
    print(f"Generated {len(keywords)} unique search keywords")
    
    # 結果をJSONファイルに保存
    output_file = args.output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(keywords, f, indent=2, ensure_ascii=False)
    
    print(f"Keywords saved to {output_file}")
    
    # 次のステップの説明
    print("\nTo use these keywords for Mercari search:")
    print(f"python scripts/fetch_mercari.py --file {output_file} --output mercari_data.json")

if __name__ == "__main__":
    main()
