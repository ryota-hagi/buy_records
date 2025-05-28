#!/usr/bin/env python
"""
eBay検索キーワード生成スクリプト
Discogsデータからアーティスト名とタイトルを抽出し、eBay検索用のキーワードリストを生成します。
"""

import sys
import os
import argparse
import json
from typing import List, Dict, Any

def extract_keywords_from_discogs(discogs_file: str) -> List[str]:
    """
    Discogsデータからアーティスト名とタイトルを抽出し、検索キーワードを生成します。
    
    Args:
        discogs_file: Discogsデータを含むJSONファイルのパス
        
    Returns:
        List[str]: 検索キーワードのリスト
    """
    if not os.path.exists(discogs_file):
        print(f"Error: File {discogs_file} not found")
        return []
    
    try:
        with open(discogs_file, 'r', encoding='utf-8') as f:
            discogs_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {discogs_file}")
        return []
    
    keywords = []
    for item in discogs_data:
        artist = item.get("artist", "")
        title = item.get("title", "")
        
        if artist and title:
            # 基本キーワード: アーティスト名 + タイトル + "vinyl"
            keyword = f"{artist} {title} vinyl"
            keywords.append(keyword)
            
            # フォーマット情報がある場合は追加のキーワードを生成
            formats = item.get("format", [])
            if formats:
                format_str = " ".join(formats)
                if "LP" in format_str or "Album" in format_str:
                    keyword_with_format = f"{artist} {title} vinyl LP"
                    keywords.append(keyword_with_format)
    
    # 重複を削除
    return list(set(keywords))

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='Generate eBay search keywords from Discogs data')
    parser.add_argument('--input', type=str, default='discogs_data.json', help='Input Discogs JSON file')
    parser.add_argument('--output', type=str, default='ebay_keywords.json', help='Output keywords JSON file')
    args = parser.parse_args()
    
    print(f"Generating eBay search keywords from {args.input}...")
    
    # キーワードを生成
    keywords = extract_keywords_from_discogs(args.input)
    
    if not keywords:
        print("No keywords generated. Check the input file.")
        return
    
    # 結果をJSONファイルに保存
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(keywords, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(keywords)} keywords and saved to {args.output}")
    print("\nExample keywords:")
    for i, keyword in enumerate(keywords[:5]):
        print(f"  {i+1}. {keyword}")
    
    if len(keywords) > 5:
        print(f"  ... and {len(keywords) - 5} more")
    
    print("\nTo use these keywords with the eBay data collector:")
    print(f"  python scripts/fetch_ebay.py --file {args.output} --output ebay_data.json")

if __name__ == "__main__":
    main()
