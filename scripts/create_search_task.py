#!/usr/bin/env python
"""
検索タスクを作成するスクリプト

使用方法:
    python scripts/create_search_task.py --name "タスク名" [オプション]

必須オプション:
    --name NAME            タスクの名前

検索オプション（少なくとも1つ必要）:
    --query QUERY          検索クエリ
    --artist ARTIST        アーティスト名
    --title TITLE          タイトル
    --release-id ID        Discogs リリースID

その他のオプション:
    --platforms PLATFORMS  検索プラットフォーム（カンマ区切り、デフォルト: すべて）
                           例: "discogs,ebay,mercari,yahoo_auction"
    --genre GENRE          ジャンル
    --year YEAR            年代
    --country COUNTRY      国
    --format FORMAT        フォーマット（LP, EP, シングルなど）
    --min-price PRICE      最小価格
    --max-price PRICE      最大価格
"""

import argparse
import json
import logging
import sys
import os
from typing import Dict, Any, List

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.search.task_manager import SearchTaskManager

def parse_args():
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(description='検索タスクを作成するスクリプト')
    
    # 必須オプション
    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='タスクの名前'
    )
    
    # 検索オプション（少なくとも1つ必要）
    search_group = parser.add_argument_group('検索オプション（少なくとも1つ必要）')
    
    search_group.add_argument(
        '--query',
        type=str,
        help='検索クエリ'
    )
    
    search_group.add_argument(
        '--artist',
        type=str,
        help='アーティスト名'
    )
    
    search_group.add_argument(
        '--title',
        type=str,
        help='タイトル'
    )
    
    search_group.add_argument(
        '--release-id',
        type=int,
        help='Discogs リリースID'
    )
    
    # その他のオプション
    parser.add_argument(
        '--platforms',
        type=str,
        help='検索プラットフォーム（カンマ区切り、デフォルト: すべて）'
    )
    
    parser.add_argument(
        '--genre',
        type=str,
        help='ジャンル'
    )
    
    parser.add_argument(
        '--year',
        type=str,
        help='年代'
    )
    
    parser.add_argument(
        '--country',
        type=str,
        help='国'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        help='フォーマット（LP, EP, シングルなど）'
    )
    
    parser.add_argument(
        '--min-price',
        type=float,
        help='最小価格'
    )
    
    parser.add_argument(
        '--max-price',
        type=float,
        help='最大価格'
    )
    
    args = parser.parse_args()
    
    # 検索オプションが少なくとも1つ指定されているか確認
    if not (args.query or args.artist or args.title or args.release_id):
        parser.error('検索オプション（--query, --artist, --title, --release-id）のうち少なくとも1つを指定してください')
    
    return args

def build_search_params(args) -> Dict[str, Any]:
    """
    コマンドライン引数から検索パラメータを構築する
    
    Args:
        args: コマンドライン引数
        
    Returns:
        Dict[str, Any]: 検索パラメータ
    """
    search_params = {}
    
    # 検索オプション
    if args.query:
        search_params['query'] = args.query
    
    if args.artist:
        search_params['artist'] = args.artist
    
    if args.title:
        search_params['title'] = args.title
    
    if args.release_id:
        search_params['release_id'] = args.release_id
    
    # プラットフォーム
    if args.platforms:
        platforms = [p.strip() for p in args.platforms.split(',')]
        search_params['platforms'] = platforms
    
    # その他のオプション
    if args.genre:
        search_params['genre'] = args.genre
    
    if args.year:
        search_params['year'] = args.year
    
    if args.country:
        search_params['country'] = args.country
    
    if args.format:
        search_params['format'] = args.format
    
    if args.min_price:
        search_params['min_price'] = args.min_price
    
    if args.max_price:
        search_params['max_price'] = args.max_price
    
    return search_params

def main():
    """メイン関数"""
    args = parse_args()
    
    # 検索パラメータを構築
    search_params = build_search_params(args)
    
    logger.info(f"Creating search task '{args.name}' with params: {json.dumps(search_params, indent=2)}")
    
    # タスクマネージャーを初期化
    task_manager = SearchTaskManager()
    
    # タスクを作成
    task_id = task_manager.create_task(args.name, search_params)
    
    logger.info(f"Created search task with ID: {task_id}")
    
    # タスク情報を表示
    task = task_manager.get_task(task_id)
    if task:
        logger.info(f"Task details: {json.dumps(task, indent=2, default=str)}")

if __name__ == '__main__':
    main()
